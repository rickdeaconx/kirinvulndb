"""
Admin API endpoints for vulnerability management
Includes AI-powered vulnerability submission and analysis
Copyright © 2025 Rick Deacon, Knostic AI - https://knostic.ai
"""

from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid

from app.db.database import get_db
from app.models.vulnerability import Vulnerability, SeverityEnum, PatchStatusEnum, AttackVectorEnum
from app.models.tool import AITool
from app.services.ai_vulnerability_analyzer import AIVulnerabilityAnalyzer, VulnerabilityAnalysis
from app.services.websocket_manager import websocket_manager
from app.services.llm_enhancer import llm_enhancer, create_slug
from app.schemas.vulnerability import VulnerabilityResponse
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)

# Admin authentication key
ADMIN_API_KEY = "kirin-admin-2025-v1"

class VulnerabilitySubmission(BaseModel):
    """Schema for admin vulnerability submission"""
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Detailed vulnerability description")
    cve_id: Optional[str] = Field(None, description="CVE ID if available")
    references: List[str] = Field(default=[], description="Reference URLs")
    reporter_name: Optional[str] = Field(None, description="Name of person reporting")
    reporter_email: Optional[str] = Field(None, description="Reporter email")
    additional_context: Optional[str] = Field(None, description="Additional context or notes")
    priority: str = Field(default="medium", description="Submission priority")

class VulnerabilityAnalysisResponse(BaseModel):
    """Response schema for vulnerability analysis"""
    vulnerability_id: str
    analysis: Dict[str, Any]
    ai_enhanced_data: Dict[str, Any]
    confidence_score: float
    processing_status: str
    created_at: datetime

def validate_admin_key(x_admin_key: str = Header(None)):
    """Validate admin API key"""
    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key. Admin access required."
        )
    return True

@router.post("/submit-vulnerability", response_model=VulnerabilityAnalysisResponse)
async def submit_vulnerability(
    submission: VulnerabilitySubmission,
    background_tasks: BackgroundTasks,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Submit a new vulnerability for AI analysis and processing
    """
    validate_admin_key(x_admin_key)
    
    logger.info(f"Admin vulnerability submission received: {submission.title}")
    
    # Generate vulnerability ID
    vulnerability_id = f"ADMIN-{uuid.uuid4().hex[:8].upper()}"
    
    # Prepare data for AI analysis
    vulnerability_data = {
        "title": submission.title,
        "description": submission.description,
        "cve_id": submission.cve_id,
        "references": submission.references,
        "additional_context": submission.additional_context
    }
    
    # Run AI analysis
    analyzer = AIVulnerabilityAnalyzer()
    try:
        analysis = await analyzer.analyze_vulnerability(vulnerability_data)
        
        # Create vulnerability record
        vulnerability = Vulnerability(
            vulnerability_id=vulnerability_id,
            cve_id=submission.cve_id,
            title=analysis.enhanced_title,
            description=analysis.enhanced_description,
            severity=SeverityEnum(analysis.severity),
            cvss_score=analysis.cvss_score,
            patch_status=PatchStatusEnum(analysis.patch_status),
            attack_vectors=analysis.attack_vectors,
            technical_details=analysis.technical_details,
            references=submission.references,
            source="ADMIN_SUBMISSION",
            confidence_score=analysis.confidence_score,
            discovery_date=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            first_seen_timestamp=datetime.utcnow(),
            last_updated_timestamp=datetime.utcnow(),
            kirin_remediation_available=True,  # Admin submissions get priority
            auto_remediation_possible=analysis.severity in ["HIGH", "CRITICAL"]
        )
        
        # Link to affected AI tools
        for tool_name in analysis.affected_tools:
            tool = db.query(AITool).filter(AITool.name == tool_name).first()
            if tool:
                vulnerability.affected_tools.append(tool)
            else:
                # Create new tool if not exists
                new_tool = AITool(
                    name=tool_name,
                    description=f"AI tool identified through admin submission",
                    category="ai_assistant",
                    vendor="Unknown"
                )
                db.add(new_tool)
                db.flush()
                vulnerability.affected_tools.append(new_tool)
        
        # Save to database
        db.add(vulnerability)
        db.commit()
        
        logger.info(f"Admin vulnerability saved: {vulnerability_id} - {analysis.severity}")
        
        # Prepare response
        analysis_response = VulnerabilityAnalysisResponse(
            vulnerability_id=vulnerability_id,
            analysis={
                "severity": analysis.severity,
                "cvss_score": analysis.cvss_score,
                "attack_vectors": analysis.attack_vectors,
                "affected_tools": analysis.affected_tools,
                "risk_assessment": analysis.risk_assessment,
                "ai_analysis_notes": analysis.ai_analysis_notes
            },
            ai_enhanced_data={
                "enhanced_title": analysis.enhanced_title,
                "enhanced_description": analysis.enhanced_description,
                "technical_details": analysis.technical_details,
                "remediation_suggestions": analysis.remediation_suggestions,
                "patch_status": analysis.patch_status
            },
            confidence_score=analysis.confidence_score,
            processing_status="completed",
            created_at=vulnerability.created_at
        )
        
        # Send real-time notification
        background_tasks.add_task(
            notify_new_vulnerability,
            vulnerability_id,
            analysis.severity,
            analysis.affected_tools
        )
        
        # Trigger WordPress blog post creation
        background_tasks.add_task(
            create_wordpress_blog_post,
            vulnerability,
            analysis,
            submission.reporter_name,
            submission.reporter_email
        )
        
        return analysis_response
        
    except Exception as e:
        logger.error(f"Error processing admin vulnerability submission: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process vulnerability submission: {str(e)}"
        )

@router.get("/vulnerabilities", response_model=List[VulnerabilityResponse])
async def list_admin_vulnerabilities(
    skip: int = 0,
    limit: int = 50,
    source: Optional[str] = "ADMIN_SUBMISSION",
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: List vulnerabilities with admin filtering options
    """
    validate_admin_key(x_admin_key)
    
    query = db.query(Vulnerability)
    
    if source:
        query = query.filter(Vulnerability.source == source)
    
    vulnerabilities = query.offset(skip).limit(limit).all()
    
    return [vuln.to_dict() for vuln in vulnerabilities]

@router.post("/reanalyze-vulnerability/{vulnerability_id}")
async def reanalyze_vulnerability(
    vulnerability_id: str,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Re-run AI analysis on existing vulnerability
    """
    validate_admin_key(x_admin_key)
    
    vulnerability = db.query(Vulnerability).filter(
        Vulnerability.vulnerability_id == vulnerability_id
    ).first()
    
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Prepare data for re-analysis
    vulnerability_data = {
        "title": vulnerability.title,
        "description": vulnerability.description,
        "cve_id": vulnerability.cve_id,
        "references": vulnerability.references or []
    }
    
    # Run AI analysis
    analyzer = AIVulnerabilityAnalyzer()
    analysis = await analyzer.analyze_vulnerability(vulnerability_data)
    
    # Update vulnerability with new analysis
    vulnerability.title = analysis.enhanced_title
    vulnerability.description = analysis.enhanced_description
    vulnerability.severity = SeverityEnum(analysis.severity)
    vulnerability.cvss_score = analysis.cvss_score
    vulnerability.attack_vectors = analysis.attack_vectors
    vulnerability.technical_details = analysis.technical_details
    vulnerability.confidence_score = analysis.confidence_score
    vulnerability.updated_at = datetime.utcnow()
    vulnerability.last_updated_timestamp = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Re-analyzed vulnerability: {vulnerability_id}")
    
    return {
        "vulnerability_id": vulnerability_id,
        "status": "reanalyzed",
        "new_severity": analysis.severity,
        "confidence_score": analysis.confidence_score,
        "analysis_notes": analysis.ai_analysis_notes
    }

@router.delete("/vulnerability/{vulnerability_id}")
async def delete_vulnerability(
    vulnerability_id: str,
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Delete a vulnerability
    """
    validate_admin_key(x_admin_key)
    
    vulnerability = db.query(Vulnerability).filter(
        Vulnerability.vulnerability_id == vulnerability_id
    ).first()
    
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    db.delete(vulnerability)
    db.commit()
    
    logger.info(f"Admin deleted vulnerability: {vulnerability_id}")
    
    return {"status": "deleted", "vulnerability_id": vulnerability_id}

@router.get("/stats/admin")
async def admin_stats(
    x_admin_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Extended vulnerability statistics
    """
    validate_admin_key(x_admin_key)
    
    # Basic stats
    total_vulnerabilities = db.query(Vulnerability).count()
    admin_submitted = db.query(Vulnerability).filter(
        Vulnerability.source == "ADMIN_SUBMISSION"
    ).count()
    
    # Recent activity (last 24 hours)
    recent_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    recent_vulnerabilities = db.query(Vulnerability).filter(
        Vulnerability.created_at >= recent_date
    ).count()
    
    # Confidence distribution
    high_confidence = db.query(Vulnerability).filter(
        Vulnerability.confidence_score >= 0.8
    ).count()
    
    medium_confidence = db.query(Vulnerability).filter(
        Vulnerability.confidence_score >= 0.6,
        Vulnerability.confidence_score < 0.8
    ).count()
    
    low_confidence = db.query(Vulnerability).filter(
        Vulnerability.confidence_score < 0.6
    ).count()
    
    return {
        "total_vulnerabilities": total_vulnerabilities,
        "admin_submitted": admin_submitted,
        "recent_24h": recent_vulnerabilities,
        "confidence_distribution": {
            "high": high_confidence,
            "medium": medium_confidence,
            "low": low_confidence
        },
        "analysis_engine": "Knostic AI v1.0",
        "last_updated": datetime.utcnow().isoformat()
    }

async def notify_new_vulnerability(vulnerability_id: str, severity: str, affected_tools: List[str]):
    """Send real-time notification about new vulnerability"""
    try:
        message = {
            "type": "vulnerability_submitted",
            "data": {
                "vulnerability_id": vulnerability_id,
                "severity": severity,
                "affected_tools": affected_tools,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "admin_submission"
            }
        }
        
        await websocket_manager.broadcast_to_channel(message, "vulnerabilities")
        logger.info(f"WebSocket notification sent for {vulnerability_id}")
        
    except Exception as e:
        logger.error(f"Failed to send WebSocket notification: {e}")

async def create_wordpress_blog_post(
    vulnerability: Vulnerability, 
    analysis: VulnerabilityAnalysis,
    reporter_name: Optional[str],
    reporter_email: Optional[str]
):
    """Create WordPress blog post for new vulnerability"""
    try:
        logger.info(f"Creating WordPress blog post for {vulnerability.vulnerability_id}")
        
        # Generate WordPress-ready content
        post_title = f"{vulnerability.cve_id or vulnerability.vulnerability_id}: {analysis.severity} Vulnerability in {', '.join(analysis.affected_tools)}"
        
        # Create WordPress-compatible blog post content
        # Build content sections as separate strings for better control
        vulnerability_overview = f"""<h3>📋 Vulnerability Overview</h3>
<ul>
<li><strong>CVE ID:</strong> {vulnerability.cve_id or 'Pending Assignment'}</li>
<li><strong>Vulnerability ID:</strong> {vulnerability.vulnerability_id}</li>
<li><strong>Severity:</strong> {analysis.severity} (CVSS {analysis.cvss_score}/10)</li>
<li><strong>Discovery Date:</strong> {vulnerability.discovery_date.strftime('%B %d, %Y') if vulnerability.discovery_date else 'Unknown'}</li>
<li><strong>Patch Status:</strong> {analysis.patch_status.replace('_', ' ').title()}</li>
</ul>"""

        description_section = f"""<h3>🔍 Description</h3>
<p>{analysis.enhanced_description}</p>"""

        impact_section = f"""<h3>⚠️ Impact Assessment</h3>
<p>{analysis.risk_assessment}</p>

<h4>Attack Vectors:</h4>
<ul>
{"".join(f"<li><strong>{vector.replace('_', ' ').title()}</strong></li>" for vector in analysis.attack_vectors)}
</ul>"""

        affected_tools_section = ""
        if analysis.affected_tools:
            affected_tools_section = f"""<h3>🛠️ Affected AI Tools</h3>
<ul>
{"".join(f"<li><strong>{tool.replace('_', ' ').title()}</strong></li>" for tool in analysis.affected_tools)}
</ul>"""

        technical_details_section = f"""<h3>🔬 Technical Details</h3>
<p>{analysis.technical_details}</p>"""

        remediation_section = f"""<h3>🛡️ Remediation Recommendations</h3>
<ol>
{"".join(f"<li>{suggestion}</li>" for suggestion in analysis.remediation_suggestions)}
</ol>"""

        kirin_plugin_section = ""
        if vulnerability.kirin_remediation_available:
            kirin_plugin_section = f"""<h3>🔧 Kirin Plugin Available</h3>
<p><strong>Good News!</strong> This vulnerability can be automatically remediated using the Kirin security plugin for supported AI development environments.</p>"""

        references_section = ""
        if vulnerability.references:
            references_section = f"""<h3>📚 References</h3>
<ul>
{"".join(f"<li><a href='{ref}' target='_blank' rel='noopener'>{ref}</a></li>" for ref in vulnerability.references)}
</ul>"""

        footer_section = f"""<p><strong>AI Analysis Confidence:</strong> {analysis.confidence_score * 100:.0f}%</p>
{f"<p><strong>Reporter:</strong> {reporter_name}</p>" if reporter_name else ""}
<p><em>This analysis was generated by <strong>Knostic AI's Kirin Vulnerability Database</strong>. For the most up-to-date information, visit our <a href='http://localhost:8080/api/vulnerabilities/{vulnerability.vulnerability_id}'>vulnerability database</a>.</em></p>"""

        # Combine all sections with proper WordPress formatting
        post_content = f"""<p><strong>{analysis.severity} SEVERITY</strong> | <strong>CVSS {analysis.cvss_score}/10</strong> | <strong>{analysis.patch_status.upper()}</strong></p>

{vulnerability_overview}

{description_section}

{impact_section}

{affected_tools_section}

{technical_details_section}

{remediation_section}

{kirin_plugin_section}

{references_section}

<hr>

{footer_section}"""
        
        # Get enhanced content for metadata
        enhanced_content = await llm_enhancer.enhance_vulnerability(vulnerability)
        
        # Use enhanced title if available
        final_title = enhanced_content.get("enhanced_title", post_title)
        
        # Create WordPress post data structure
        wordpress_post = {
            "post_id": f"kirin-{vulnerability.vulnerability_id.lower()}",
            "title": final_title,
            "content": post_content,
            "slug": enhanced_content.get("slug", create_slug(final_title)),
            "meta_description": enhanced_content.get("meta_description", f"{final_title} - AI security vulnerability analysis"),
            "categories": ["Security", "Vulnerability", "AI Tools", analysis.severity],
            "tags": analysis.affected_tools + analysis.attack_vectors + [analysis.patch_status],
            "status": "draft",  # Start as draft for review
            "author": "Kirin VulnDB",
            "excerpt": enhanced_content.get("meta_description", f"{final_title}..."),
            "custom_fields": {
                "vulnerability_id": vulnerability.vulnerability_id,
                "cve_id": vulnerability.cve_id,
                "severity": analysis.severity,
                "cvss_score": analysis.cvss_score,
                "confidence_score": analysis.confidence_score,
                "affected_tools": ",".join(analysis.affected_tools),
                "attack_vectors": ",".join(analysis.attack_vectors),
                "discovery_date": vulnerability.discovery_date.isoformat() if vulnerability.discovery_date else None,
                "kirin_auto_post": True
            }
        }
        
        # In a real implementation, this would POST to WordPress REST API
        # For now, we'll create a webhook payload that WordPress can consume
        webhook_payload = {
            "event": "vulnerability_blog_post",
            "data": wordpress_post,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "kirin_vulndb"
        }
        
        # Store the blog post data for webhook delivery
        # This could be sent to WordPress via webhook or saved for RSS consumption
        logger.info(f"WordPress blog post created: {post_title}")
        logger.info(f"Post categories: {wordpress_post['categories']}")
        logger.info(f"Post tags: {wordpress_post['tags']}")
        
        # Send webhook to WordPress site
        from app.api.wordpress import send_wordpress_webhook
        await send_wordpress_webhook(webhook_payload, "default")
        
    except Exception as e:
        logger.error(f"Failed to create WordPress blog post: {e}")