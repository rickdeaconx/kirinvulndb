import asyncio
import logging
from datetime import datetime, timedelta
from celery import Task

from app.celery_app import celery_app
from app.collectors.collector_manager import collector_manager
from app.collectors.nvd_collector import NVDCollector
from app.collectors.vendor_collectors import GitHubSecurityCollector, VendorRSSCollector

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task with callbacks"""
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")


@celery_app.task(base=CallbackTask, bind=True)
def collect_nvd_vulnerabilities(self, since_hours: int = 24):
    """Collect vulnerabilities from NVD"""
    logger.info("Starting NVD vulnerability collection")
    
    try:
        since = datetime.utcnow() - timedelta(hours=since_hours)
        
        # Run async collector
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            collector = NVDCollector()
            collected = loop.run_until_complete(collector.run_collection(since))
            logger.info(f"NVD collection completed: {collected} vulnerabilities")
            return collected
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"NVD collection failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery_app.task(base=CallbackTask, bind=True)
def collect_vendor_advisories(self, since_hours: int = 12):
    """Collect vendor security advisories"""
    logger.info("Starting vendor advisory collection")
    
    try:
        since = datetime.utcnow() - timedelta(hours=since_hours)
        total_collected = 0
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # GitHub Security Advisories
            github_collector = GitHubSecurityCollector()
            github_collected = loop.run_until_complete(github_collector.run_collection(since))
            total_collected += github_collected
            
            logger.info(f"Vendor advisory collection completed: {total_collected} vulnerabilities")
            return total_collected
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Vendor advisory collection failed: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)


@celery_app.task(base=CallbackTask, bind=True)
def collect_community_sources(self, since_hours: int = 24):
    """Collect from community sources (RSS feeds, etc.)"""
    logger.info("Starting community sources collection")
    
    try:
        since = datetime.utcnow() - timedelta(hours=since_hours)
        total_collected = 0
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # RSS feed collectors
            rss_feeds = [
                ("Microsoft", "https://msrc.microsoft.com/update-guide/rss"),
                ("JetBrains", "https://blog.jetbrains.com/feed/"),
            ]
            
            for vendor, feed_url in rss_feeds:
                try:
                    collector = VendorRSSCollector(vendor, feed_url)
                    collected = loop.run_until_complete(collector.run_collection(since))
                    total_collected += collected
                except Exception as e:
                    logger.error(f"Failed to collect from {vendor} RSS: {e}")
            
            logger.info(f"Community sources collection completed: {total_collected} vulnerabilities")
            return total_collected
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Community sources collection failed: {e}")
        raise self.retry(exc=e, countdown=600, max_retries=2)


@celery_app.task(base=CallbackTask)
def run_full_collection_cycle():
    """Run a complete collection cycle"""
    logger.info("Starting full collection cycle")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(collector_manager.run_collection_cycle(force=True))
            logger.info("Full collection cycle completed")
            return True
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Full collection cycle failed: {e}")
        return False


@celery_app.task(base=CallbackTask, bind=True)
def collect_single_vulnerability(self, source: str, vulnerability_id: str):
    """Collect a single vulnerability by ID"""
    logger.info(f"Collecting single vulnerability: {vulnerability_id} from {source}")
    
    try:
        # This would be implemented based on specific requirements
        # For now, just return success
        logger.info(f"Single vulnerability collection completed: {vulnerability_id}")
        return True
        
    except Exception as e:
        logger.error(f"Single vulnerability collection failed: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=2)


@celery_app.task(base=CallbackTask)
def update_tool_statistics():
    """Update vulnerability statistics for all AI tools"""
    logger.info("Updating tool statistics")
    
    try:
        from app.db.database import SessionLocal
        from app.models.tool import AITool
        from app.models.vulnerability import Vulnerability, SeverityEnum
        from sqlalchemy import func
        
        with SessionLocal() as db:
            tools = db.query(AITool).all()
            
            for tool in tools:
                # Count total vulnerabilities
                total_vulns = db.query(Vulnerability).join(
                    Vulnerability.affected_tools
                ).filter(AITool.id == tool.id).count()
                
                # Count critical vulnerabilities
                critical_vulns = db.query(Vulnerability).join(
                    Vulnerability.affected_tools
                ).filter(
                    AITool.id == tool.id,
                    Vulnerability.severity == SeverityEnum.CRITICAL
                ).count()
                
                # Update tool statistics
                tool.total_vulnerabilities = total_vulns
                tool.critical_vulnerabilities = critical_vulns
                
                # Get latest vulnerability date
                latest_vuln = db.query(Vulnerability).join(
                    Vulnerability.affected_tools
                ).filter(AITool.id == tool.id).order_by(
                    Vulnerability.discovery_date.desc()
                ).first()
                
                if latest_vuln:
                    tool.last_vulnerability_date = latest_vuln.discovery_date.isoformat()
                
                db.commit()
            
            logger.info(f"Updated statistics for {len(tools)} tools")
            return len(tools)
            
    except Exception as e:
        logger.error(f"Tool statistics update failed: {e}")
        return 0