#!/usr/bin/env python3
"""
Test script for vulnerability collectors
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors.collector_manager import collector_manager
from app.collectors.nvd_collector import NVDCollector
from app.collectors.vendor_collectors import GitHubSecurityCollector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_individual_collectors():
    """Test individual collectors"""
    logger.info("Testing individual collectors...")
    
    # Test NVD Collector
    logger.info("Testing NVD Collector...")
    nvd = NVDCollector()
    
    async with nvd:
        try:
            vulns = await nvd.collect_vulnerabilities()
            logger.info(f"NVD Collector returned {len(vulns) if vulns else 0} vulnerabilities")
            
            if vulns:
                # Test parsing first vulnerability
                parsed = nvd.parse_vulnerability(vulns[0])
                if parsed:
                    logger.info(f"Successfully parsed NVD vulnerability: {parsed['vulnerability_id']}")
                else:
                    logger.info("No AI tool vulnerabilities found in NVD data")
        except Exception as e:
            logger.error(f"NVD Collector test failed: {e}")
    
    # Test GitHub Collector
    logger.info("Testing GitHub Security Collector...")
    github = GitHubSecurityCollector()
    
    async with github:
        try:
            advisories = await github.collect_vulnerabilities()
            logger.info(f"GitHub Collector returned {len(advisories) if advisories else 0} advisories")
            
            if advisories:
                parsed = github.parse_vulnerability(advisories[0])
                if parsed:
                    logger.info(f"Successfully parsed GitHub advisory: {parsed['vulnerability_id']}")
                else:
                    logger.info("No AI tool advisories found in GitHub data")
        except Exception as e:
            logger.error(f"GitHub Collector test failed: {e}")


async def test_collector_manager():
    """Test the collector manager"""
    logger.info("Testing collector manager...")
    
    try:
        # Test all collectors
        test_results = await collector_manager.test_collectors()
        
        logger.info("Collector test results:")
        for name, result in test_results.items():
            status = result['status']
            if status == 'success':
                logger.info(f"  ✓ {name}: {result['test_results']} items")
            else:
                logger.error(f"  ✗ {name}: {result['error']}")
        
        # Get stats
        stats = collector_manager.get_stats()
        logger.info(f"Collector manager stats: {stats}")
        
    except Exception as e:
        logger.error(f"Collector manager test failed: {e}")


async def run_sample_collection():
    """Run a sample collection cycle"""
    logger.info("Running sample collection cycle...")
    
    try:
        await collector_manager.run_collection_cycle(force=True)
        logger.info("Sample collection cycle completed")
    except Exception as e:
        logger.error(f"Sample collection failed: {e}")


async def main():
    """Main test function"""
    logger.info("Starting collector tests...")
    
    # Test individual collectors
    await test_individual_collectors()
    
    # Test collector manager
    await test_collector_manager()
    
    # Run sample collection (commented out to avoid making too many API calls)
    # await run_sample_collection()
    
    logger.info("Collector tests completed")


if __name__ == "__main__":
    asyncio.run(main())