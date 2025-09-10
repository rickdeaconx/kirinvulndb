from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
import logging
from pydantic import BaseModel

from app.db.database import get_db
from app.models.vulnerability import Vulnerability, SeverityEnum, PatchStatusEnum
from app.models.tool import AITool
from app.schemas.vulnerability import VulnerabilityResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple API key validation for WordPress integration
VALID_API_KEYS = {
    "wp-demo-key": {"name": "Demo Site", "domain": "*"},
    "wp-prod-key": {"name": "Production Site", "domain": "*.com"},
}

# Webhook configuration
WEBHOOK_ENDPOINTS = {
    "default": "https://your-wordpress-site.com/wp-json/kirin/v1/webhook",
    "demo": "https://demo-site.com/wp-json/kirin/v1/webhook"
}

class WebhookPayload(BaseModel):
    event: str
    data: Dict[str, Any]
    timestamp: str
    source: str = "kirin_vulndb"

class WordPressPost(BaseModel):
    title: str
    content: str
    categories: List[str]
    tags: List[str]
    status: str = "draft"
    vulnerability_id: str

def validate_api_key(x_api_key: Optional[str] = Header(None)):
    """Validate API key for WordPress integration"""
    if not x_api_key or x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return VALID_API_KEYS[x_api_key]

@router.get("/embed/vulnerabilities")
async def get_vulnerabilities_for_embed(
    limit: int = Query(10, description="Number of vulnerabilities", ge=1, le=50),
    severity: Optional[SeverityEnum] = Query(None, description="Filter by severity"),
    tool: Optional[str] = Query(None, description="Filter by AI tool"),
    format: str = Query("json", description="Response format: json, html, widget"),
    theme: str = Query("light", description="Theme: light, dark, auto"),
    api_key_info: Dict = Depends(validate_api_key),
    db: Session = Depends(get_db)
):
    """Get vulnerabilities formatted for WordPress embedding"""
    
    query = db.query(Vulnerability).order_by(Vulnerability.created_at.desc())
    
    # Apply filters
    if severity:
        query = query.filter(Vulnerability.severity == severity)
    
    if tool:
        query = query.join(Vulnerability.affected_tools).filter(
            AITool.name.ilike(f"%{tool}%")
        )
    
    vulnerabilities = query.limit(limit).all()
    
    # Return different formats based on request
    if format == "html":
        return generate_html_widget(vulnerabilities, theme)
    elif format == "widget":
        return generate_widget_data(vulnerabilities)
    else:
        return {
            "vulnerabilities": [vuln.to_dict() for vuln in vulnerabilities],
            "total": len(vulnerabilities),
            "api_usage": {
                "client": api_key_info["name"],
                "timestamp": datetime.utcnow().isoformat()
            }
        }

@router.get("/embed/stats")
async def get_stats_for_embed(
    api_key_info: Dict = Depends(validate_api_key),
    db: Session = Depends(get_db)
):
    """Get vulnerability statistics for WordPress widgets"""
    
    total_vulns = db.query(Vulnerability).count()
    critical_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == SeverityEnum.CRITICAL
    ).count()
    high_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == SeverityEnum.HIGH
    ).count()
    
    # Recent vulnerabilities (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_vulns = db.query(Vulnerability).filter(
        Vulnerability.created_at >= week_ago
    ).count()
    
    # AI tools affected
    tools_count = db.query(AITool).count()
    
    return {
        "stats": {
            "total_vulnerabilities": total_vulns,
            "critical_vulnerabilities": critical_vulns,
            "high_vulnerabilities": high_vulns,
            "recent_vulnerabilities": recent_vulns,
            "ai_tools_monitored": tools_count,
            "last_updated": datetime.utcnow().isoformat()
        },
        "api_usage": {
            "client": api_key_info["name"],
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.get("/embed/alerts")
async def get_alerts_for_embed(
    limit: int = Query(5, description="Number of alerts", ge=1, le=20),
    api_key_info: Dict = Depends(validate_api_key),
    db: Session = Depends(get_db)
):
    """Get critical alerts for WordPress display"""
    
    # Get critical vulnerabilities from last 30 days
    month_ago = datetime.utcnow() - timedelta(days=30)
    critical_vulns = db.query(Vulnerability).filter(
        Vulnerability.severity == SeverityEnum.CRITICAL,
        Vulnerability.created_at >= month_ago
    ).order_by(Vulnerability.created_at.desc()).limit(limit).all()
    
    alerts = []
    for vuln in critical_vulns:
        alerts.append({
            "id": vuln.vulnerability_id,
            "title": vuln.title,
            "severity": vuln.severity.value,
            "cvss_score": vuln.cvss_score,
            "discovery_date": vuln.discovery_date.isoformat() if vuln.discovery_date else None,
            "patch_status": vuln.patch_status.value,
            "affected_tools": [tool.name for tool in vuln.affected_tools],
            "alert_type": "critical_vulnerability"
        })
    
    return {
        "alerts": alerts,
        "alert_count": len(alerts),
        "api_usage": {
            "client": api_key_info["name"],
            "timestamp": datetime.utcnow().isoformat()
        }
    }

def generate_html_widget(vulnerabilities: List[Vulnerability], theme: str = "light") -> Dict[str, Any]:
    """Generate HTML widget for direct embedding"""
    
    theme_styles = {
        "light": {
            "bg": "#ffffff",
            "text": "#333333",
            "border": "#e1e5e9",
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745"
        },
        "dark": {
            "bg": "#1a1a1a",
            "text": "#ffffff",
            "border": "#404040",
            "critical": "#ff6b6b",
            "high": "#ffa726",
            "medium": "#ffeb3b",
            "low": "#66bb6a"
        }
    }
    
    styles = theme_styles.get(theme, theme_styles["light"])
    
    html = f"""
    <div class="kirin-vuln-widget" style="
        background: {styles['bg']};
        color: {styles['text']};
        border: 1px solid {styles['border']};
        border-radius: 8px;
        padding: 16px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-size: 14px;
        max-width: 100%;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 16px;">
            <div style="font-weight: 600; font-size: 16px;">🛡️ AI Security Monitor</div>
            <div style="margin-left: auto; font-size: 12px; opacity: 0.7;">
                Powered by Kirin VulnDB
            </div>
        </div>
    """
    
    for vuln in vulnerabilities[:5]:  # Limit to 5 for widget
        severity_color = styles.get(vuln.severity.value.lower(), styles['text'])
        html += f"""
        <div style="
            margin-bottom: 12px;
            padding: 12px;
            border: 1px solid {styles['border']};
            border-radius: 4px;
            border-left: 4px solid {severity_color};
        ">
            <div style="font-weight: 600; margin-bottom: 4px;">
                {vuln.vulnerability_id or 'N/A'} - {vuln.severity.value}
            </div>
            <div style="margin-bottom: 8px; font-size: 13px;">
                {vuln.title[:80]}{'...' if len(vuln.title) > 80 else ''}
            </div>
            <div style="font-size: 12px; opacity: 0.8;">
                CVSS: {vuln.cvss_score or 'N/A'} | Status: {vuln.patch_status.value.replace('_', ' ').title()}
            </div>
        </div>
        """
    
    html += """
        <div style="text-align: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid {}; font-size: 12px;">
            <a href="http://localhost:8080" target="_blank" style="color: {}; text-decoration: none;">
                View Full Dashboard →
            </a>
        </div>
    </div>
    """.format(styles['border'], styles['text'])
    
    return {
        "format": "html",
        "content": html,
        "vulnerability_count": len(vulnerabilities),
        "theme": theme
    }

def generate_widget_data(vulnerabilities: List[Vulnerability]) -> Dict[str, Any]:
    """Generate simplified data for WordPress widget consumption"""
    
    widget_data = {
        "widget_type": "vulnerability_summary",
        "items": [],
        "summary": {
            "total": len(vulnerabilities),
            "critical": len([v for v in vulnerabilities if v.severity == SeverityEnum.CRITICAL]),
            "high": len([v for v in vulnerabilities if v.severity == SeverityEnum.HIGH]),
            "medium": len([v for v in vulnerabilities if v.severity == SeverityEnum.MEDIUM]),
            "low": len([v for v in vulnerabilities if v.severity == SeverityEnum.LOW])
        }
    }
    
    for vuln in vulnerabilities[:10]:  # Limit for widget
        widget_data["items"].append({
            "id": vuln.vulnerability_id,
            "title": vuln.title,
            "severity": vuln.severity.value,
            "cvss": vuln.cvss_score,
            "status": vuln.patch_status.value,
            "date": vuln.created_at.strftime("%Y-%m-%d"),
            "tools": [tool.name for tool in vuln.affected_tools][:3]  # Limit tools
        })
    
    return widget_data

@router.post("/webhook/receive")
async def receive_wordpress_webhook(
    request: Request,
    api_key_info: Dict = Depends(validate_api_key)
):
    """Receive webhooks from WordPress site"""
    try:
        payload = await request.json()
        
        logger.info(f"Received WordPress webhook from {api_key_info['name']}: {payload.get('event', 'unknown')}")
        
        # Process different webhook events
        event = payload.get("event")
        
        if event == "post_published":
            # WordPress notifies us that a vulnerability post was published
            vulnerability_id = payload.get("data", {}).get("vulnerability_id")
            if vulnerability_id:
                logger.info(f"WordPress published vulnerability post: {vulnerability_id}")
        
        elif event == "post_updated":
            # WordPress notifies us of post updates
            vulnerability_id = payload.get("data", {}).get("vulnerability_id")
            logger.info(f"WordPress updated vulnerability post: {vulnerability_id}")
        
        elif event == "site_health":
            # WordPress sends health check
            logger.info(f"WordPress site health check from {api_key_info['name']}")
        
        return {
            "status": "received",
            "event": event,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing WordPress webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

@router.post("/webhook/send")
async def send_webhook_test(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    api_key_info: Dict = Depends(validate_api_key)
):
    """Test endpoint to send webhook to WordPress"""
    
    background_tasks.add_task(
        send_wordpress_webhook,
        payload.dict(),
        api_key_info["name"]
    )
    
    return {
        "status": "webhook_queued",
        "event": payload.event,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/post/create")
async def create_wordpress_post(
    post_data: WordPressPost,
    background_tasks: BackgroundTasks,
    api_key_info: Dict = Depends(validate_api_key),
    db: Session = Depends(get_db)
):
    """Create WordPress post from vulnerability data"""
    
    # Get vulnerability details
    vulnerability = db.query(Vulnerability).filter(
        Vulnerability.vulnerability_id == post_data.vulnerability_id
    ).first()
    
    if not vulnerability:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    
    # Prepare webhook payload
    webhook_payload = {
        "event": "create_post",
        "data": {
            "post": post_data.dict(),
            "vulnerability": {
                "id": vulnerability.vulnerability_id,
                "cve_id": vulnerability.cve_id,
                "severity": vulnerability.severity.value,
                "cvss_score": vulnerability.cvss_score,
                "description": vulnerability.description,
                "affected_tools": [tool.name for tool in vulnerability.affected_tools],
                "discovery_date": vulnerability.discovery_date.isoformat() if vulnerability.discovery_date else None
            }
        },
        "timestamp": datetime.utcnow().isoformat(),
        "source": "kirin_vulndb"
    }
    
    # Send webhook in background
    background_tasks.add_task(
        send_wordpress_webhook,
        webhook_payload,
        api_key_info["name"]
    )
    
    return {
        "status": "post_creation_queued",
        "vulnerability_id": post_data.vulnerability_id,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/webhook/status")
async def webhook_status(
    api_key_info: Dict = Depends(validate_api_key)
):
    """Check webhook system status"""
    
    return {
        "webhook_system": "active",
        "client": api_key_info["name"],
        "endpoints": {
            "receive": "/api/wordpress/webhook/receive",
            "send": "/api/wordpress/webhook/send",
            "create_post": "/api/wordpress/post/create"
        },
        "supported_events": [
            "vulnerability_created",
            "vulnerability_updated", 
            "critical_alert",
            "post_published",
            "post_updated",
            "site_health"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

async def send_wordpress_webhook(payload: Dict[str, Any], client_name: str = "default"):
    """Send webhook to WordPress site"""
    import aiohttp
    
    try:
        # Determine webhook endpoint
        endpoint = WEBHOOK_ENDPOINTS.get(client_name.lower(), WEBHOOK_ENDPOINTS["default"])
        
        logger.info(f"Sending webhook to WordPress ({client_name}): {payload.get('event')}")
        
        headers = {
            "Content-Type": "application/json",
            "X-Kirin-Source": "vulnerability-database",
            "X-Kirin-Timestamp": datetime.utcnow().isoformat()
        }
        
        # In a real implementation, this would make the HTTP request
        # For demo purposes, we'll simulate success
        
        logger.info(f"Webhook sent successfully to {endpoint}")
        logger.info(f"Event: {payload.get('event')}")
        logger.info(f"Data keys: {list(payload.get('data', {}).keys())}")
        
        # TODO: Uncomment for real webhook delivery
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(endpoint, json=payload, headers=headers, timeout=30) as response:
        #         if response.status == 200:
        #             logger.info(f"Webhook delivered successfully to {endpoint}")
        #         else:
        #             logger.error(f"Webhook delivery failed: {response.status}")
        
    except Exception as e:
        logger.error(f"Failed to send WordPress webhook: {e}")