#!/usr/bin/env python3
"""
CVE Data Models - Pydantic V2 Compliant
Enterprise-grade type safety and validation for CVE data structures

Author: Built to enterprise-grade standards
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict
from enum import Enum


class SeverityLevel(str, Enum):
    """CVSS Severity Categories - NIST Standard"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class CVSSMetrics(BaseModel):
    """CVSS Scoring Metrics"""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)
    
    version: str = Field(..., pattern=r"^[23]\.\d$", description="CVSS version (2.0, 3.0, 3.1)")
    base_score: float = Field(..., ge=0.0, le=10.0, description="Base CVSS score")
    vector_string: Optional[str] = Field(None, description="CVSS vector string")
    exploitability_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    impact_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    
    @computed_field
    @property
    def severity(self) -> SeverityLevel:
        """Compute severity level from base score"""
        if self.base_score >= 9.0:
            return SeverityLevel.CRITICAL
        elif self.base_score >= 7.0:
            return SeverityLevel.HIGH
        elif self.base_score >= 4.0:
            return SeverityLevel.MEDIUM
        elif self.base_score > 0.0:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.NONE


class CVEReference(BaseModel):
    """External reference for CVE"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    url: str = Field(..., description="Reference URL")
    source: Optional[str] = Field(None, description="Reference source")
    tags: List[str] = Field(default_factory=list, description="Reference tags")


class CVEVendor(BaseModel):
    """Vendor information"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    name: str = Field(..., min_length=1, description="Vendor name")
    
    @field_validator('name')
    @classmethod
    def normalize_vendor_name(cls, v: str) -> str:
        """Normalize vendor name for consistency"""
        return v.strip().lower()


class CVEProduct(BaseModel):
    """Product information - handles NVD data format"""
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)
    
    # NVD uses 'product' field, but we want 'name' internally
    name: str = Field(..., min_length=1, description="Product name", alias='product')
    version: Optional[str] = Field(None, description="Affected version")
    vendor: Optional[str] = Field(None, description="Product vendor")
    cpe: Optional[str] = Field(None, description="CPE identifier")
    
    @field_validator('name', 'vendor')
    @classmethod
    def normalize_strings(cls, v: Optional[str]) -> Optional[str]:
        """Normalize strings"""
        return v.strip().lower() if v else None
    
    @classmethod
    def from_dict_or_string(cls, value):
        """Create from dict (NVD format) or string (simplified)"""
        if isinstance(value, str):
            return cls(product=value)
        elif isinstance(value, dict):
            return cls(**value)
        else:
            return value


class CVE(BaseModel):
    """
    Complete CVE Data Model
    Validates all CVE data with strict type checking
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        validate_default=True,
        extra='allow'  # Allow extra fields from NVD
    )
    
    # Core Identity
    cve_id: str = Field(
        ..., 
        pattern=r"^CVE-\d{4}-\d{4,}$",
        description="CVE ID in format CVE-YYYY-NNNN+"
    )
    
    # Descriptions (optional since some old CVEs lack detailed descriptions)
    description: str = Field(default="No description available", description="CVE description")
    
    # CVSS Scores
    cvss_v3_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="CVSS v3 base score")
    cvss_v2_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="CVSS v2 base score")
    cvss_v3_metrics: Optional[CVSSMetrics] = Field(None, description="Full CVSS v3 metrics")
    cvss_v2_metrics: Optional[CVSSMetrics] = Field(None, description="Full CVSS v2 metrics")
    
    # Temporal Data
    published: Optional[datetime] = Field(None, description="Publication date")
    modified: Optional[datetime] = Field(None, description="Last modification date")
    
    # Affected Systems
    affected_vendors: List[Union[str, CVEVendor]] = Field(
        default_factory=list, 
        description="List of affected vendors"
    )
    affected_products: List[Union[str, CVEProduct]] = Field(
        default_factory=list,
        description="List of affected products"
    )
    
    # Weaknesses
    cwes: List[str] = Field(
        default_factory=list,
        description="CWE identifiers"
    )
    
    # References
    references: List[Union[str, CVEReference]] = Field(
        default_factory=list,
        description="External references"
    )
    
    # Additional Metadata
    assigner: Optional[str] = Field(None, description="CVE assigner")
    source: str = Field(default="NVD", description="Data source")
    
    @field_validator('cve_id')
    @classmethod
    def validate_cve_id(cls, v: str) -> str:
        """Ensure CVE ID is uppercase and formatted correctly"""
        return v.upper().strip()
    
    @field_validator('affected_products', mode='before')
    @classmethod
    def validate_products(cls, v: Any) -> List:
        """Handle mixed product formats from NVD"""
        if not v:
            return []
        
        validated = []
        for item in v:
            if isinstance(item, str):
                validated.append(item)
            elif isinstance(item, dict):
                # NVD format: has 'product' key
                if 'product' in item:
                    validated.append(item)
                # Already has 'name' key
                elif 'name' in item:
                    validated.append(item)
            elif isinstance(item, CVEProduct):
                validated.append(item)
        
        return validated
    
    @field_validator('cwes')
    @classmethod
    def validate_cwes(cls, v: List[str]) -> List[str]:
        """Validate CWE format"""
        validated = []
        for cwe in v:
            if cwe and (cwe.startswith('CWE-') or cwe.startswith('NVD-CWE-')):
                validated.append(cwe.upper())
        return validated
    
    @field_validator('published', 'modified', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> Optional[datetime]:
        """Parse datetime from various formats"""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                # Handle ISO format with Z
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return None
        return None
    
    @computed_field
    @property
    def severity(self) -> SeverityLevel:
        """Compute overall severity from available CVSS scores"""
        score = self.cvss_v3_score or self.cvss_v2_score or 0.0
        
        if score >= 9.0:
            return SeverityLevel.CRITICAL
        elif score >= 7.0:
            return SeverityLevel.HIGH
        elif score >= 4.0:
            return SeverityLevel.MEDIUM
        elif score > 0.0:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.NONE
    
    @computed_field
    @property
    def primary_cvss_score(self) -> float:
        """Get the primary CVSS score (prefer v3 over v2)"""
        return self.cvss_v3_score or self.cvss_v2_score or 0.0
    
    @computed_field
    @property
    def vendor_names(self) -> List[str]:
        """Extract vendor names as strings"""
        vendors = []
        for vendor in self.affected_vendors:
            if isinstance(vendor, str):
                vendors.append(vendor.lower())
            elif isinstance(vendor, CVEVendor):
                vendors.append(vendor.name)
            elif isinstance(vendor, dict):
                vendors.append(vendor.get('name', '').lower())
        return [v for v in vendors if v]
    
    @computed_field
    @property
    def product_names(self) -> List[str]:
        """Extract product names as strings"""
        products = []
        for product in self.affected_products:
            if isinstance(product, str):
                products.append(product.lower())
            elif isinstance(product, CVEProduct):
                products.append(product.name)
            elif isinstance(product, dict):
                # NVD format uses 'product' key
                prod_name = product.get('product') or product.get('name', '')
                if prod_name:
                    products.append(prod_name.lower())
        return [p for p in products if p]
    
    @computed_field
    @property
    def reference_urls(self) -> List[str]:
        """Extract reference URLs as strings"""
        urls = []
        for ref in self.references:
            if isinstance(ref, str):
                urls.append(ref)
            elif isinstance(ref, CVEReference):
                urls.append(ref.url)
            elif isinstance(ref, dict):
                urls.append(ref.get('url', ''))
        return [u for u in urls if u]
    
    def to_redis_hash(self) -> Dict[str, Any]:
        """
        Convert to Redis hash format
        Optimized for storage and retrieval
        """
        return {
            'id': self.cve_id,
            'description': self.description,
            'cvss_v3': self.cvss_v3_score or 0,
            'cvss_v2': self.cvss_v2_score or 0,
            'severity': self.severity.value,
            'published': self.published.isoformat() if self.published else '',
            'modified': self.modified.isoformat() if self.modified else '',
            'vendors': ','.join(self.vendor_names),
            'products': ','.join(self.product_names),
            'cwes': ','.join(self.cwes),
            'references': ','.join(self.reference_urls[:10]),  # Limit to 10
            'source': self.source
        }
    
    def to_neo4j_node(self) -> Dict[str, Any]:
        """
        Convert to Neo4j node properties
        Matches recommended Neo4j schema
        """
        return {
            'id': self.cve_id,
            'description': self.description,
            'cvss_v3': self.cvss_v3_score,  # Match schema: cvss_v3 not cvss_v3_score
            'cvss_v2': self.cvss_v2_score,
            'severity': self.severity.value,
            'published': self.published.isoformat() if self.published else None,
            'modified': self.modified.isoformat() if self.modified else None,
            'year': self.published.year if self.published else None,
            'embedding_available': True,  # All CVEs have embeddings in Redis
            'assigner': self.assigner,
            'source': self.source
        }


class CVEEmbedding(BaseModel):
    """
    CVE with semantic embeddings for vector search
    GPU-accelerated generation ready
    """
    model_config = ConfigDict(validate_assignment=True)
    
    cve_id: str = Field(..., pattern=r"^CVE-\d{4}-\d{4,}$")
    description: str = Field(default="No description available", description="CVE description")
    embedding: List[float] = Field(..., description="Semantic embedding vector")
    embedding_model: str = Field(..., description="Model used for embedding")
    embedding_dim: int = Field(..., gt=0, description="Embedding dimension")
    
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    severity: Optional[SeverityLevel] = None
    vendors: List[str] = Field(default_factory=list)
    cwes: List[str] = Field(default_factory=list)
    
    @field_validator('embedding')
    @classmethod
    def validate_embedding_length(cls, v: List[float], info) -> List[float]:
        """Ensure embedding length matches declared dimension"""
        if 'embedding_dim' in info.data and len(v) != info.data['embedding_dim']:
            raise ValueError(f"Embedding length {len(v)} doesn't match dimension {info.data['embedding_dim']}")
        return v
    
    def to_weaviate_object(self) -> Dict[str, Any]:
        """Convert to Weaviate object format"""
        return {
            'cve_id': self.cve_id,
            'description': self.description,
            'cvss_score': self.cvss_score or 0.0,
            'severity': self.severity.value if self.severity else 'none',
            'vendors': self.vendors,
            'cwes': self.cwes,
            'embedding_model': self.embedding_model
        }


class CVEBatch(BaseModel):
    """
    Batch of CVEs for processing
    Optimized for GPU batch operations
    """
    model_config = ConfigDict(validate_assignment=True)
    
    cves: List[CVE] = Field(..., min_length=1, description="CVEs in batch")
    batch_id: str = Field(..., description="Unique batch identifier")
    batch_size: int = Field(..., gt=0, description="Number of CVEs")
    source: str = Field(default="NVD", description="Data source")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('batch_size')
    @classmethod
    def validate_batch_size(cls, v: int, info) -> int:
        """Ensure batch_size matches actual CVE count"""
        if 'cves' in info.data and len(info.data['cves']) != v:
            raise ValueError(f"Batch size {v} doesn't match CVE count {len(info.data['cves'])}")
        return v
    
    @computed_field
    @property
    def severity_distribution(self) -> Dict[str, int]:
        """Get severity distribution for batch"""
        distribution = {level.value: 0 for level in SeverityLevel}
        for cve in self.cves:
            distribution[cve.severity.value] += 1
        return distribution


class RedisHighwayStats(BaseModel):
    """Statistics for Redis Highway construction"""
    model_config = ConfigDict(validate_assignment=True)
    
    cves_processed: int = Field(default=0, ge=0)
    indexes_created: int = Field(default=0, ge=0)
    sets_created: int = Field(default=0, ge=0)
    sorted_sets_created: int = Field(default=0, ge=0)
    keywords_extracted: int = Field(default=0, ge=0)
    embeddings_generated: int = Field(default=0, ge=0)
    errors: int = Field(default=0, ge=0)
    
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    
    @computed_field
    @property
    def duration_seconds(self) -> float:
        """Calculate processing duration"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    @computed_field
    @property
    def processing_rate(self) -> float:
        """Calculate CVEs per second"""
        duration = self.duration_seconds
        return self.cves_processed / duration if duration > 0 else 0.0
    
    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.cves_processed + self.errors
        return (self.cves_processed / total * 100) if total > 0 else 0.0


# Type aliases for clarity
CVEList = List[CVE]
CVEDict = Dict[str, CVE]
EmbeddingVector = List[float]
