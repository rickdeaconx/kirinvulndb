from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class KirinPluginStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    ERROR = "error"
    UPDATING = "updating"


class KirinPluginStatus(BaseModel):
    plugin_version: str = Field(..., description="Version of the Kirin plugin")
    status: KirinPluginStatusEnum = Field(..., description="Current plugin status")
    last_update: datetime = Field(..., description="Last update timestamp")
    monitored_tools: List[str] = Field(default=[], description="List of tools being monitored")
    active_policies: List[str] = Field(default=[], description="List of active security policies")
    error_message: Optional[str] = Field(None, description="Error message if status is error")


class KirinVulnerability(BaseModel):
    vulnerability_id: str = Field(..., description="Vulnerability ID")
    cve_id: Optional[str] = Field(None, description="CVE ID if available")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Vulnerability description")
    severity: str = Field(..., description="Vulnerability severity")
    cvss_score: Optional[float] = Field(None, description="CVSS score")
    discovery_date: Optional[str] = Field(None, description="Discovery date")
    patch_status: str = Field(..., description="Patch status")
    attack_vectors: List[str] = Field(default=[], description="Attack vectors")
    technical_details: Optional[str] = Field(None, description="Technical details")
    affected_versions: List[str] = Field(default=[], description="Affected versions")
    fixed_versions: List[str] = Field(default=[], description="Fixed versions")
    references: List[str] = Field(default=[], description="Reference URLs")
    kirin_remediation_available: bool = Field(default=False, description="Kirin remediation available")
    can_auto_remediate: bool = Field(default=False, description="Auto remediation possible")
    confidence_score: Optional[float] = Field(None, description="Confidence score")


class KirinVulnerabilityFeed(BaseModel):
    vulnerabilities: List[KirinVulnerability] = Field(..., description="List of vulnerabilities")
    total_found: int = Field(..., description="Total number of vulnerabilities found")
    cursor_specific: bool = Field(..., description="Whether feed is Cursor-specific")
    generated_at: datetime = Field(..., description="Feed generation timestamp")
    kirin_plugin_version: str = Field(..., description="Kirin plugin version")


class KirinRemediationRequest(BaseModel):
    vulnerability_id: str = Field(..., description="Vulnerability ID to remediate")
    context: Dict[str, Any] = Field(default={}, description="Context information for remediation")
    priority: str = Field(default="normal", description="Remediation priority")
    auto_apply: bool = Field(default=False, description="Whether to auto-apply remediation")


class KirinRemediationResponse(BaseModel):
    vulnerability_id: str = Field(..., description="Vulnerability ID")
    remediation_available: bool = Field(..., description="Whether remediation is available")
    remediation_type: Optional[str] = Field(None, description="Type of remediation")
    steps: List[str] = Field(default=[], description="Remediation steps")
    validation_test: Optional[str] = Field(None, description="Validation test command")
    estimated_time: Optional[str] = Field(None, description="Estimated time to complete")
    risk_level: Optional[str] = Field(None, description="Risk level of applying remediation")
    requires_manual_review: bool = Field(default=False, description="Requires manual review")
    backup_required: bool = Field(default=True, description="Backup required before applying")
    reason: Optional[str] = Field(None, description="Reason if remediation not available")


class KirinPolicyRequest(BaseModel):
    request_id: str = Field(..., description="Unique request ID")
    vulnerability_ids: List[str] = Field(..., description="List of vulnerability IDs")
    context: Dict[str, Any] = Field(default={}, description="Context for policy application")
    severity_threshold: Optional[str] = Field(None, description="Minimum severity to apply policy")


class KirinPolicyResponse(BaseModel):
    request_id: str = Field(..., description="Request ID")
    policies_applied: List[Dict[str, Any]] = Field(..., description="List of applied policies")
    overall_action: str = Field(..., description="Overall recommended action")
    applied_at: datetime = Field(..., description="Timestamp when policies were applied")


class KirinToolCompatibility(BaseModel):
    tool_name: str = Field(..., description="AI tool name")
    tool_version: Optional[str] = Field(None, description="Tool version")
    supported: bool = Field(..., description="Whether tool is supported")
    compatibility_level: str = Field(..., description="Compatibility level")
    known_issues: List[str] = Field(default=[], description="Known compatibility issues")
    recommended_settings: Dict[str, Any] = Field(default={}, description="Recommended settings")


class KirinNotification(BaseModel):
    type: str = Field(..., description="Notification type")
    priority: str = Field(..., description="Notification priority")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    vulnerability_ids: List[str] = Field(default=[], description="Related vulnerability IDs")
    action_required: bool = Field(default=False, description="Whether action is required")
    expires_at: Optional[datetime] = Field(None, description="Notification expiry time")


class KirinConfiguration(BaseModel):
    update_interval: int = Field(default=300, description="Update interval in seconds")
    max_vulnerabilities_per_request: int = Field(default=100, description="Max vulnerabilities per request")
    auto_remediation_enabled: bool = Field(default=False, description="Auto remediation enabled")
    notification_levels: List[str] = Field(default=["CRITICAL", "HIGH"], description="Notification levels")
    monitored_tools: List[str] = Field(default=[], description="List of monitored tools")
    security_policies: Dict[str, Any] = Field(default={}, description="Security policies")
    integration_settings: Dict[str, Any] = Field(default={}, description="Integration settings")


class KirinHealthCheck(BaseModel):
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="Plugin version")
    last_communication: datetime = Field(..., description="Last communication timestamp")
    active_connections: int = Field(default=0, description="Active connections count")
    errors: List[str] = Field(default=[], description="Recent errors")
    performance_metrics: Dict[str, Any] = Field(default={}, description="Performance metrics")


class KirinAnalytics(BaseModel):
    time_period: str = Field(..., description="Analytics time period")
    vulnerabilities_processed: int = Field(default=0, description="Total vulnerabilities processed")
    remediations_applied: int = Field(default=0, description="Total remediations applied")
    policies_enforced: int = Field(default=0, description="Total policies enforced")
    success_rate: float = Field(default=0.0, description="Success rate percentage")
    most_affected_tools: List[Dict[str, Any]] = Field(default=[], description="Most affected tools")
    threat_trends: Dict[str, Any] = Field(default={}, description="Threat trends data")


class KirinWebhookPayload(BaseModel):
    event_type: str = Field(..., description="Webhook event type")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    signature: Optional[str] = Field(None, description="Webhook signature for verification")


class KirinExportRequest(BaseModel):
    format: str = Field(default="json", description="Export format (json, csv, xml)")
    vulnerability_ids: Optional[List[str]] = Field(None, description="Specific vulnerability IDs to export")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range filter")
    include_remediation: bool = Field(default=True, description="Include remediation data")
    include_analytics: bool = Field(default=False, description="Include analytics data")


class KirinExportResponse(BaseModel):
    export_id: str = Field(..., description="Export request ID")
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    expires_at: datetime = Field(..., description="Download URL expiry time")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    created_at: datetime = Field(..., description="Export creation timestamp")


# New schemas for Cursor plugin integration
class RemediationRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class RemediationStepType(str, Enum):
    AUTOMATED = "automated"
    MANUAL = "manual"
    VERIFICATION = "verification"

class WorkspaceInfo(BaseModel):
    """Information about the user's Cursor workspace"""
    project_path: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    cursor_version: Optional[str] = None
    extensions: List[str] = Field(default=[])

class CursorKirinRemediationRequest(BaseModel):
    """Request for AI-powered remediation from Kirin plugin (Cursor-specific)"""
    workspace_info: WorkspaceInfo
    cursor_version: str = Field(..., description="Current Cursor version")
    priority: str = Field(default="medium", description="Remediation priority")
    auto_apply: bool = Field(default=False, description="Allow automatic application")

class RemediationStep(BaseModel):
    """Individual remediation step for Cursor"""
    step_id: str
    step_type: RemediationStepType
    title: str
    description: str
    command: Optional[str] = None  # For automated steps
    instructions: Optional[str] = None  # For manual steps
    expected_outcome: str
    risk_level: RemediationRiskLevel
    estimated_seconds: int = 30
    prerequisites: List[str] = Field(default=[])

class AutomatedAction(BaseModel):
    """Automated action that Kirin plugin can execute"""
    action_id: str
    action_type: str  # "setting_change", "extension_disable", "config_update", etc.
    target: str  # What to modify
    old_value: Optional[str] = None
    new_value: str
    reversible: bool = True
    backup_location: Optional[str] = None

class ManualAction(BaseModel):
    """Manual action requiring user intervention"""
    action_id: str
    title: str
    description: str
    instructions: List[str]
    verification_steps: List[str]
    estimated_minutes: int = 5

class CursorKirinRemediationResponse(BaseModel):
    """AI-generated remediation response for Kirin plugin (Cursor-specific)"""
    vulnerability_id: str
    remediation_id: str
    steps: List[RemediationStep]
    automated_actions: List[AutomatedAction]
    manual_actions: List[ManualAction]
    risk_level: RemediationRiskLevel
    estimated_time_minutes: int
    requires_restart: bool = False
    backup_recommended: bool = True
    success_indicators: List[str]
    rollback_steps: List[str]
    generated_at: datetime
    expires_at: datetime
    kirin_compatible: bool = True