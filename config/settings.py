"""
cyber-pi Configuration Management
Enterprise Threat Intelligence Platform Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional
import os


class Settings(BaseSettings):
    """
    Comprehensive configuration for cyber-pi platform
    Leverages existing TQAKB infrastructure and massive hardware resources
    """
    
    # ========================================================================
    # APPLICATION SETTINGS
    # ========================================================================
    app_name: str = "cyber-pi"
    app_version: str = "1.0.0-alpha"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    
    # ========================================================================
    # HARDWARE RESOURCES (HPE DL380 "The Beast")
    # ========================================================================
    # CPU Configuration
    cpu_cores: int = 32
    max_workers: int = 128  # Aggressive parallelization
    
    # GPU Configuration
    gpu_devices: List[int] = [0, 1]  # Dual NVIDIA A6000
    gpu_memory_per_device: int = 48  # GB per GPU
    total_gpu_memory: int = 96  # GB total VRAM
    gpu_batch_size: int = 10000  # Documents per GPU batch
    
    # Memory Configuration
    total_ram: int = 768  # GB
    processing_memory_limit: int = 400  # GB for active processing
    
    # Storage Configuration
    total_storage: int = 30  # TB
    daily_growth_estimate: int = 1  # TB per day
    
    # ========================================================================
    # TRI-MODAL DATABASE CONFIGURATION
    # ========================================================================
    # Redis (Real-time streaming and caching)
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_max_connections: int = 1000
    
    # Neo4j (Threat relationship graphs)
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="dev-neo4j-password", env="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", env="NEO4J_DATABASE")
    
    # Weaviate (Vector search and embeddings)
    weaviate_url: str = Field(default="http://localhost:30883", env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    
    # PostgreSQL (Optional structured storage)
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(default="cyberpi", env="POSTGRES_USER")
    postgres_password: str = Field(default="cyberpi", env="POSTGRES_PASSWORD")
    postgres_database: str = Field(default="cyberpi", env="POSTGRES_DATABASE")
    
    # ========================================================================
    # DATA COLLECTION CONFIGURATION
    # ========================================================================
    # RSS Collection
    rss_worker_count: int = 32
    rss_collection_interval: int = 300  # seconds (5 minutes)
    rss_timeout: int = 30  # seconds
    
    # Government API Collection
    gov_api_worker_count: int = 16
    gov_api_rate_limit: int = 100  # requests per minute
    
    # Social Media Collection
    social_worker_count: int = 16
    twitter_bearer_token: Optional[str] = Field(default=None, env="TWITTER_BEARER_TOKEN")
    reddit_client_id: Optional[str] = Field(default=None, env="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(default=None, env="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = Field(default="cyber-pi/1.0", env="REDDIT_USER_AGENT")
    
    # Vendor Intelligence
    vendor_worker_count: int = 20
    vendor_collection_interval: int = 600  # seconds (10 minutes)
    
    # Underground Intelligence
    underground_worker_count: int = 8
    use_tor_proxy: bool = False
    tor_proxy_url: Optional[str] = Field(default=None, env="TOR_PROXY_URL")
    
    # Industrial/OT Specialized
    industrial_worker_count: int = 12
    industrial_priority: bool = True  # High priority for critical infrastructure
    
    # ========================================================================
    # PROCESSING CONFIGURATION
    # ========================================================================
    # GPU Processing
    enable_gpu_processing: bool = True
    gpu_model_name: str = "sentence-transformers/all-mpnet-base-v2"
    embedding_dimension: int = 768
    
    # NLP Configuration
    spacy_model: str = "en_core_web_lg"
    max_text_length: int = 100000  # characters
    
    # Threat Classification
    classification_confidence_threshold: float = 0.7
    enable_multi_label: bool = True
    
    # Attribution Engine
    attribution_min_confidence: float = 0.6
    enable_nation_state_tracking: bool = True
    
    # ========================================================================
    # INTELLIGENCE SOURCES
    # ========================================================================
    # Source Categories
    enable_government_sources: bool = True
    enable_vendor_sources: bool = True
    enable_social_sources: bool = True
    enable_underground_sources: bool = True
    enable_industrial_sources: bool = True
    
    # Source Quality Thresholds
    min_source_credibility: float = 0.5
    require_corroboration: bool = True
    corroboration_count: int = 2
    
    # ========================================================================
    # NEWSLETTER & REPORTING
    # ========================================================================
    # Generation Schedule
    daily_brief_enabled: bool = True
    daily_brief_time: str = "06:00"  # UTC
    
    weekly_report_enabled: bool = True
    weekly_report_day: str = "Monday"
    weekly_report_time: str = "08:00"  # UTC
    
    # Report Tiers
    enable_enterprise_tier: bool = True
    enable_midmarket_tier: bool = True
    enable_industrial_tier: bool = True
    
    # Delivery Methods
    email_enabled: bool = False
    api_delivery_enabled: bool = True
    pdf_generation_enabled: bool = True
    
    # ========================================================================
    # SECURITY & AUTHENTICATION
    # ========================================================================
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API Security
    enable_api_key_auth: bool = False
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 100
    
    # ========================================================================
    # MONITORING & LOGGING
    # ========================================================================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "json"
    enable_prometheus: bool = True
    prometheus_port: int = 9090
    
    # Performance Monitoring
    track_processing_time: bool = True
    track_gpu_utilization: bool = True
    track_memory_usage: bool = True
    
    # ========================================================================
    # STORAGE PATHS
    # ========================================================================
    data_dir: str = "/home/david/projects/cyber-pi/data"
    raw_data_dir: str = "/home/david/projects/cyber-pi/data/raw"
    processed_data_dir: str = "/home/david/projects/cyber-pi/data/processed"
    reports_dir: str = "/home/david/projects/cyber-pi/data/reports"
    
    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================
    enable_experimental_features: bool = False
    enable_ml_predictions: bool = True
    enable_automated_attribution: bool = True
    enable_real_time_alerting: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from .env without validation errors


# Global settings instance
settings = Settings()


# Convenience functions
def get_redis_url() -> str:
    """Get Redis connection URL"""
    if settings.redis_password:
        return f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
    return f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def get_neo4j_uri() -> str:
    """Get Neo4j connection URI"""
    return settings.neo4j_uri


def get_weaviate_url() -> str:
    """Get Weaviate connection URL"""
    return settings.weaviate_url


def get_postgres_url() -> str:
    """Get PostgreSQL connection URL"""
    return f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"


# Export settings
__all__ = ["settings", "Settings", "get_redis_url", "get_neo4j_uri", "get_weaviate_url", "get_postgres_url"]
