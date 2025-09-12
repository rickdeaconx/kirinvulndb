from sqlalchemy import Column, String, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, UUID_TYPE
import enum


class ReferenceTypeEnum(str, enum.Enum):
    CVE = "cve"
    VENDOR_ADVISORY = "vendor_advisory"
    SECURITY_BLOG = "security_blog"
    EXPLOIT_DB = "exploit_db"
    GITHUB_ISSUE = "github_issue"
    RESEARCH_PAPER = "research_paper"
    NEWS_ARTICLE = "news_article"
    SOCIAL_MEDIA = "social_media"
    DOCUMENTATION = "documentation"


class Reference(Base):
    """External references for vulnerabilities"""
    __tablename__ = "reference"
    
    # Basic information
    url = Column(String(1000), nullable=False)
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    reference_type = Column(Enum(ReferenceTypeEnum), nullable=False)
    
    # Source information
    source_domain = Column(String(200), nullable=True)
    author = Column(String(200), nullable=True)
    publication_date = Column(String(100), nullable=True)
    
    # Quality metrics
    credibility_score = Column(String(5), nullable=True)  # 0.0 to 1.0
    relevance_score = Column(String(5), nullable=True)   # 0.0 to 1.0
    
    # Tracking
    last_checked = Column(String(100), nullable=True)
    is_accessible = Column(String(20), default=True)
    
    def __repr__(self):
        return f"<Reference(type={self.reference_type}, url={self.url[:50]})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "reference_type": self.reference_type.value,
            "source_domain": self.source_domain,
            "author": self.author,
            "publication_date": self.publication_date,
            "credibility_score": self.credibility_score,
            "relevance_score": self.relevance_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }