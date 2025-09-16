"""
RSS Feed API for WordPress Integration
Provides vulnerability data as RSS feeds for blog consumption
Copyright © 2025 Rick Deacon, Knostic AI - https://knostic.ai
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import or_ 
from typing import Optional
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from xml.dom import minidom
import html
import logging

from app.db.database import get_db
from app.models.vulnerability import Vulnerability
from app.models.tool import AITool
from app.services.llm_enhancer import llm_enhancer

router = APIRouter()
logger = logging.getLogger(__name__)


def format_rss_date(dt: datetime) -> str:
    """Format datetime for RSS pubDate"""
    return dt.strftime('%a, %d %b %Y %H:%M:%S %z') or dt.strftime('%a, %d %b %Y %H:%M:%S GMT')


async def create_vulnerability_description(vuln: Vulnerability) -> str:
    """Create LLM-enhanced blog-style description for RSS feed"""
    try:
        # Get LLM-enhanced content
        enhanced_content = await llm_enhancer.enhance_vulnerability(vuln)
        
        if enhanced_content.get("blog_format"):
            # Return the enhanced blog-style description
            blog_content = enhanced_content["enhanced_description"]
            
            # Add Knostic Kirin footer
            blog_content += f"""
<hr>
<p><em>This vulnerability intelligence is powered by <strong>Knostic Kirin</strong> - Advanced AI Security Monitoring</em></p>
<p><em>📊 Confidence Score: {vuln.confidence_score}/1.0 | 🔍 Source: {vuln.source}</em></p>
<p><em>🏷️ ID: {vuln.vulnerability_id} | 📅 Discovered: {vuln.discovery_date.strftime('%Y-%m-%d') if vuln.discovery_date else 'Unknown'}</em></p>
"""
            return blog_content
    
    except Exception as e:
        logger.error(f"LLM enhancement failed for {vuln.vulnerability_id}: {e}")
        # Fall back to original format
    
    # Fallback to original format if LLM fails
    description_parts = [
        f"<h2>Kirin Security Alert</h2>",
        f"<p><strong>CVE ID:</strong> {vuln.cve_id or 'N/A'}</p>",
        f"<p><strong>Severity:</strong> {vuln.severity.value} (CVSS: {vuln.cvss_score or 'N/A'})</p>",
        f"<p><strong>Patch Status:</strong> {vuln.patch_status.value}</p>",
        f"<h3>Description</h3>",
        f"<p>{html.escape(vuln.description)}</p>"
    ]
    
    if vuln.attack_vectors:
        vectors = ", ".join(vuln.attack_vectors)
        description_parts.append(f"<p><strong>Attack Vectors:</strong> {vectors}</p>")
    
    if vuln.technical_details:
        description_parts.append(f"<h3>Technical Details</h3>")
        description_parts.append(f"<p>{html.escape(vuln.technical_details)}</p>")
    
    if vuln.affected_tools:
        tools = [tool.display_name for tool in vuln.affected_tools]
        description_parts.append(f"<h3>Affected AI Tools</h3>")
        description_parts.append(f"<p>{', '.join(tools)}</p>")
    
    if vuln.references:
        description_parts.append(f"<h3>References</h3>")
        description_parts.append("<ul>")
        for ref in vuln.references:
            ref_text = ref.title if hasattr(ref, 'title') else str(ref)
            ref_url = ref.url if hasattr(ref, 'url') else str(ref)
            description_parts.append(f"<li><a href='{ref_url}' target='_blank'>{ref_text}</a></li>")
        description_parts.append("</ul>")
    
    description_parts.append(f"<hr>")
    description_parts.append(f"<p><em>Powered by Knostic Kirin - AI Security Intelligence Platform</em></p>")
    
    return "".join(description_parts)


@router.get("/vulnerabilities.xml")
async def vulnerability_rss_feed(
    limit: int = Query(50, description="Maximum number of vulnerabilities", le=200),
    since_days: int = Query(30, description="Get vulnerabilities from last N days", le=365),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    tool: Optional[str] = Query(None, description="Filter by AI tool name"),
    patch_status: Optional[str] = Query(None, description="Filter by patch status"),
    db: Session = Depends(get_db)
):
    """
    Generate RSS feed for vulnerabilities - WordPress compatible
    Perfect for importing into WordPress as blog posts
    """
    logger.info("Generating RSS feed for vulnerabilities")
    
    # Calculate date range
    since_date = datetime.utcnow() - timedelta(days=since_days)
    
    # Build query - ONLY AI-related vulnerabilities
    query = db.query(Vulnerability).filter(
        Vulnerability.discovery_date >= since_date
    )
    
    # STRICT AI FILTERING - Cursor prioritized as primary AI IDE
    ai_keywords_filter = [
        # Cursor gets TOP priority - our primary AI IDE  
        "cursor", "cursor ide", "cursor.sh", "cursor editor", "cursor ai",
        "copilot", "tabnine", "codeium", "ai", "artificial intelligence",
        "machine learning", "code completion", "code generation", "llm", 
        "large language model", "prompt injection", "neural", "transformer"
    ]
    
    # Filter by description containing AI keywords OR having AI tools
    ai_condition = or_(
        # Has AI tools associated
        Vulnerability.affected_tools.any(),
        # Or description contains AI keywords
        or_(*[Vulnerability.description.ilike(f"%{keyword}%") for keyword in ai_keywords_filter]),
        # Or title contains AI keywords  
        or_(*[Vulnerability.title.ilike(f"%{keyword}%") for keyword in ai_keywords_filter]),
        # Or source is admin (manually curated)
        Vulnerability.source == "ADMIN_SUBMISSION"
    )
    
    query = query.filter(ai_condition)
    
    # Apply filters
    if severity:
        from app.models.vulnerability import SeverityEnum
        try:
            severity_enum = SeverityEnum(severity.upper())
            query = query.filter(Vulnerability.severity == severity_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    
    if tool:
        query = query.join(Vulnerability.affected_tools).filter(
            AITool.name.ilike(f"%{tool}%")
        )
    
    if patch_status:
        from app.models.vulnerability import PatchStatusEnum
        try:
            patch_enum = PatchStatusEnum(patch_status.lower())
            query = query.filter(Vulnerability.patch_status == patch_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid patch status: {patch_status}")
    
    # Order and limit
    vulnerabilities = query.order_by(
        Vulnerability.discovery_date.desc()
    ).limit(limit).all()
    
    # Create RSS XML
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    rss.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
    
    channel = ET.SubElement(rss, "channel")
    
    # Channel metadata
    ET.SubElement(channel, "title").text = "Kirin Vulnerability Database - Cursor AI Security Feed"
    ET.SubElement(channel, "link").text = "https://knostic.ai"
    ET.SubElement(channel, "description").text = "Latest Cursor IDE and AI tool vulnerabilities from Kirin VulnDB - Prioritizing Cursor security"
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "managingEditor").text = "rick@knostic.ai (Rick Deacon)"
    ET.SubElement(channel, "webMaster").text = "rick@knostic.ai (Rick Deacon)"
    ET.SubElement(channel, "generator").text = "Kirin VulnDB by Knostic AI"
    ET.SubElement(channel, "lastBuildDate").text = format_rss_date(datetime.utcnow())
    
    # Add items with LLM enhancement
    for vuln in vulnerabilities:
        item = ET.SubElement(channel, "item")
        
        # Enhanced Title using LLM
        try:
            enhanced_content = await llm_enhancer.enhance_vulnerability(vuln)
            title = enhanced_content.get("enhanced_title", f"Kirin Alert: {vuln.title}")
        except Exception as e:
            logger.error(f"Failed to enhance title for {vuln.vulnerability_id}: {e}")
            # Fallback title
            tool_names = [tool.display_name for tool in vuln.affected_tools] if vuln.affected_tools else ["AI Tools"]
            title = f"Kirin Alert: {vuln.severity.value} Vulnerability in {', '.join(tool_names[:3])}"
        
        ET.SubElement(item, "title").text = title
        
        # Link (could point to detailed view)
        ET.SubElement(item, "link").text = f"https://knostic.ai/vulnerability/{vuln.vulnerability_id}"
        
        # Description (LLM-enhanced blog content for WordPress)
        description = await create_vulnerability_description(vuln)
        ET.SubElement(item, "description").text = description
        
        # Content (full HTML content)
        content_elem = ET.SubElement(item, "content:encoded")
        content_elem.text = description
        
        # Publication date
        pub_date = vuln.discovery_date or vuln.created_at
        ET.SubElement(item, "pubDate").text = format_rss_date(pub_date)
        
        # GUID (unique identifier)
        guid_elem = ET.SubElement(item, "guid", isPermaLink="false")
        guid_elem.text = vuln.vulnerability_id
        
        # Categories (tags for WordPress)
        ET.SubElement(item, "category").text = f"Security"
        ET.SubElement(item, "category").text = f"Vulnerability"
        ET.SubElement(item, "category").text = f"{vuln.severity.value}"
        
        for tool in (vuln.affected_tools or []):
            ET.SubElement(item, "category").text = tool.name.replace("_", " ").title()
        
        if vuln.attack_vectors:
            for vector in vuln.attack_vectors:
                ET.SubElement(item, "category").text = vector.replace("_", " ").title()
        
        # Author
        ET.SubElement(item, "dc:creator").text = "Kirin VulnDB"
    
    # Convert to string with pretty printing
    rough_string = ET.tostring(rss, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding=None)
    
    # Remove empty lines
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    final_xml = '\n'.join(lines)
    
    return Response(
        content=final_xml,
        media_type="application/rss+xml",
        headers={
            "Content-Disposition": "inline; filename=vulnerabilities.xml",
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
    )


@router.get("/cursor-vulnerabilities.xml")
async def cursor_vulnerability_rss_feed(
    limit: int = Query(50, description="Maximum number of vulnerabilities", le=200),
    since_days: int = Query(30, description="Get vulnerabilities from last N days", le=365),
    severity: Optional[str] = Query(None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)"),
    db: Session = Depends(get_db)
):
    """
    Generate RSS feed for Cursor-specific vulnerabilities
    Specialized feed for Cursor IDE security blog posts
    """
    logger.info("Generating Cursor-specific RSS feed")
    
    # Calculate date range
    since_date = datetime.utcnow() - timedelta(days=since_days)
    
    # Get Cursor tool
    cursor_tool = db.query(AITool).filter(AITool.name == "cursor").first()
    if not cursor_tool:
        raise HTTPException(status_code=404, detail="Cursor tool not found")
    
    # Build query for Cursor vulnerabilities only - STRICT AI FILTERING
    query = db.query(Vulnerability).filter(
        Vulnerability.discovery_date >= since_date
    )
    
    # CURSOR-SPECIFIC FILTERING - Only include Cursor-related OR general AI coding vulnerabilities
    cursor_condition = or_(
        # Has Cursor tool specifically
        Vulnerability.affected_tools.any(AITool.name == "cursor"),
        # Or contains cursor in title/description
        Vulnerability.title.ilike("%cursor%"),
        Vulnerability.description.ilike("%cursor%"),
        # Or is admin submitted (manually curated)
        Vulnerability.source == "ADMIN_SUBMISSION"
    )
    
    query = query.filter(cursor_condition)
    
    # Apply severity filter
    if severity:
        from app.models.vulnerability import SeverityEnum
        try:
            severity_enum = SeverityEnum(severity.upper())
            query = query.filter(Vulnerability.severity == severity_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    
    # Order and limit
    vulnerabilities = query.order_by(
        Vulnerability.discovery_date.desc()
    ).limit(limit).all()
    
    # Create RSS XML
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    rss.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
    
    channel = ET.SubElement(rss, "channel")
    
    # Channel metadata
    ET.SubElement(channel, "title").text = "Cursor IDE Security Vulnerabilities - Kirin VulnDB"
    ET.SubElement(channel, "link").text = "https://knostic.ai/cursor-security"
    ET.SubElement(channel, "description").text = "Latest security vulnerabilities affecting Cursor IDE - AI-powered code editor security alerts"
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "managingEditor").text = "rick@knostic.ai (Rick Deacon)"
    ET.SubElement(channel, "webMaster").text = "rick@knostic.ai (Rick Deacon)"
    ET.SubElement(channel, "generator").text = "Kirin VulnDB by Knostic AI"
    ET.SubElement(channel, "lastBuildDate").text = format_rss_date(datetime.utcnow())
    
    # Add items
    for vuln in vulnerabilities:
        item = ET.SubElement(channel, "item")
        
        # Title: Focus on Cursor
        title = f"Cursor IDE {vuln.severity.value} Vulnerability: {vuln.cve_id or vuln.vulnerability_id}"
        ET.SubElement(item, "title").text = title
        
        # Link
        ET.SubElement(item, "link").text = f"https://knostic.ai/cursor-vulnerability/{vuln.vulnerability_id}"
        
        # Enhanced description for Cursor
        description_parts = [
            f"<h3>Cursor IDE Security Alert</h3>",
            f"<p><strong>CVE ID:</strong> {vuln.cve_id or 'N/A'}</p>",
            f"<p><strong>Severity:</strong> {vuln.severity.value} (CVSS: {vuln.cvss_score or 'N/A'})</p>",
            f"<p><strong>Patch Status:</strong> {vuln.patch_status.value}</p>",
            f"<h4>Vulnerability Description</h4>",
            f"<p>{html.escape(vuln.description)}</p>"
        ]
        
        if vuln.attack_vectors:
            vectors = ", ".join(vuln.attack_vectors)
            description_parts.append(f"<p><strong>Attack Vectors:</strong> {vectors}</p>")
        
        if vuln.technical_details:
            description_parts.append(f"<h4>Technical Details</h4>")
            description_parts.append(f"<p>{html.escape(vuln.technical_details)}</p>")
        
        # Add Kirin plugin remediation info
        if vuln.kirin_remediation_available:
            description_parts.append(f"<h4>Kirin Plugin Remediation Available</h4>")
            description_parts.append(f"<p>This vulnerability can be automatically remediated using the Kirin security plugin for Cursor IDE.</p>")
        
        if vuln.references:
            description_parts.append(f"<h4>References</h4>")
            description_parts.append("<ul>")
            for ref in vuln.references:
                description_parts.append(f"<li><a href='{ref}' target='_blank'>{ref}</a></li>")
            description_parts.append("</ul>")
        
        description_parts.append(f"<hr>")
        description_parts.append(f"<p><em>Powered by <a href='https://knostic.ai'>Knostic AI</a> - Kirin Vulnerability Database</em></p>")
        
        description = "".join(description_parts)
        ET.SubElement(item, "description").text = description
        ET.SubElement(item, "content:encoded").text = description
        
        # Publication date
        pub_date = vuln.discovery_date or vuln.created_at
        ET.SubElement(item, "pubDate").text = format_rss_date(pub_date)
        
        # GUID
        guid_elem = ET.SubElement(item, "guid", isPermaLink="false")
        guid_elem.text = f"cursor-{vuln.vulnerability_id}"
        
        # Categories
        ET.SubElement(item, "category").text = "Cursor IDE"
        ET.SubElement(item, "category").text = "Security"
        ET.SubElement(item, "category").text = "AI Code Editor"
        ET.SubElement(item, "category").text = f"{vuln.severity.value} Severity"
        
        if vuln.attack_vectors:
            for vector in vuln.attack_vectors:
                ET.SubElement(item, "category").text = vector.replace("_", " ").title()
        
        # Author
        ET.SubElement(item, "dc:creator").text = "Kirin VulnDB Security Team"
    
    # Convert to pretty XML
    rough_string = ET.tostring(rss, 'unicode')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ", encoding=None)
    
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    final_xml = '\n'.join(lines)
    
    return Response(
        content=final_xml,
        media_type="application/rss+xml",
        headers={
            "Content-Disposition": "inline; filename=cursor-vulnerabilities.xml",
            "Cache-Control": "public, max-age=3600"
        }
    )


@router.get("/feed-info")
async def rss_feed_info():
    """Information about available RSS feeds"""
    return {
        "feeds": {
            "all_vulnerabilities": {
                "url": "/api/rss/vulnerabilities.xml",
                "description": "All AI tool vulnerabilities",
                "parameters": [
                    "limit (max 200, default 50)",
                    "since_days (max 365, default 30)", 
                    "severity (CRITICAL, HIGH, MEDIUM, LOW)",
                    "tool (filter by AI tool name)",
                    "patch_status (unpatched, patch_available, patched, wont_fix)"
                ]
            },
            "cursor_vulnerabilities": {
                "url": "/api/rss/cursor-vulnerabilities.xml",
                "description": "Cursor IDE specific vulnerabilities",
                "parameters": [
                    "limit (max 200, default 50)",
                    "since_days (max 365, default 30)",
                    "severity (CRITICAL, HIGH, MEDIUM, LOW)"
                ]
            }
        },
        "wordpress_integration": {
            "description": "These RSS feeds are optimized for WordPress import",
            "features": [
                "HTML formatted content",
                "Proper categories/tags",
                "Publication dates",
                "Unique GUIDs",
                "SEO-friendly titles"
            ]
        },
        "powered_by": "Knostic AI - https://knostic.ai"
    }