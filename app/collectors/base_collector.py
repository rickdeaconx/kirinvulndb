from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import httpx
import asyncio
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.vulnerability import Vulnerability
from app.services.vulnerability_service import VulnerabilityService

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Base class for vulnerability collectors"""
    
    def __init__(self, name: str, base_url: str, rate_limit: int = 60):
        self.name = name
        self.base_url = base_url
        self.rate_limit = rate_limit  # requests per minute
        self.last_collection = None
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    @abstractmethod
    async def collect_vulnerabilities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Collect vulnerabilities from the source"""
        pass
    
    @abstractmethod
    def parse_vulnerability(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse raw vulnerability data into standard format"""
        pass
    
    async def fetch_data(self, url: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Fetch data from API with rate limiting"""
        try:
            # Rate limiting
            await self._rate_limit()
            
            logger.info(f"Fetching data from {url}")
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    async def _rate_limit(self):
        """Simple rate limiting"""
        if hasattr(self, '_last_request'):
            elapsed = datetime.now() - self._last_request
            min_interval = 60 / self.rate_limit  # seconds between requests
            
            if elapsed.total_seconds() < min_interval:
                wait_time = min_interval - elapsed.total_seconds()
                await asyncio.sleep(wait_time)
        
        self._last_request = datetime.now()
    
    async def run_collection(self, since: Optional[datetime] = None) -> int:
        """Run the collection process"""
        logger.info(f"Starting collection for {self.name}")
        
        try:
            # Collect raw data
            vulnerabilities = await self.collect_vulnerabilities(since)
            
            if not vulnerabilities:
                logger.info(f"No vulnerabilities collected from {self.name}")
                return 0
            
            # Process and store vulnerabilities
            processed = 0
            errors = 0
            
            with SessionLocal() as db:
                service = VulnerabilityService(db)
                
                for vuln_data in vulnerabilities:
                    try:
                        parsed = self.parse_vulnerability(vuln_data)
                        if parsed:
                            # Check if already exists
                            existing = service.get_vulnerability_by_id(parsed['vulnerability_id'])
                            
                            if existing:
                                # Update existing
                                from app.schemas.vulnerability import VulnerabilityUpdate
                                update_data = VulnerabilityUpdate(**parsed)
                                service.update_vulnerability(parsed['vulnerability_id'], update_data)
                                logger.debug(f"Updated vulnerability: {parsed['vulnerability_id']}")
                            else:
                                # Create new
                                from app.schemas.vulnerability import VulnerabilityCreate
                                create_data = VulnerabilityCreate(**parsed)
                                service.create_vulnerability(create_data)
                                logger.debug(f"Created vulnerability: {parsed['vulnerability_id']}")
                            
                            processed += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing vulnerability from {self.name}: {e}")
                        errors += 1
            
            self.last_collection = datetime.utcnow()
            logger.info(f"Collection completed for {self.name}. Processed: {processed}, Errors: {errors}")
            return processed
            
        except Exception as e:
            logger.error(f"Collection failed for {self.name}: {e}")
            return 0
    
    def should_collect(self, interval_minutes: int) -> bool:
        """Check if collection should run based on interval"""
        if not self.last_collection:
            return True
        
        elapsed = datetime.utcnow() - self.last_collection
        return elapsed > timedelta(minutes=interval_minutes)
    
    def map_severity(self, cvss_score: Optional[float]) -> str:
        """Map CVSS score to severity level"""
        if not cvss_score:
            return "INFO"
        
        if cvss_score >= 9.0:
            return "CRITICAL"
        elif cvss_score >= 7.0:
            return "HIGH"
        elif cvss_score >= 4.0:
            return "MEDIUM"
        elif cvss_score >= 0.1:
            return "LOW"
        else:
            return "INFO"
    
    def extract_affected_tools(self, description: str, cpe_names: List[str] = None) -> List[str]:
        """Extract affected AI tools from description and CPE names"""
        tools = []
        
        # Tool name mappings
        tool_keywords = {
            "cursor": ["cursor", "cursor.ai"],
            "github_copilot": ["github copilot", "copilot", "github.copilot"],
            "amazon_codewhisperer": ["codewhisperer", "amazon codewhisperer", "aws codewhisperer"],
            "tabnine": ["tabnine", "tab nine"],
            "codeium": ["codeium"],
            "replit_ghostwriter": ["replit", "ghostwriter", "replit ghostwriter"],
            "sourcegraph_cody": ["sourcegraph", "cody"],
            "jetbrains_ai_assistant": ["jetbrains", "intellij", "pycharm", "webstorm"]
        }
        
        # Search in description
        description_lower = description.lower()
        for tool, keywords in tool_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    tools.append(tool)
                    break
        
        # Search in CPE names if available
        if cpe_names:
            for cpe in cpe_names:
                cpe_lower = cpe.lower()
                for tool, keywords in tool_keywords.items():
                    for keyword in keywords:
                        if keyword.replace(" ", "_") in cpe_lower:
                            if tool not in tools:
                                tools.append(tool)
        
        return tools