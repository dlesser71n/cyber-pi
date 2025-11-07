"""
TQAKB V4 Configuration Management
Environment-based configuration with Pydantic validation
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr, field_validator

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(True, env="DEBUG")
    log_level: str = Field("DEBUG", env="LOG_LEVEL")
    
    # API Configuration
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_workers: int = Field(4, env="API_WORKERS")
    api_reload: bool = Field(True, env="API_RELOAD")
    cors_origins: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000", "http://tqakb.local"],
        env="CORS_ORIGINS"
    )
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = Field("localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    kafka_security_protocol: str = Field("PLAINTEXT", env="KAFKA_SECURITY_PROTOCOL")
    kafka_group_id: str = Field("tqakb-v4", env="KAFKA_GROUP_ID")
    kafka_auto_offset_reset: str = Field("earliest", env="KAFKA_AUTO_OFFSET_RESET")
    kafka_enable_auto_commit: bool = Field(True, env="KAFKA_ENABLE_AUTO_COMMIT")
    
    # Redis Configuration
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_db: int = Field(0, env="REDIS_DB")
    redis_password: Optional[SecretStr] = Field(None, env="REDIS_PASSWORD")
    redis_ssl: bool = Field(False, env="REDIS_SSL")
    redis_pool_size: int = Field(50, env="REDIS_POOL_SIZE")
    redis_pool_max_connections: int = Field(100, env="REDIS_POOL_MAX_CONNECTIONS")
    
    # Neo4j Configuration
    neo4j_uri: str = Field("bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field("neo4j", env="NEO4J_USER")
    neo4j_password: SecretStr = Field("password123", env="NEO4J_PASSWORD")
    neo4j_database: str = Field("neo4j", env="NEO4J_DATABASE")
    neo4j_connection_pool_size: int = Field(50, env="NEO4J_CONNECTION_POOL_SIZE")
    
    # Weaviate Configuration
    weaviate_url: str = Field("http://localhost:8080", env="WEAVIATE_URL")
    weaviate_api_key: Optional[SecretStr] = Field(None, env="WEAVIATE_API_KEY")
    weaviate_batch_size: int = Field(100, env="WEAVIATE_BATCH_SIZE")
    weaviate_timeout: int = Field(60, env="WEAVIATE_TIMEOUT")
    
    # Ollama Configuration
    ollama_host: str = Field("http://localhost:11434", env="OLLAMA_HOST")
    ollama_model: str = Field("llama3.2:latest", env="OLLAMA_MODEL")
    ollama_embedding_model: str = Field("nomic-embed-text:latest", env="OLLAMA_EMBEDDING_MODEL")
    ollama_timeout: int = Field(120, env="OLLAMA_TIMEOUT")
    ollama_num_ctx: int = Field(4096, env="OLLAMA_NUM_CTX")
    
    # Monitoring
    prometheus_enabled: bool = Field(True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(9090, env="PROMETHEUS_PORT")
    otel_enabled: bool = Field(True, env="OTEL_ENABLED")
    otel_exporter_otlp_endpoint: str = Field("http://localhost:4317", env="OTEL_EXPORTER_OTLP_ENDPOINT")
    
    # Security
    jwt_secret_key: SecretStr = Field("change-me-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
    
    # Performance
    async_pool_size: int = Field(100, env="ASYNC_POOL_SIZE")
    batch_size: int = Field(1000, env="BATCH_SIZE")
    cache_ttl: int = Field(3600, env="CACHE_TTL")
    max_retries: int = Field(3, env="MAX_RETRIES")
    retry_delay: float = Field(1.0, env="RETRY_DELAY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() in ["development", "dev"]

    def validate_security_settings(self) -> None:
        """Validate security settings - call this during app startup"""
        import secrets

        # Check JWT secret in production
        if self.is_production():
            default_secrets = [
                "change-me-in-production",
                "password123",
                "secret",
                "password",
                "admin"
            ]

            jwt_secret = self.jwt_secret_key.get_secret_value()
            if jwt_secret in default_secrets or len(jwt_secret) < 32:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: Default or weak JWT_SECRET_KEY detected in production! "
                    f"Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
                )

            # Check Neo4j password
            neo4j_pass = self.neo4j_password.get_secret_value()
            if neo4j_pass in ["password123", "password", "neo4j", "admin"]:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: Default NEO4J_PASSWORD detected in production! "
                    "Use a strong, unique password."
                )

            # Check Redis password if SSL is disabled
            if not self.redis_ssl and self.redis_password:
                import warnings
                warnings.warn(
                    "WARNING: Redis SSL is disabled in production. "
                    "Enable REDIS_SSL=true for encrypted connections.",
                    UserWarning
                )
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_password:
            password = self.redis_password.get_secret_value()
            return f"redis://:{password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_kafka_config(self) -> dict:
        """Get Kafka configuration dictionary"""
        return {
            'bootstrap_servers': self.kafka_bootstrap_servers,
            'security_protocol': self.kafka_security_protocol,
            'group_id': self.kafka_group_id,
            'auto_offset_reset': self.kafka_auto_offset_reset,
            'enable_auto_commit': self.kafka_enable_auto_commit,
        }
    
    def get_neo4j_config(self) -> dict:
        """Get Neo4j configuration dictionary"""
        return {
            'uri': self.neo4j_uri,
            'user': self.neo4j_user,
            'password': self.neo4j_password.get_secret_value(),
            'database': self.neo4j_database,
            'max_connection_pool_size': self.neo4j_connection_pool_size,
        }

# Create singleton instance
settings = Settings()