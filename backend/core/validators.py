"""
Input Validation and Sanitization for Cyber-PI-Intel
Prevents injection attacks, XSS, and malformed requests
"""

from typing import Any, Optional, List
from fastapi import HTTPException, status
import re
from pydantic import BaseModel, Field, validator


class InputValidator:
    """Centralized input validation and sanitization"""

    # Regex patterns for validation
    PATTERNS = {
        'cve_id': re.compile(r'^CVE-\d{4}-\d{4,7}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9_-]+$'),
        'domain': re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'),
        'ip_address': re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'),
        'hash_md5': re.compile(r'^[a-f0-9]{32}$'),
        'hash_sha1': re.compile(r'^[a-f0-9]{40}$'),
        'hash_sha256': re.compile(r'^[a-f0-9]{64}$'),
        'mitre_technique': re.compile(r'^T\d{4}(\.\d{3})?$'),
        'safe_string': re.compile(r'^[a-zA-Z0-9\s\-_.,:;!?()\[\]{}\'\"]+$')
    }

    # Maximum lengths for various fields
    MAX_LENGTHS = {
        'query': 500,
        'title': 200,
        'description': 5000,
        'actor_name': 100,
        'industry': 50,
        'source': 100
    }

    @classmethod
    def validate_cve_id(cls, cve_id: str) -> str:
        """Validate CVE identifier format"""
        if not cls.PATTERNS['cve_id'].match(cve_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CVE ID format: {cve_id}. Expected: CVE-YYYY-NNNN"
            )
        return cve_id

    @classmethod
    def validate_mitre_technique(cls, technique_id: str) -> str:
        """Validate MITRE ATT&CK technique ID"""
        if not cls.PATTERNS['mitre_technique'].match(technique_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid MITRE technique ID: {technique_id}. Expected: T1234 or T1234.001"
            )
        return technique_id

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000, field_name: str = "input") -> str:
        """
        Sanitize string input to prevent injection attacks

        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length
            field_name: Name of field for error messages

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be a string"
            )

        # Remove null bytes
        value = value.replace('\x00', '')

        # Check length
        if len(value) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} exceeds maximum length of {max_length} characters"
            )

        # Remove control characters except newline and tab
        value = ''.join(char for char in value if char in '\n\t' or ord(char) >= 32)

        # Strip leading/trailing whitespace
        value = value.strip()

        return value

    @classmethod
    def validate_integer_range(cls, value: int, min_val: int = 1, max_val: int = 1000,
                               field_name: str = "value") -> int:
        """Validate integer is within acceptable range"""
        if not isinstance(value, int):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be an integer"
            )

        if value < min_val or value > max_val:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be between {min_val} and {max_val}"
            )

        return value

    @classmethod
    def validate_list_length(cls, values: List[Any], max_items: int = 100,
                            field_name: str = "list") -> List[Any]:
        """Validate list doesn't exceed maximum items"""
        if not isinstance(values, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be a list"
            )

        if len(values) > max_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} exceeds maximum of {max_items} items"
            )

        return values

    @classmethod
    def validate_severity(cls, severity: str) -> str:
        """Validate threat severity level"""
        valid_severities = ['critical', 'high', 'medium', 'low', 'info']
        severity_lower = severity.lower()

        if severity_lower not in valid_severities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}. Must be one of: {', '.join(valid_severities)}"
            )

        return severity_lower

    @classmethod
    def sanitize_neo4j_parameter(cls, param: str, max_length: int = 200) -> str:
        """
        Sanitize parameters for Neo4j Cypher queries
        Even though we use parameterized queries, this adds defense-in-depth
        """
        # Sanitize basic string
        param = cls.sanitize_string(param, max_length, "Neo4j parameter")

        # Check for suspicious patterns
        suspicious_patterns = [
            'MATCH', 'CREATE', 'DELETE', 'DETACH', 'REMOVE', 'SET',
            'MERGE', 'DROP', 'CALL', 'RETURN', 'WHERE', 'UNION'
        ]

        param_upper = param.upper()
        for pattern in suspicious_patterns:
            if pattern in param_upper:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid characters detected in parameter"
                )

        return param

    @classmethod
    def validate_search_query(cls, query: str) -> str:
        """Validate and sanitize search query"""
        query = cls.sanitize_string(query, cls.MAX_LENGTHS['query'], "search query")

        # Prevent ReDoS attacks - check for excessive regex special characters
        special_chars = sum(1 for c in query if c in r'.*+?[]{}()\|^$')
        if special_chars > len(query) * 0.3:  # More than 30% special chars
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query contains too many special characters"
            )

        return query


class ValidatedThreatQuery(BaseModel):
    """Validated threat query model"""
    query: str = Field(..., min_length=1, max_length=500)
    industry: Optional[str] = Field(None, max_length=50)
    severity: Optional[List[str]] = Field(None, max_items=5)
    limit: int = Field(10, ge=1, le=100)

    @validator('query')
    def validate_query(cls, v):
        return InputValidator.validate_search_query(v)

    @validator('industry')
    def validate_industry(cls, v):
        if v:
            return InputValidator.sanitize_string(v, 50, "industry")
        return v

    @validator('severity')
    def validate_severity_list(cls, v):
        if v:
            return [InputValidator.validate_severity(s) for s in v]
        return v


class ValidatedCollectionRequest(BaseModel):
    """Validated collection request model"""
    sources: List[str] = Field(default=["technical", "social", "ot_ics", "dark_web"], max_items=10)
    industry: Optional[str] = Field(None, max_length=50)

    @validator('sources')
    def validate_sources(cls, v):
        valid_sources = ['technical', 'social', 'ot_ics', 'dark_web', 'geopolitical', 'newsletters']
        for source in v:
            if source not in valid_sources:
                raise ValueError(f"Invalid source: {source}. Must be one of: {', '.join(valid_sources)}")
        return v

    @validator('industry')
    def validate_industry(cls, v):
        if v:
            return InputValidator.sanitize_string(v, 50, "industry")
        return v


class ValidatedActorName(BaseModel):
    """Validated threat actor name"""
    actor_name: str = Field(..., min_length=1, max_length=100)

    @validator('actor_name')
    def validate_actor(cls, v):
        return InputValidator.sanitize_neo4j_parameter(v, 100)


class ValidatedLimit(BaseModel):
    """Validated limit parameter"""
    limit: int = Field(default=20, ge=1, le=1000)

    @validator('limit')
    def validate_limit(cls, v):
        return InputValidator.validate_integer_range(v, 1, 1000, "limit")


# Query parameter validators
def validate_limit_param(limit: int = 50) -> int:
    """Validate limit query parameter"""
    return InputValidator.validate_integer_range(limit, 1, 1000, "limit")


def validate_offset_param(offset: int = 0) -> int:
    """Validate offset query parameter"""
    return InputValidator.validate_integer_range(offset, 0, 100000, "offset")


def validate_severity_param(severity: Optional[str] = None) -> Optional[str]:
    """Validate severity query parameter"""
    if severity:
        return InputValidator.validate_severity(severity)
    return severity


def validate_industry_param(industry: Optional[str] = None) -> Optional[str]:
    """Validate industry query parameter"""
    if industry:
        return InputValidator.sanitize_string(industry, 50, "industry")
    return industry
