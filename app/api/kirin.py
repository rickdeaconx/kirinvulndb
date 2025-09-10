from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.db.database import get_db
from app.models.vulnerability import Vulnerability, SeverityEnum, PatchStatusEnum
from app.models.tool import AITool
from app.schemas.kirin import (
    KirinPluginStatus,
    KirinRemediationRequest, 
    KirinRemediationResponse,
    KirinPolicyRequest,
    KirinPolicyResponse,
    KirinVulnerabilityFeed
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/vulnerabilities/feed", response_model=KirinVulnerabilityFeed)
async def get_kirin_vulnerability_feed(
    since: Optional[datetime] = Query(None, description="Get vulnerabilities since this timestamp"),
    tools: Optional[str] = Query(None, description="Comma-separated list of tool names"),
    severity: Optional[SeverityEnum] = Query(None, description="Minimum severity level"),
    unpatched_only: bool = Query(True, description="Only include unpatched vulnerabilities"),
    limit: int = Query(100, description="Maximum number of results", le=1000),
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Get vulnerability feed for real-time monitoring
    This endpoint provides vulnerabilities specifically formatted for the Kirin plugin
    """
    
    # Default to last 24 hours if no since timestamp provided
    if not since:
        since = datetime.utcnow() - timedelta(hours=24)
    
    # Build query
    query = db.query(Vulnerability).filter(
        Vulnerability.updated_at >= since
    )
    
    # Filter by tools if specified
    if tools:
        tool_list = [tool.strip() for tool in tools.split(',')]
        query = query.join(Vulnerability.affected_tools).filter(
            AITool.name.in_(tool_list)
        )
    
    # Filter by severity
    if severity:
        severity_hierarchy = {
            SeverityEnum.CRITICAL: 0,
            SeverityEnum.HIGH: 1,
            SeverityEnum.MEDIUM: 2,
            SeverityEnum.LOW: 3,
            SeverityEnum.INFO: 4
        }
        min_level = severity_hierarchy.get(severity, 4)
        allowed_severities = [s for s, level in severity_hierarchy.items() if level <= min_level]
        query = query.filter(Vulnerability.severity.in_(allowed_severities))
    
    # Filter unpatched only
    if unpatched_only:
        query = query.filter(Vulnerability.patch_status == PatchStatusEnum.UNPATCHED)
    
    # Order by severity (critical first) then by discovery date
    query = query.order_by(
        Vulnerability.severity.asc(),  # Enum ordering: CRITICAL=0, HIGH=1, etc.
        Vulnerability.discovery_date.desc()
    )
    
    vulnerabilities = query.limit(limit).all()
    
    # Format for Kirin plugin
    kirin_vulnerabilities = []
    for vuln in vulnerabilities:
        kirin_vuln = {
            "id": vuln.vulnerability_id,
            "cve_id": vuln.cve_id,
            "title": vuln.title,
            "description": vuln.description,
            "severity": vuln.severity.value,
            "cvss_score": vuln.cvss_score,
            "affected_tools": [tool.name for tool in vuln.affected_tools],
            "attack_vectors": [av.value if hasattr(av, 'value') else av for av in vuln.attack_vectors] if vuln.attack_vectors else [],
            "patch_status": vuln.patch_status.value,
            "poc_available": vuln.poc_available,
            "exploit_in_wild": vuln.exploit_in_wild,
            "discovery_date": vuln.discovery_date.isoformat() if vuln.discovery_date else None,
            "kirin_remediation_available": vuln.kirin_remediation_available,
            "kirin_policy_mappings": vuln.kirin_policy_mappings or {},
            "auto_remediation_possible": vuln.auto_remediation_possible,
            "references": vuln.references,
            "tags": vuln.tags,
            "updated_at": vuln.updated_at.isoformat()
        }
        kirin_vulnerabilities.append(kirin_vuln)
    
    return KirinVulnerabilityFeed(
        vulnerabilities=kirin_vulnerabilities,
        total_count=len(kirin_vulnerabilities),
        last_updated=datetime.utcnow(),
        next_update_eta=datetime.utcnow() + timedelta(minutes=5)  # Next expected update
    )


@router.post("/plugin/status")
async def update_plugin_status(
    status: KirinPluginStatus,
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Update plugin status and configuration
    Allows the plugin to report its status and receive configuration updates
    """
    
    logger.info(f"Kirin plugin status update: {status.plugin_version} - {status.status}")
    
    # Store plugin status (would typically go to a plugin_status table)
    # For now, just log and return configuration
    
    # Return current configuration for the plugin
    return {
        "status": "acknowledged",
        "server_version": "1.0.0",
        "configuration": {
            "update_interval": 300,  # 5 minutes
            "max_vulnerabilities_per_request": 100,
            "auto_remediation_enabled": True,
            "notification_levels": ["CRITICAL", "HIGH"],
            "monitored_tools": [
                "cursor", "github_copilot", "amazon_codewhisperer", 
                "tabnine", "codeium", "replit_ghostwriter"
            ]
        },
        "policies": {
            "block_critical_vulnerabilities": True,
            "warn_on_high_severity": True,
            "auto_update_definitions": True
        }
    }


@router.post("/remediation/request", response_model=KirinRemediationResponse)
async def request_remediation(
    request: KirinRemediationRequest,
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Request automatic remediation for a vulnerability
    """
    
    # Find the vulnerability
    vuln = db.query(Vulnerability).filter(
        Vulnerability.vulnerability_id == request.vulnerability_id
    ).first()
    
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Check if remediation is available
    if not vuln.kirin_remediation_available:
        return KirinRemediationResponse(
            vulnerability_id=request.vulnerability_id,
            remediation_available=False,
            reason="No automated remediation available for this vulnerability"
        )
    
    # Generate remediation based on vulnerability type
    remediation_steps = generate_remediation_steps(vuln, request.context)
    
    return KirinRemediationResponse(
        vulnerability_id=request.vulnerability_id,
        remediation_available=True,
        remediation_type="code_patch",
        steps=remediation_steps,
        validation_test=f"test_vulnerability_{vuln.vulnerability_id.replace('-', '_')}",
        estimated_time="5-10 minutes",
        risk_level="low",
        requires_manual_review=vuln.severity in [SeverityEnum.CRITICAL, SeverityEnum.HIGH],
        backup_required=True
    )


@router.post("/policy/apply", response_model=KirinPolicyResponse)
async def apply_security_policy(
    request: KirinPolicyRequest,
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Apply security policy based on vulnerability assessment
    """
    
    policies_applied = []
    
    # Process each vulnerability in the request
    for vuln_id in request.vulnerability_ids:
        vuln = db.query(Vulnerability).filter(
            Vulnerability.vulnerability_id == vuln_id
        ).first()
        
        if vuln:
            policy = determine_security_policy(vuln, request.context)
            policies_applied.append({
                "vulnerability_id": vuln_id,
                "policy": policy,
                "severity": vuln.severity.value,
                "action": policy["action"]
            })
    
    return KirinPolicyResponse(
        request_id=request.request_id,
        policies_applied=policies_applied,
        overall_action=determine_overall_action(policies_applied),
        applied_at=datetime.utcnow()
    )


@router.get("/tools/compatibility")
async def get_tool_compatibility(
    tool_name: str = Query(..., description="Name of the AI tool"),
    tool_version: Optional[str] = Query(None, description="Version of the AI tool"),
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Check compatibility and get tool-specific vulnerability information
    """
    
    # Find the tool
    tool = db.query(AITool).filter(AITool.name == tool_name).first()
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    # Get recent vulnerabilities for this tool
    recent_vulns = db.query(Vulnerability).join(Vulnerability.affected_tools).filter(
        AITool.name == tool_name,
        Vulnerability.updated_at >= datetime.utcnow() - timedelta(days=30)
    ).order_by(Vulnerability.severity.asc()).limit(10).all()
    
    # Check version compatibility
    version_status = "unknown"
    if tool_version and tool.current_version:
        if tool_version == tool.current_version:
            version_status = "current"
        elif tool_version < tool.current_version:
            version_status = "outdated"
        else:
            version_status = "newer"
    
    return {
        "tool": {
            "name": tool.name,
            "display_name": tool.display_name,
            "vendor": tool.vendor,
            "current_version": tool.current_version,
            "is_monitored": tool.is_actively_monitored
        },
        "compatibility": {
            "supported": True,
            "version_status": version_status,
            "recommended_version": tool.current_version
        },
        "security_status": {
            "total_vulnerabilities": tool.total_vulnerabilities,
            "critical_vulnerabilities": tool.critical_vulnerabilities,
            "recent_vulnerabilities": len(recent_vulns),
            "risk_level": get_risk_level(tool.critical_vulnerabilities, tool.total_vulnerabilities)
        },
        "recent_vulnerabilities": [
            {
                "id": vuln.vulnerability_id,
                "severity": vuln.severity.value,
                "title": vuln.title,
                "patch_status": vuln.patch_status.value,
                "kirin_remediation_available": vuln.kirin_remediation_available
            }
            for vuln in recent_vulns
        ]
    }


@router.post("/vulnerabilities/report")
async def report_vulnerability_status(
    vulnerability_id: str,
    status_update: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Report vulnerability remediation status back to the database
    """
    
    vuln = db.query(Vulnerability).filter(
        Vulnerability.vulnerability_id == vulnerability_id
    ).first()
    
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Update vulnerability status based on plugin report
    if status_update.get("remediation_applied"):
        # Mark as patched if remediation was successfully applied
        if status_update.get("remediation_successful"):
            vuln.patch_status = PatchStatusEnum.PATCHED
            logger.info(f"Vulnerability {vulnerability_id} marked as patched by Kirin plugin")
        else:
            logger.warning(f"Remediation failed for vulnerability {vulnerability_id}: {status_update.get('error')}")
    
    # Update Kirin-specific metadata
    kirin_metadata = vuln.kirin_policy_mappings or {}
    kirin_metadata.update({
        "last_plugin_update": datetime.utcnow().isoformat(),
        "plugin_status": status_update.get("status"),
        "remediation_attempts": kirin_metadata.get("remediation_attempts", 0) + (1 if status_update.get("remediation_applied") else 0)
    })
    vuln.kirin_policy_mappings = kirin_metadata
    
    db.commit()
    
    return {
        "status": "updated",
        "vulnerability_id": vulnerability_id,
        "updated_at": datetime.utcnow().isoformat()
    }


def generate_remediation_steps(vuln: Vulnerability, context: Dict[str, Any]) -> List[str]:
    """Generate specific remediation steps for a vulnerability"""
    
    steps = []
    
    # Base steps for all vulnerabilities
    steps.append("1. Create backup of current code state")
    steps.append("2. Review vulnerability details and impact assessment")
    
    # Severity-specific steps
    if vuln.severity == SeverityEnum.CRITICAL:
        steps.append("3. URGENT: Immediately disable affected functionality if possible")
        steps.append("4. Apply security patches to vulnerable components")
        steps.append("5. Implement additional security controls")
    elif vuln.severity == SeverityEnum.HIGH:
        steps.append("3. Apply security patches within 24 hours")
        steps.append("4. Update dependency versions to patched versions")
    else:
        steps.append("3. Schedule remediation within maintenance window")
        steps.append("4. Apply patches during next deployment cycle")
    
    # Attack vector specific steps
    if vuln.attack_vectors:
        for vector in vuln.attack_vectors:
            if vector.value == "prompt_injection":
                steps.append("5. Implement input sanitization and validation")
                steps.append("6. Add prompt injection detection filters")
            elif vector.value == "rce":
                steps.append("5. Restrict code execution permissions")
                steps.append("6. Implement sandbox environments")
    
    steps.append(f"{len(steps) + 1}. Run validation tests to confirm fix")
    steps.append(f"{len(steps) + 1}. Monitor for any regression issues")
    
    return steps


def determine_security_policy(vuln: Vulnerability, context: Dict[str, Any]) -> Dict[str, Any]:
    """Determine security policy action for a vulnerability"""
    
    if vuln.severity == SeverityEnum.CRITICAL:
        return {
            "action": "block",
            "reason": "Critical vulnerability detected",
            "immediate_action_required": True,
            "notification_priority": "urgent"
        }
    elif vuln.severity == SeverityEnum.HIGH:
        return {
            "action": "warn",
            "reason": "High severity vulnerability detected", 
            "remediation_timeline": "24 hours",
            "notification_priority": "high"
        }
    else:
        return {
            "action": "log",
            "reason": "Vulnerability logged for review",
            "remediation_timeline": "next maintenance window",
            "notification_priority": "normal"
        }


def determine_overall_action(policies: List[Dict[str, Any]]) -> str:
    """Determine overall action based on all policies"""
    
    if any(p["policy"]["action"] == "block" for p in policies):
        return "block"
    elif any(p["policy"]["action"] == "warn" for p in policies):
        return "warn"
    else:
        return "log"


def get_risk_level(critical_count: float, total_count: float) -> str:
    """Calculate risk level based on vulnerability counts"""
    
    if critical_count > 0:
        return "high"
    elif total_count > 5:
        return "medium"
    elif total_count > 0:
        return "low"
    else:
        return "none"