"""
Vulnerability monitoring API endpoints
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from datetime import datetime
from typing import Dict, Any
import asyncio
import logging

from app.services.vulnerability_monitor import VulnerabilityMonitor
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/scan/manual")
async def trigger_manual_scan(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Manually trigger a vulnerability scan"""
    
    async def run_scan():
        """Run the scan in background"""
        try:
            async with VulnerabilityMonitor() as monitor:
                stats = await monitor.run_discovery_cycle()
                logger.info(f"Manual scan completed: {stats}")
        except Exception as e:
            logger.error(f"Manual scan failed: {e}")
    
    # Run scan in background
    background_tasks.add_task(run_scan)
    
    return {
        "message": "Manual vulnerability scan started",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/status")
async def get_monitoring_status() -> Dict[str, Any]:
    """Get current monitoring status"""
    
    from app.db.database import SessionLocal
    from app.models.vulnerability import Vulnerability
    from sqlalchemy import func, desc
    
    with SessionLocal() as db:
        # Get latest scan statistics
        total_vulns = db.query(Vulnerability).count()
        recent_vulns = db.query(Vulnerability).filter(
            Vulnerability.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count()
        
        # Get latest vulnerability
        latest_vuln = db.query(Vulnerability).order_by(desc(Vulnerability.created_at)).first()
        
        # Get source breakdown
        source_stats = db.query(
            Vulnerability.source, 
            func.count(Vulnerability.id)
        ).group_by(Vulnerability.source).all()
    
    return {
        "monitoring_active": True,
        "check_interval": "24 hours",
        "total_vulnerabilities": total_vulns,
        "new_today": recent_vulns,
        "last_vulnerability": {
            "id": latest_vuln.vulnerability_id if latest_vuln else None,
            "title": latest_vuln.title if latest_vuln else None,
            "created_at": latest_vuln.created_at.isoformat() if latest_vuln else None
        } if latest_vuln else None,
        "sources": {source: count for source, count in source_stats},
        "next_scheduled_scan": "Next automatic scan in background",
        "manual_scan_available": True
    }

@router.get("/sources")
async def get_monitoring_sources() -> Dict[str, Any]:
    """Get information about monitoring sources"""
    
    sources = [
        {
            "name": "NVD API",
            "description": "NIST National Vulnerability Database",
            "url": "https://services.nvd.nist.gov/rest/json/cves/2.0",
            "check_interval": "24 hours",
            "keywords": ["copilot", "cursor", "tabnine", "ai assistant"],
            "status": "active"
        },
        {
            "name": "GitHub Security Advisories",
            "description": "GitHub's security advisory database",
            "url": "https://api.github.com/advisories",
            "check_interval": "12 hours", 
            "keywords": ["github", "vscode", "copilot"],
            "status": "active"
        },
        {
            "name": "CISA Cybersecurity Advisories",
            "description": "US-CERT security advisories",
            "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
            "check_interval": "24 hours",
            "keywords": ["ai", "development tools"],
            "status": "active"
        },
        {
            "name": "Vendor Security Blogs",
            "description": "Official security blogs from AI tool vendors",
            "sources": [
                "Microsoft Security",
                "GitHub Security Blog", 
                "JetBrains Security"
            ],
            "check_interval": "24 hours",
            "status": "active"
        }
    ]
    
    return {
        "total_sources": len(sources),
        "sources": sources,
        "monitoring_strategy": "Multi-source aggregation with AI-powered relevance filtering"
    }

@router.get("/config")
async def get_monitoring_config() -> Dict[str, Any]:
    """Get monitoring configuration"""
    
    return {
        "monitoring_enabled": not settings.DEBUG,
        "check_interval": "24 hours",
        "ai_keyword_filtering": True,
        "automatic_classification": True,
        "source_verification": True,
        "keywords": [
            "copilot", "cursor", "tabnine", "codeium", "code completion",
            "ai assistant", "code generation", "jetbrains ai", "codewhisperer"
        ],
        "severity_thresholds": {
            "critical": 9.0,
            "high": 7.0,
            "medium": 4.0,
            "low": 0.0
        },
        "data_retention": "730 days",
        "rate_limiting": "1 second between API calls"
    }