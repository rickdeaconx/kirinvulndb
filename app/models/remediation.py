from sqlalchemy import Column, String, Text, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from .base import Base, UUID_TYPE
import enum


class RemediationTypeEnum(str, enum.Enum):
    CODE_PATCH = "code_patch"
    CONFIGURATION = "configuration"
    UPDATE_DEPENDENCY = "update_dependency"
    POLICY_CHANGE = "policy_change"
    WORKAROUND = "workaround"


class RemediationStatusEnum(str, enum.Enum):
    AVAILABLE = "available"
    IN_DEVELOPMENT = "in_development"
    TESTING = "testing"
    DEPLOYED = "deployed"
    FAILED = "failed"


class Remediation(Base):
    """Remediation solutions for vulnerabilities"""
    __tablename__ = "remediation"
    
    # Foreign key to vulnerability
    vulnerability_id = Column(UUID_TYPE, ForeignKey('vulnerability.id'), nullable=False)
    
    # Remediation details
    remediation_type = Column(Enum(RemediationTypeEnum), nullable=False)
    status = Column(Enum(RemediationStatusEnum), nullable=False, default=RemediationStatusEnum.AVAILABLE)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Implementation details
    code_changes = Column(Text, nullable=True)  # Actual code changes or patches
    configuration_changes = Column(JSON, nullable=True)  # Config changes needed
    dependencies = Column(JSON, nullable=True)  # Required dependencies/versions
    
    # Kirin-specific
    kirin_policy_id = Column(String(100), nullable=True)
    auto_applicable = Column(Boolean, default=False)
    validation_test = Column(Text, nullable=True)  # Test to verify fix
    rollback_instructions = Column(Text, nullable=True)
    
    # Metadata
    effectiveness_score = Column(String(5), nullable=True)  # 0.0 to 1.0
    complexity_level = Column(String(20), nullable=True)  # low, medium, high
    estimated_time = Column(String(50), nullable=True)  # Time to implement
    side_effects = Column(Text, nullable=True)
    
    # Success tracking
    success_rate = Column(String(5), default=0.0)
    times_applied = Column(String(10), default=0)
    
    # Relationship back to vulnerability
    vulnerability = relationship("Vulnerability", back_populates="remediations")
    
    def __repr__(self):
        return f"<Remediation(type={self.remediation_type}, title={self.title})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "vulnerability_id": str(self.vulnerability_id),
            "remediation_type": self.remediation_type.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "auto_applicable": self.auto_applicable,
            "effectiveness_score": self.effectiveness_score,
            "complexity_level": self.complexity_level,
            "estimated_time": self.estimated_time,
            "success_rate": self.success_rate,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }