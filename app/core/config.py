from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "Kirin Vulnerability Database - Cursor AI Security"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Real-time vulnerability monitoring for Cursor IDE and AI coding assistants"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./kirinvulndb.db"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "kirinvulndb"
    DATABASE_USER: str = "kirinuser"
    DATABASE_PASSWORD: str = "kirinpassword"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_VULNERABILITIES: str = "vulnerabilities"
    KAFKA_TOPIC_ALERTS: str = "alerts"
    KAFKA_GROUP_ID: str = "kirinvulndb"
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_VULNERABILITIES: str = "vulnerabilities"
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    
    # API Security
    API_SECRET_KEY: str = "your-super-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY_HEADER: str = "X-API-Key"
    
    # External APIs
    NVD_API_KEY: Optional[str] = None
    NVD_BASE_URL: str = "https://services.nvd.nist.gov/rest/json"
    SHODAN_API_KEY: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_BURST: int = 10
    
    # Collection intervals (seconds)
    CVE_COLLECTION_INTERVAL: int = 300      # 5 minutes
    VENDOR_COLLECTION_INTERVAL: int = 600   # 10 minutes
    COMMUNITY_COLLECTION_INTERVAL: int = 3600  # 1 hour
    
    # WebSocket
    WEBSOCKET_MAX_CONNECTIONS: int = 10000
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    # Monitoring
    PROMETHEUS_PORT: int = 8000
    METRICS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Notification services
    SLACK_WEBHOOK_URL: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None
    EMAIL_SMTP_HOST: Optional[str] = None
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_USE_TLS: bool = True
    
    # AI Tools to monitor
    MONITORED_TOOLS: List[str] = [
        "cursor",
        "github_copilot",
        "amazon_codewhisperer", 
        "tabnine",
        "codeium",
        "replit_ghostwriter",
        "sourcegraph_cody",
        "jetbrains_ai_assistant"
    ]
    
    # Data retention
    VULNERABILITY_RETENTION_DAYS: int = 730  # 2 years
    ALERT_RETENTION_DAYS: int = 90
    LOG_RETENTION_DAYS: int = 30
    
    # Cache settings
    CACHE_TTL_VULNERABILITIES: int = 300    # 5 minutes
    CACHE_TTL_STATISTICS: int = 60          # 1 minute
    CACHE_TTL_API_RESPONSES: int = 30       # 30 seconds
    
    # Security settings
    ALLOWED_HOSTS: List[str] = ["*"]
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Worker settings
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    MAX_WORKERS: int = 4
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set Celery URLs based on Redis if not explicitly set
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL


# Create global settings instance
settings = Settings()