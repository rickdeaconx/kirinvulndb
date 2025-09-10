from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class AIToolBase(BaseModel):
    name: str = Field(..., max_length=100, description="Tool name (unique identifier)")
    display_name: str = Field(..., max_length=200, description="Display name for UI")
    vendor: str = Field(..., max_length=100, description="Tool vendor/company")
    description: Optional[str] = Field(None, description="Tool description")


class AIToolCreate(AIToolBase):
    current_version: Optional[str] = Field(None, description="Current version")
    supported_languages: Optional[List[str]] = Field(None, description="Supported programming languages")
    platform_support: Optional[List[str]] = Field(None, description="Supported platforms")
    security_contact: Optional[str] = Field(None, description="Security contact email")
    security_policy_url: Optional[str] = Field(None, description="Security policy URL")
    vulnerability_disclosure_url: Optional[str] = Field(None, description="Vulnerability disclosure URL")
    is_actively_monitored: bool = Field(default=True, description="Whether tool is actively monitored")
    monitoring_priority: float = Field(default=1.0, description="Monitoring priority (higher = more frequent)")
    api_endpoints: Optional[Dict[str, str]] = Field(None, description="API endpoints for security data")
    rss_feeds: Optional[List[str]] = Field(None, description="Security RSS/Atom feeds")
    github_repos: Optional[List[str]] = Field(None, description="Related GitHub repositories")
    
    @validator('security_policy_url', 'vulnerability_disclosure_url')
    def validate_urls(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v
    
    @validator('rss_feeds')
    def validate_rss_feeds(cls, v):
        if v:
            for feed in v:
                if not feed.startswith(('http://', 'https://')):
                    raise ValueError(f"Invalid RSS feed URL: {feed}")
        return v


class AIToolUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=200)
    vendor: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)
    current_version: Optional[str] = Field(None)
    supported_languages: Optional[List[str]] = Field(None)
    platform_support: Optional[List[str]] = Field(None)
    security_contact: Optional[str] = Field(None)
    security_policy_url: Optional[str] = Field(None)
    vulnerability_disclosure_url: Optional[str] = Field(None)
    is_actively_monitored: Optional[bool] = Field(None)
    monitoring_priority: Optional[float] = Field(None)
    api_endpoints: Optional[Dict[str, str]] = Field(None)
    rss_feeds: Optional[List[str]] = Field(None)
    github_repos: Optional[List[str]] = Field(None)
    
    @validator('security_policy_url', 'vulnerability_disclosure_url')
    def validate_urls(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class AIToolResponse(AIToolBase):
    id: str = Field(..., description="Internal UUID")
    current_version: Optional[str] = Field(None)
    supported_languages: Optional[List[str]] = Field(None)
    platform_support: Optional[List[str]] = Field(None)
    security_contact: Optional[str] = Field(None)
    security_policy_url: Optional[str] = Field(None)
    vulnerability_disclosure_url: Optional[str] = Field(None)
    is_actively_monitored: bool = Field(...)
    monitoring_priority: float = Field(...)
    last_security_check: Optional[str] = Field(None)
    api_endpoints: Optional[Dict[str, str]] = Field(None)
    rss_feeds: Optional[List[str]] = Field(None)
    github_repos: Optional[List[str]] = Field(None)
    total_vulnerabilities: float = Field(...)
    critical_vulnerabilities: float = Field(...)
    last_vulnerability_date: Optional[str] = Field(None)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    
    class Config:
        from_attributes = True


class AIToolList(BaseModel):
    tools: List[Dict[str, Any]] = Field(...)
    total: int = Field(..., description="Total number of tools")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Offset used for pagination")
    
    class Config:
        from_attributes = True


class AIToolSummary(BaseModel):
    """Lightweight tool summary for lists"""
    id: str
    name: str
    display_name: str
    vendor: str
    is_actively_monitored: bool
    total_vulnerabilities: int
    critical_vulnerabilities: int
    
    class Config:
        from_attributes = True