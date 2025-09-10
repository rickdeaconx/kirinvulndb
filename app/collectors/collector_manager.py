import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.collectors.nvd_collector import NVDCollector
from app.collectors.vendor_collectors import GitHubSecurityCollector, CursorSecurityCollector, VendorRSSCollector
from app.db.database import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


class CollectorManager:
    """Manages all vulnerability collectors"""
    
    def __init__(self):
        self.collectors = []
        self.is_running = False
        self.stats = {
            "last_run": None,
            "total_collected": 0,
            "errors": 0,
            "collector_stats": {}
        }
        
        # Initialize collectors
        self._initialize_collectors()
    
    def _initialize_collectors(self):
        """Initialize all collectors"""
        
        # Core collectors
        self.collectors.extend([
            NVDCollector(),
            GitHubSecurityCollector(),
            CursorSecurityCollector()
        ])
        
        # RSS feed collectors for various vendors
        rss_feeds = [
            ("Microsoft", "https://msrc.microsoft.com/update-guide/rss"),
            ("JetBrains", "https://blog.jetbrains.com/feed/"),
            ("Tabnine", "https://www.tabnine.com/blog/feed/"),
        ]
        
        for vendor, feed_url in rss_feeds:
            self.collectors.append(VendorRSSCollector(vendor, feed_url))
        
        logger.info(f"Initialized {len(self.collectors)} collectors")
    
    async def run_collection_cycle(self, force: bool = False):
        """Run a complete collection cycle"""
        if self.is_running and not force:
            logger.warning("Collection cycle already running")
            return
        
        self.is_running = True
        logger.info("Starting vulnerability collection cycle")
        
        try:
            # Run collectors based on their intervals
            tasks = []
            
            for collector in self.collectors:
                # Determine if collector should run
                should_run = force
                
                if not should_run:
                    if isinstance(collector, NVDCollector):
                        should_run = collector.should_collect(settings.CVE_COLLECTION_INTERVAL // 60)
                    elif hasattr(collector, 'vendor_name') or 'RSS' in collector.name:
                        should_run = collector.should_collect(settings.COMMUNITY_COLLECTION_INTERVAL // 60)
                    else:
                        should_run = collector.should_collect(settings.VENDOR_COLLECTION_INTERVAL // 60)
                
                if should_run:
                    task = asyncio.create_task(self._run_collector(collector))
                    tasks.append(task)
            
            if tasks:
                # Run collectors concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                total_collected = 0
                for i, result in enumerate(results):
                    collector_name = tasks[i].get_name() if hasattr(tasks[i], 'get_name') else f"collector_{i}"
                    
                    if isinstance(result, Exception):
                        logger.error(f"Collector {collector_name} failed: {result}")
                        self.stats["errors"] += 1
                    else:
                        total_collected += result
                        logger.info(f"Collector {collector_name} collected {result} vulnerabilities")
                
                self.stats["total_collected"] += total_collected
                self.stats["last_run"] = datetime.utcnow()
                
                logger.info(f"Collection cycle completed. Total collected: {total_collected}")
            else:
                logger.info("No collectors needed to run")
                
        except Exception as e:
            logger.error(f"Error in collection cycle: {e}")
            self.stats["errors"] += 1
        finally:
            self.is_running = False
    
    async def _run_collector(self, collector) -> int:
        """Run a single collector"""
        try:
            async with collector:
                # Calculate since date based on collector type
                since = None
                if collector.last_collection:
                    since = collector.last_collection
                else:
                    # Default lookback period
                    since = datetime.utcnow() - timedelta(hours=24)
                
                collected = await collector.run_collection(since)
                
                # Update stats
                self.stats["collector_stats"][collector.name] = {
                    "last_run": datetime.utcnow(),
                    "collected": collected,
                    "success": True
                }
                
                return collected
                
        except Exception as e:
            logger.error(f"Error running collector {collector.name}: {e}")
            self.stats["collector_stats"][collector.name] = {
                "last_run": datetime.utcnow(),
                "collected": 0,
                "success": False,
                "error": str(e)
            }
            raise
    
    async def run_continuous_collection(self):
        """Run continuous collection with scheduled intervals"""
        logger.info("Starting continuous vulnerability collection")
        
        while True:
            try:
                await self.run_collection_cycle()
                
                # Wait for the shortest interval before next check
                wait_time = min(
                    settings.CVE_COLLECTION_INTERVAL,
                    settings.VENDOR_COLLECTION_INTERVAL,
                    settings.COMMUNITY_COLLECTION_INTERVAL
                )
                
                logger.info(f"Waiting {wait_time} seconds before next collection check")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Error in continuous collection: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        return {
            **self.stats,
            "collectors": {
                name: {
                    "type": type(collector).__name__,
                    "last_collection": collector.last_collection.isoformat() if collector.last_collection else None,
                    "status": "active" if collector.last_collection else "pending"
                }
                for name, collector in zip([c.name for c in self.collectors], self.collectors)
            }
        }
    
    async def test_collectors(self) -> Dict[str, Any]:
        """Test all collectors to ensure they're working"""
        results = {}
        
        for collector in self.collectors:
            try:
                async with collector:
                    # Test fetch with minimal data
                    test_since = datetime.utcnow() - timedelta(hours=1)
                    vulnerabilities = await collector.collect_vulnerabilities(test_since)
                    
                    results[collector.name] = {
                        "status": "success",
                        "test_results": len(vulnerabilities) if vulnerabilities else 0,
                        "tested_at": datetime.utcnow().isoformat()
                    }
                    
            except Exception as e:
                results[collector.name] = {
                    "status": "error",
                    "error": str(e),
                    "tested_at": datetime.utcnow().isoformat()
                }
        
        return results


# Global collector manager instance
collector_manager = CollectorManager()