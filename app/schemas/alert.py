from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.alert import AlertTypeEnum, AlertPriorityEnum, AlertStatusEnum


class AlertBase(BaseModel):
    alert_type: AlertTypeEnum = Field(..., description="Type of alert")
    priority: AlertPriorityEnum = Field(..., description="Alert priority level")
    title: str = Field(..., max_length=500, description="Alert title")
    message: str = Field(..., description="Alert message content")
    summary: Optional[str] = Field(None, description="Brief summary")


class AlertCreate(AlertBase):
    vulnerability_id: str = Field(..., description="Associated vulnerability ID")
    target_audience: Optional[List[str]] = Field(None, description="Target user groups")
    channels: Optional[List[str]] = Field(None, description="Notification channels")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled delivery time")
    trigger_conditions: Optional[Dict[str, Any]] = Field(None, description="Trigger conditions")
    suppression_rules: Optional[Dict[str, Any]] = Field(None, description="Suppression rules")
    is_automated: bool = Field(default=True, description="Whether alert is automated")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for grouping")


class AlertUpdate(BaseModel):
    status: Optional[AlertStatusEnum] = Field(None)
    title: Optional[str] = Field(None, max_length=500)
    message: Optional[str] = Field(None)
    summary: Optional[str] = Field(None)
    target_audience: Optional[List[str]] = Field(None)
    channels: Optional[List[str]] = Field(None)
    scheduled_time: Optional[datetime] = Field(None)


class AlertResponse(AlertBase):
    id: str = Field(..., description="Internal UUID")
    vulnerability_id: str = Field(..., description="Associated vulnerability ID")
    status: AlertStatusEnum = Field(..., description="Current alert status")
    target_audience: Optional[List[str]] = Field(None)
    channels: Optional[List[str]] = Field(None)
    scheduled_time: Optional[datetime] = Field(None)
    sent_time: Optional[datetime] = Field(None)
    acknowledged_time: Optional[datetime] = Field(None)
    trigger_conditions: Optional[Dict[str, Any]] = Field(None)
    suppression_rules: Optional[Dict[str, Any]] = Field(None)
    retry_count: str = Field(...)
    last_retry: Optional[datetime] = Field(None)
    delivery_failures: Optional[Dict[str, Any]] = Field(None)
    open_rate: Optional[str] = Field(None)
    click_rate: Optional[str] = Field(None)
    is_automated: bool = Field(...)
    correlation_id: Optional[str] = Field(None)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    
    class Config:
        from_attributes = True


class AlertList(BaseModel):
    alerts: List[Dict[str, Any]] = Field(...)
    total: int = Field(..., description="Total number of alerts")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Offset used for pagination")
    
    class Config:
        from_attributes = True


class AlertSummary(BaseModel):
    """Lightweight alert summary for lists"""
    id: str
    alert_type: AlertTypeEnum
    priority: AlertPriorityEnum
    status: AlertStatusEnum
    title: str
    created_at: datetime
    
    class Config:
        from_attributes = True