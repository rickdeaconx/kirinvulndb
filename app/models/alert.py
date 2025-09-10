from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base
import enum
from datetime import datetime


class AlertTypeEnum(str, enum.Enum):
    NEW_VULNERABILITY = "new_vulnerability"
    SEVERITY_UPGRADE = "severity_upgrade"
    EXPLOIT_AVAILABLE = "exploit_available"
    PATCH_AVAILABLE = "patch_available"
    MASS_EXPLOITATION = "mass_exploitation"
    ZERO_DAY = "zero_day"


class AlertPriorityEnum(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertStatusEnum(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class Alert(Base):
    """Alert notifications for vulnerabilities"""
    __tablename__ = "alert"
    
    # Foreign key to vulnerability
    vulnerability_id = Column(UUID(as_uuid=True), ForeignKey('vulnerability.id'), nullable=False)
    
    # Alert details
    alert_type = Column(Enum(AlertTypeEnum), nullable=False)
    priority = Column(Enum(AlertPriorityEnum), nullable=False)
    status = Column(Enum(AlertStatusEnum), nullable=False, default=AlertStatusEnum.PENDING)
    
    # Content
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    
    # Targeting
    target_audience = Column(JSON, nullable=True)  # List of user groups or individual users
    channels = Column(JSON, nullable=True)  # List of notification channels (email, slack, etc.)
    
    # Scheduling
    scheduled_time = Column(DateTime(timezone=True), nullable=True)
    sent_time = Column(DateTime(timezone=True), nullable=True)
    acknowledged_time = Column(DateTime(timezone=True), nullable=True)
    
    # Conditions
    trigger_conditions = Column(JSON, nullable=True)  # Conditions that triggered this alert
    suppression_rules = Column(JSON, nullable=True)   # Rules for suppressing similar alerts
    
    # Tracking
    retry_count = Column(String(5), default=0)
    last_retry = Column(DateTime(timezone=True), nullable=True)
    delivery_failures = Column(JSON, nullable=True)  # Track delivery failures by channel
    
    # Metrics
    open_rate = Column(String(5), nullable=True)
    click_rate = Column(String(5), nullable=True)
    
    # Auto-generated fields
    is_automated = Column(Boolean, default=True)
    correlation_id = Column(String(100), nullable=True)  # Group related alerts
    
    # Relationship back to vulnerability
    vulnerability = relationship("Vulnerability", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(type={self.alert_type}, priority={self.priority}, title={self.title[:50]})>"
    
    @property
    def is_critical(self) -> bool:
        return self.priority == AlertPriorityEnum.CRITICAL
    
    @property
    def is_pending(self) -> bool:
        return self.status == AlertStatusEnum.PENDING
    
    def mark_sent(self):
        self.status = AlertStatusEnum.SENT
        self.sent_time = datetime.utcnow()
    
    def mark_acknowledged(self):
        self.status = AlertStatusEnum.ACKNOWLEDGED
        self.acknowledged_time = datetime.utcnow()
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "vulnerability_id": str(self.vulnerability_id),
            "alert_type": self.alert_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "title": self.title,
            "message": self.message,
            "summary": self.summary,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "sent_time": self.sent_time.isoformat() if self.sent_time else None,
            "is_automated": self.is_automated,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }