"""
Kirin Plugin API - Cursor Integration
Provides AI-powered remediation outlines for Cursor vulnerabilities only.
Copyright © 2025 Rick Deacon, Knostic AI - https://knostic.ai
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json

from app.db.database import get_db
from app.models.vulnerability import Vulnerability
from app.models.tool import AITool
from app.schemas.kirin import CursorKirinRemediationRequest, CursorKirinRemediationResponse, KirinVulnerabilityFeed
from app.services.ai_remediation_service import AIRemediationService

router = APIRouter()
logger = logging.getLogger(__name__)

# Kirin Plugin Authentication
KIRIN_PLUGIN_KEY = "kirin-cursor-plugin-v1"

def validate_kirin_plugin_key(x_kirin_key: str = Header(None)):
    """Validate Kirin plugin authentication"""
    if not x_kirin_key or x_kirin_key != KIRIN_PLUGIN_KEY:
        raise HTTPException(
            status_code=401, 
            detail="Invalid Kirin plugin key. Only Cursor plugin integration is supported."
        )
    return True

@router.get("/cursor/vulnerabilities", response_model=KirinVulnerabilityFeed)
async def get_cursor_vulnerabilities_for_kirin(
    since: Optional[datetime] = Query(None, description="Get vulnerabilities since this timestamp"),
    unpatched_only: bool = Query(True, description="Only include unpatched vulnerabilities"),
    limit: int = Query(50, description="Maximum number of results", le=200),
    x_kirin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Get Cursor vulnerabilities for plugin integration
    This endpoint is specifically designed for the Kirin Cursor plugin
    """
    validate_kirin_plugin_key(x_kirin_key)
    
    logger.info("Kirin plugin requesting Cursor vulnerabilities")
    
    # Get Cursor tool
    cursor_tool = db.query(AITool).filter(AITool.name == "cursor").first()
    if not cursor_tool:
        raise HTTPException(status_code=404, detail="Cursor tool not found in database")
    
    # Build query for Cursor vulnerabilities only
    query = db.query(Vulnerability).join(Vulnerability.affected_tools).filter(
        AITool.name == "cursor"
    )
    
    if since:
        query = query.filter(Vulnerability.updated_at >= since)
        
    if unpatched_only:
        query = query.filter(
            Vulnerability.patch_status.in_(["unpatched", "patch_available"])
        )
    
    # Order by severity and discovery date
    query = query.order_by(
        Vulnerability.severity.desc(),
        Vulnerability.discovery_date.desc()
    )
    
    vulnerabilities = query.limit(limit).all()
    
    # Format for Kirin plugin consumption
    kirin_vulns = []
    for vuln in vulnerabilities:
        kirin_vuln = {
            "vulnerability_id": vuln.vulnerability_id,
            "cve_id": vuln.cve_id,
            "title": vuln.title,
            "description": vuln.description,
            "severity": vuln.severity.value,
            "cvss_score": vuln.cvss_score,
            "discovery_date": vuln.discovery_date.isoformat() if vuln.discovery_date else None,
            "patch_status": vuln.patch_status.value,
            "attack_vectors": vuln.attack_vectors or [],
            "technical_details": vuln.technical_details,
            "affected_versions": vuln.affected_versions or [],
            "fixed_versions": vuln.fixed_versions or [],
            "references": vuln.references or [],
            "kirin_remediation_available": vuln.kirin_remediation_available,
            "can_auto_remediate": vuln.auto_remediation_possible,
            "confidence_score": vuln.confidence_score
        }
        kirin_vulns.append(kirin_vuln)
    
    return KirinVulnerabilityFeed(
        vulnerabilities=kirin_vulns,
        total_found=len(kirin_vulns),
        cursor_specific=True,
        generated_at=datetime.utcnow(),
        kirin_plugin_version="1.0.0"
    )

@router.post("/cursor/remediate/{vulnerability_id}")
async def request_cursor_remediation(
    vulnerability_id: str,
    request_data: CursorKirinRemediationRequest,
    x_kirin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Request AI-powered remediation for Cursor vulnerability
    Returns actionable remediation steps that the Kirin plugin can execute
    """
    validate_kirin_plugin_key(x_kirin_key)
    
    logger.info(f"Kirin plugin requesting remediation for {vulnerability_id}")
    
    # Find the vulnerability and verify it affects Cursor
    vulnerability = db.query(Vulnerability).filter(
        Vulnerability.vulnerability_id == vulnerability_id
    ).first()
    
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Verify this vulnerability affects Cursor
    cursor_affected = any(tool.name == "cursor" for tool in vulnerability.affected_tools)
    if not cursor_affected:
        raise HTTPException(
            status_code=400, 
            detail="This vulnerability does not affect Cursor. Kirin plugin only supports Cursor vulnerabilities."
        )
    
    # Generate AI-powered remediation using the service
    ai_service = AIRemediationService()
    
    try:
        remediation = await ai_service.generate_cursor_remediation(
            vulnerability=vulnerability,
            workspace_info=request_data.workspace_info,
            current_version=request_data.cursor_version
        )
        
        # Log the remediation request
        logger.info(f"Generated remediation for {vulnerability_id}: {len(remediation.steps)} steps")
        
        # Update vulnerability to mark remediation as available
        vulnerability.kirin_remediation_available = True
        db.commit()
        
        return CursorKirinRemediationResponse(
            vulnerability_id=vulnerability_id,
            remediation_id=remediation.remediation_id,
            steps=remediation.steps,
            automated_actions=remediation.automated_actions,
            manual_actions=remediation.manual_actions,
            risk_level=remediation.risk_level,
            estimated_time_minutes=remediation.estimated_time_minutes,
            requires_restart=remediation.requires_restart,
            backup_recommended=remediation.backup_recommended,
            success_indicators=remediation.success_indicators,
            rollback_steps=remediation.rollback_steps,
            generated_at=datetime.utcnow(),
            expires_at=remediation.expires_at,
            kirin_compatible=True
        )
        
    except Exception as e:
        logger.error(f"Failed to generate remediation for {vulnerability_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate remediation: {str(e)}"
        )

@router.get("/cursor/remediation-status/{remediation_id}")
async def get_remediation_status(
    remediation_id: str,
    x_kirin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Get status of a remediation action
    Allows the plugin to track remediation progress
    """
    validate_kirin_plugin_key(x_kirin_key)
    
    # This would integrate with a remediation tracking system
    # For now, return basic status info
    
    return {
        "remediation_id": remediation_id,
        "status": "available",
        "message": "Remediation steps ready for Kirin plugin execution",
        "kirin_plugin_compatible": True,
        "cursor_specific": True
    }

@router.post("/cursor/report-remediation")
async def report_remediation_result(
    result_data: Dict[str, Any],
    x_kirin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Kirin Plugin API: Report back remediation results from Kirin plugin
    Allows tracking of successful/failed remediations
    """
    validate_kirin_plugin_key(x_kirin_key)
    
    logger.info(f"Kirin plugin reporting remediation result: {result_data.get('remediation_id')}")
    
    # Log the result for analytics
    remediation_id = result_data.get("remediation_id")
    success = result_data.get("success", False)
    error_message = result_data.get("error_message")
    
    if success:
        logger.info(f"Remediation {remediation_id} completed successfully by Kirin plugin")
    else:
        logger.warning(f"Remediation {remediation_id} failed: {error_message}")
    
    return {
        "acknowledged": True,
        "remediation_id": remediation_id,
        "message": "Remediation result recorded",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/health")
async def kirin_plugin_health():
    """Health check endpoint for Kirin plugin integration"""
    return {
        "status": "healthy",
        "service": "Kirin Plugin API",
        "supported_tools": ["cursor"],
        "api_version": "1.0.0",
        "powered_by": "Knostic AI - https://knostic.ai"
    }