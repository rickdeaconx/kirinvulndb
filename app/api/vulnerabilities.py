from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.db.database import get_db
from app.models.vulnerability import Vulnerability, SeverityEnum, PatchStatusEnum
from app.models.tool import AITool
from app.schemas.vulnerability import (
    VulnerabilityResponse, 
    VulnerabilityCreate, 
    VulnerabilityUpdate,
    VulnerabilityList
)
from app.services.vulnerability_service import VulnerabilityService
from app.utils.pagination import paginate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/latest", response_model=VulnerabilityList)
async def get_latest_vulnerabilities(
    hours: int = Query(24, description="Hours to look back", ge=1, le=168),
    severity: Optional[SeverityEnum] = Query(None, description="Filter by severity"),
    tool: Optional[str] = Query(None, description="Filter by AI tool name"),
    limit: int = Query(50, description="Number of results", ge=1, le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    db: Session = Depends(get_db)
):
    """Get latest vulnerabilities within specified time window"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # STRICT AI-ONLY FILTERING - Cursor prioritized as primary AI IDE
    ai_keywords = [
        # Cursor gets TOP priority - our main AI IDE
        "cursor", "cursor ide", "cursor.sh", "cursor editor", "cursor ai",
        "copilot", "tabnine", "codeium", "ai", "artificial intelligence",
        "machine learning", "code completion", "code generation", "llm", 
        "large language model", "prompt injection", "neural", "transformer"
    ]
    
    ai_filter = or_(
        # Has AI tools associated
        Vulnerability.affected_tools.any(),
        # Or description contains AI keywords
        or_(*[Vulnerability.description.ilike(f"%{keyword}%") for keyword in ai_keywords]),
        # Or title contains AI keywords
        or_(*[Vulnerability.title.ilike(f"%{keyword}%") for keyword in ai_keywords]),
        # Or source is admin (manually curated)
        Vulnerability.source == "ADMIN_SUBMISSION"
    )
    
    query = db.query(Vulnerability).filter(
        Vulnerability.created_at >= cutoff_time,
        ai_filter
    )
    
    # Apply filters
    if severity:
        query = query.filter(Vulnerability.severity == severity)
    
    if tool:
        query = query.join(Vulnerability.affected_tools).filter(
            AITool.name == tool
        )
    
    # Order by creation time (newest first)
    query = query.order_by(Vulnerability.created_at.desc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    vulnerabilities = query.offset(offset).limit(limit).all()
    
    return VulnerabilityList(
        vulnerabilities=[vuln.to_dict() for vuln in vulnerabilities],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/critical", response_model=VulnerabilityList)
async def get_critical_vulnerabilities(
    unpatched_only: bool = Query(False, description="Only show unpatched vulnerabilities"),
    limit: int = Query(100, description="Number of results", ge=1, le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    db: Session = Depends(get_db)
):
    """Get critical severity vulnerabilities requiring immediate attention"""
    
    query = db.query(Vulnerability).filter(
        Vulnerability.severity == SeverityEnum.CRITICAL
    )
    
    if unpatched_only:
        query = query.filter(
            Vulnerability.patch_status == PatchStatusEnum.UNPATCHED
        )
    
    # Order by discovery date (newest first)
    query = query.order_by(Vulnerability.discovery_date.desc())
    
    total = query.count()
    vulnerabilities = query.offset(offset).limit(limit).all()
    
    return VulnerabilityList(
        vulnerabilities=[vuln.to_dict() for vuln in vulnerabilities],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/by-tool/{tool_name}", response_model=VulnerabilityList)
async def get_vulnerabilities_by_tool(
    tool_name: str = Path(..., description="AI tool name"),
    severity: Optional[SeverityEnum] = Query(None, description="Filter by severity"),
    patch_status: Optional[PatchStatusEnum] = Query(None, description="Filter by patch status"),
    limit: int = Query(50, description="Number of results", ge=1, le=1000),
    offset: int = Query(0, description="Offset for pagination", ge=0),
    db: Session = Depends(get_db)
):
    """Get vulnerabilities for a specific AI tool"""
    
    # Check if tool exists
    tool = db.query(AITool).filter(AITool.name == tool_name).first()
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    query = db.query(Vulnerability).join(Vulnerability.affected_tools).filter(
        AITool.name == tool_name
    )
    
    # Apply filters
    if severity:
        query = query.filter(Vulnerability.severity == severity)
    
    if patch_status:
        query = query.filter(Vulnerability.patch_status == patch_status)
    
    query = query.order_by(Vulnerability.discovery_date.desc())
    
    total = query.count()
    vulnerabilities = query.offset(offset).limit(limit).all()
    
    return VulnerabilityList(
        vulnerabilities=[vuln.to_dict() for vuln in vulnerabilities],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/search")
async def search_vulnerabilities(
    q: str = Query(..., description="Search query", min_length=2),
    severity: Optional[SeverityEnum] = Query(None),
    tool: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Full-text search across vulnerabilities"""
    
    # Basic text search (can be enhanced with Elasticsearch later)
    query = db.query(Vulnerability).filter(
        Vulnerability.title.ilike(f"%{q}%") |
        Vulnerability.description.ilike(f"%{q}%") |
        Vulnerability.vulnerability_id.ilike(f"%{q}%") |
        Vulnerability.cve_id.ilike(f"%{q}%")
    )
    
    if severity:
        query = query.filter(Vulnerability.severity == severity)
        
    if tool:
        query = query.join(Vulnerability.affected_tools).filter(
            AITool.name == tool
        )
    
    query = query.order_by(Vulnerability.discovery_date.desc())
    
    total = query.count()
    vulnerabilities = query.offset(offset).limit(limit).all()
    
    return {
        "vulnerabilities": [vuln.to_dict() for vuln in vulnerabilities],
        "total": total,
        "limit": limit,
        "offset": offset,
        "query": q
    }


@router.get("/trending")
async def get_trending_vulnerabilities(
    days: int = Query(7, description="Days to analyze for trends", ge=1, le=30),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get trending vulnerabilities based on recent activity"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get vulnerabilities with high activity (new discoveries, updates)
    vulnerabilities = db.query(Vulnerability).filter(
        Vulnerability.created_at >= cutoff_date
    ).order_by(
        Vulnerability.created_at.desc(),
        Vulnerability.severity.desc()
    ).limit(limit).all()
    
    return {
        "trending_vulnerabilities": [vuln.to_dict() for vuln in vulnerabilities],
        "period_days": days,
        "count": len(vulnerabilities)
    }


@router.get("/stats")
async def get_vulnerability_statistics(
    days: int = Query(30, description="Days to analyze", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get vulnerability statistics and metrics"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total counts
    total_vulnerabilities = db.query(Vulnerability).count()
    recent_vulnerabilities = db.query(Vulnerability).filter(
        Vulnerability.created_at >= cutoff_date
    ).count()
    
    # Severity breakdown
    severity_counts = {}
    for severity in SeverityEnum:
        count = db.query(Vulnerability).filter(
            Vulnerability.severity == severity,
            Vulnerability.created_at >= cutoff_date
        ).count()
        severity_counts[severity.value] = count
    
    # Patch status breakdown
    patch_counts = {}
    for status in PatchStatusEnum:
        count = db.query(Vulnerability).filter(
            Vulnerability.patch_status == status,
            Vulnerability.created_at >= cutoff_date
        ).count()
        patch_counts[status.value] = count
    
    # Tool breakdown
    tool_counts = {}
    tools = db.query(AITool).all()
    for tool in tools:
        count = db.query(Vulnerability).join(Vulnerability.affected_tools).filter(
            AITool.id == tool.id,
            Vulnerability.created_at >= cutoff_date
        ).count()
        tool_counts[tool.name] = count
    
    return {
        "period_days": days,
        "total_vulnerabilities": total_vulnerabilities,
        "recent_vulnerabilities": recent_vulnerabilities,
        "severity_distribution": severity_counts,
        "patch_status_distribution": patch_counts,
        "tool_distribution": tool_counts,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def get_vulnerability_by_id(
    vulnerability_id: str = Path(..., description="Vulnerability ID"),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific vulnerability"""
    
    vulnerability = db.query(Vulnerability).filter(
        Vulnerability.vulnerability_id == vulnerability_id
    ).first()
    
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    return VulnerabilityResponse(**vulnerability.to_dict())


@router.post("/", response_model=VulnerabilityResponse)
async def create_vulnerability(
    vulnerability_data: VulnerabilityCreate,
    db: Session = Depends(get_db)
):
    """Create a new vulnerability entry"""
    
    service = VulnerabilityService(db)
    try:
        vulnerability = service.create_vulnerability(vulnerability_data)
        logger.info(f"Created vulnerability: {vulnerability.vulnerability_id}")
        return VulnerabilityResponse(**vulnerability.to_dict())
    except Exception as e:
        logger.error(f"Error creating vulnerability: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{vulnerability_id}", response_model=VulnerabilityResponse)
async def update_vulnerability(
    vulnerability_id: str,
    vulnerability_data: VulnerabilityUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing vulnerability"""
    
    service = VulnerabilityService(db)
    try:
        vulnerability = service.update_vulnerability(vulnerability_id, vulnerability_data)
        if not vulnerability:
            raise HTTPException(status_code=404, detail="Vulnerability not found")
        
        logger.info(f"Updated vulnerability: {vulnerability_id}")
        return VulnerabilityResponse(**vulnerability.to_dict())
    except Exception as e:
        logger.error(f"Error updating vulnerability {vulnerability_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))