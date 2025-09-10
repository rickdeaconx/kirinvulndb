from sqlalchemy import Column, String, Text, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from .base import Base
from .vulnerability import vulnerability_tool_association


class AITool(Base):
    """AI Coding Assistant Tool model"""
    __tablename__ = "aitool"
    
    # Basic information
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    vendor = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Tool details
    current_version = Column(String(50), nullable=True)
    supported_languages = Column(JSON, nullable=True)  # List of programming languages
    platform_support = Column(JSON, nullable=True)    # List of supported platforms
    
    # Security configuration
    security_contact = Column(String(200), nullable=True)
    security_policy_url = Column(String(500), nullable=True)
    vulnerability_disclosure_url = Column(String(500), nullable=True)
    
    # Monitoring configuration
    is_actively_monitored = Column(Boolean, default=True)
    monitoring_priority = Column(Float, default=1.0)  # Higher = more frequent monitoring
    last_security_check = Column(String(100), nullable=True)
    
    # Vendor-specific API details
    api_endpoints = Column(JSON, nullable=True)  # Vendor API endpoints for security data
    rss_feeds = Column(JSON, nullable=True)      # Security RSS/Atom feeds
    github_repos = Column(JSON, nullable=True)   # Related GitHub repositories
    
    # Statistics
    total_vulnerabilities = Column(Float, default=0)
    critical_vulnerabilities = Column(Float, default=0)
    last_vulnerability_date = Column(String(100), nullable=True)
    
    # Many-to-many relationship with vulnerabilities
    vulnerabilities = relationship(
        "Vulnerability",
        secondary=vulnerability_tool_association,
        back_populates="affected_tools"
    )
    
    def __repr__(self):
        return f"<AITool(name={self.name}, vendor={self.vendor})>"
    
    @property
    def vulnerability_count(self) -> int:
        return len(self.vulnerabilities)
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "vendor": self.vendor,
            "description": self.description,
            "current_version": self.current_version,
            "supported_languages": self.supported_languages,
            "platform_support": self.platform_support,
            "is_actively_monitored": self.is_actively_monitored,
            "total_vulnerabilities": self.total_vulnerabilities,
            "critical_vulnerabilities": self.critical_vulnerabilities,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }