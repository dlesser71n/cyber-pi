#!/usr/bin/env python3
"""
Enterprise Standard Data Validator
Production-grade data validation and quality assurance
"""

import re
import ipaddress
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ValidationResult:
    """Result of a validation operation"""
    valid: bool
    errors: List[str]
    warnings: List[str]

class DataValidator:
    """Enterprise-grade data validation"""
    
    # CVE ID pattern (e.g., CVE-2024-1234)
    CVE_PATTERN = re.compile(r'^CVE-\d{4}-\d{4,7}$')
    
    # CWE ID pattern (e.g., CWE-79)
    CWE_PATTERN = re.compile(r'^CWE-\d+$')
    
    # SHA-256 pattern
    SHA256_PATTERN = re.compile(r'^[a-fA-F0-9]{64}$')
    
    # SHA-1 pattern
    SHA1_PATTERN = re.compile(r'^[a-fA-F0-9]{40}$')
    
    # MD5 pattern
    MD5_PATTERN = re.compile(r'^[a-fA-F0-9]{32}$')
    
    # Domain pattern
    DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z]{2,})+$')
    
    # Email pattern
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def normalize_date_string(self, date_str: str) -> str:
        """Normalize various date formats to ISO8601 UTC"""
        if not date_str:
            return None
            
        # Common date formats to try
        date_formats = [
            '%Y-%m-%dT%H:%M:%SZ',      # Standard ISO8601
            '%Y-%m-%dT%H:%M:%S.%fZ',   # ISO8601 with microseconds
            '%Y-%m-%dT%H:%M:%S',       # ISO8601 without Z
            '%Y-%m-%d %H:%M:%S',       # Space separated
            '%Y-%m-%d',                # Date only
            '%Y-%m-%dT%H:%M:%S%z',     # ISO8601 with timezone
            '%Y-%m-%dT%H:%M:%S.%f%z',  # ISO8601 with microseconds and timezone
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Convert to UTC and standard format
                if dt.tzinfo is not None:
                    dt = dt.astimezone(datetime.timezone.utc)
                return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                continue
                
        # If all formats fail, try to extract date part
        try:
            # Extract just the date part if it looks like ISO format
            if 'T' in date_str:
                date_part = date_str.split('T')[0]
                dt = datetime.strptime(date_part, '%Y-%m-%d')
                return dt.strftime('%Y-%m-%dT00:00:00Z')
        except ValueError:
            pass
            
        return None

    def validate_dates(self, data: Dict[str, Any], date_fields: List[str]) -> List[str]:
        """Validate multiple date fields with flexible parsing"""
        errors = []
        
        for field in date_fields:
            if field in data:
                normalized = self.normalize_date_string(data[field])
                if normalized is None:
                    errors.append(f"Invalid {field} date format: {data[field]}")
                else:
                    # Replace with normalized format
                    data[field] = normalized
                    
        return errors
    
    def validate_cve(self, cve: Dict[str, Any]) -> ValidationResult:
        """Validate CVE data"""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = {
            'cve_id': str,
            'description': str,
            'published': str
        }
        
        # Optional fields with types
        optional_fields = {
            'cvss_v3_score': (float, int),
            'cvss_v2_score': (float, int),
            'severity': str,
            'affected_vendors': list,
            'affected_products': list,
            'cwes': list
        }
        
        # Check required fields
        for field, field_type in required_fields.items():
            if field not in cve:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(cve[field], field_type):
                errors.append(f"Invalid type for {field}: expected {field_type}, got {type(cve[field])}")
        
        # Check optional fields
        for field, field_types in optional_fields.items():
            if field in cve and not isinstance(cve[field], field_types):
                warnings.append(f"Invalid type for {field}: expected {field_types}, got {type(cve[field])}")
        
        # Validate CVE ID format
        if 'cve_id' in cve and not self.CVE_PATTERN.match(cve['cve_id']):
            errors.append(f"Invalid CVE ID format: {cve['cve_id']}")
        
        # Validate CVSS scores
        if 'cvss_v3_score' in cve and not (0 <= cve['cvss_v3_score'] <= 10):
            errors.append(f"Invalid CVSS v3 score: {cve['cvss_v3_score']}")
        
        if 'cvss_v2_score' in cve and not (0 <= cve['cvss_v2_score'] <= 10):
            errors.append(f"Invalid CVSS v2 score: {cve['cvss_v2_score']}")
        
        # Validate severity (case-insensitive)
        valid_severities = {'critical', 'high', 'medium', 'low', 'none'}
        if 'severity' in cve and cve['severity'].lower() not in valid_severities:
            errors.append(f"Invalid severity: {cve['severity']}")
        elif 'severity' in cve:
            # Normalize severity to lowercase
            cve['severity'] = cve['severity'].lower()
        
        # Validate CWEs
        if 'cwes' in cve:
            for cwe in cve['cwes']:
                if not self.CWE_PATTERN.match(cwe):
                    errors.append(f"Invalid CWE format: {cwe}")
        
        # Validate dates using flexible parsing
        date_errors = self.validate_dates(cve, ['published', 'modified', 'lastModified'])
        errors.extend(date_errors)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_threat_intel(self, threat: Dict[str, Any]) -> ValidationResult:
        """Validate threat intelligence data"""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = {
            'id': str,
            'title': str,
            'description': str,
            'severity': str,
            'type': str,
            'source': str
        }
        
        # Optional fields with types
        optional_fields = {
            'cves': list,
            'mitreTactics': list,
            'mitreTechniques': list,
            'affectedProducts': list,
            'affectedVendors': list,
            'cwes': list,
            'confidence': (float, int)
        }
        
        # Check required fields
        for field, field_type in required_fields.items():
            if field not in threat:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(threat[field], field_type):
                errors.append(f"Invalid type for {field}: expected {field_type}, got {type(threat[field])}")
        
        # Check optional fields
        for field, field_types in optional_fields.items():
            if field in threat and not isinstance(threat[field], field_types):
                warnings.append(f"Invalid type for {field}: expected {field_types}, got {type(threat[field])}")
        
        # Validate severity
        valid_severities = {'critical', 'high', 'medium', 'low'}
        if 'severity' in threat and threat['severity'] not in valid_severities:
            errors.append(f"Invalid severity: {threat['severity']}")
        
        # Validate confidence
        if 'confidence' in threat:
            if not (0 <= threat['confidence'] <= 1):
                errors.append(f"Invalid confidence score: {threat['confidence']}")
        
        # Validate CVEs
        if 'cves' in threat:
            for cve in threat['cves']:
                if not self.CVE_PATTERN.match(cve):
                    errors.append(f"Invalid CVE format: {cve}")
        
        # Validate CWEs
        if 'cwes' in threat:
            for cwe in threat['cwes']:
                if not self.CWE_PATTERN.match(cwe):
                    errors.append(f"Invalid CWE format: {cwe}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_ioc(self, ioc: Dict[str, Any]) -> ValidationResult:
        """Validate IOC data"""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = {
            'value': str,
            'type': str,
            'confidence': (float, int),
            'firstSeen': str
        }
        
        # Check required fields
        for field, field_type in required_fields.items():
            if field not in ioc:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(ioc[field], field_type):
                errors.append(f"Invalid type for {field}: expected {field_type}, got {type(ioc[field])}")
        
        # Validate IOC type and value
        if 'type' in ioc and 'value' in ioc:
            ioc_type = ioc['type']
            value = ioc['value']
            
            if ioc_type.startswith('ip.'):
                try:
                    ipaddress.ip_address(value)
                except ValueError:
                    errors.append(f"Invalid IP address: {value}")
            
            elif ioc_type.startswith('domain.'):
                if not self.DOMAIN_PATTERN.match(value):
                    errors.append(f"Invalid domain: {value}")
            
            elif ioc_type.startswith('file.'):
                if ioc_type == 'file.md5' and not self.MD5_PATTERN.match(value):
                    errors.append(f"Invalid MD5 hash: {value}")
                elif ioc_type == 'file.sha1' and not self.SHA1_PATTERN.match(value):
                    errors.append(f"Invalid SHA-1 hash: {value}")
                elif ioc_type == 'file.sha256' and not self.SHA256_PATTERN.match(value):
                    errors.append(f"Invalid SHA-256 hash: {value}")
            
            elif ioc_type.startswith('email.'):
                if ioc_type == 'email.address' and not self.EMAIL_PATTERN.match(value):
                    errors.append(f"Invalid email address: {value}")
        
        # Validate confidence
        if 'confidence' in ioc and not (0 <= ioc['confidence'] <= 1):
            errors.append(f"Invalid confidence score: {ioc['confidence']}")
        
        # Validate date using flexible parsing
        date_errors = self.validate_dates(ioc, ['firstSeen', 'lastSeen'])
        errors.extend(date_errors)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def validate_relationship(self, source_type: str, target_type: str, relationship_type: str) -> ValidationResult:
        """Validate relationship types"""
        errors = []
        warnings = []
        
        # Valid relationship types between entities
        valid_relationships = {
            ('CVE', 'Product'): {'AFFECTS'},
            ('Product', 'Vendor'): {'MADE_BY'},
            ('CVE', 'CWE'): {'HAS_WEAKNESS'},
            ('ThreatIntel', 'CVE'): {'REFERENCES'},
            ('ThreatIntel', 'MitreTactic'): {'USES_TACTIC'},
            ('ThreatIntel', 'MitreTechnique'): {'USES_TECHNIQUE'},
            ('CWE', 'MitreTechnique'): {'ENABLES_TECHNIQUE'},
            ('IOC', 'ThreatIntel'): {'INDICATES'},
            ('MitreTactic', 'MitreTechnique'): {'USES'}
        }
        
        # Check if relationship is valid
        if (source_type, target_type) not in valid_relationships:
            errors.append(f"Invalid relationship between {source_type} and {target_type}")
        elif relationship_type not in valid_relationships[(source_type, target_type)]:
            errors.append(f"Invalid relationship type {relationship_type} between {source_type} and {target_type}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
