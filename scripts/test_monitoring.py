#!/usr/bin/env python3
"""
Test the vulnerability monitoring system
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vulnerability_monitor import VulnerabilityMonitor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_monitoring():
    """Test the monitoring system"""
    logger.info("Testing vulnerability monitoring system...")
    
    async with VulnerabilityMonitor() as monitor:
        # Test a single discovery cycle
        stats = await monitor.run_discovery_cycle()
        
        logger.info("Monitoring test completed!")
        logger.info(f"Results: {stats}")
        
        return stats

if __name__ == "__main__":
    results = asyncio.run(test_monitoring())
    print(f"\n🔍 MONITORING TEST RESULTS:")
    print(f"📊 Sources checked: {results['sources_checked']}")
    print(f"🔍 Total vulnerabilities found: {results['total_found']}")
    print(f"✅ New vulnerabilities added: {results['new_vulnerabilities']}")
    print(f"\n✨ Test completed successfully!")