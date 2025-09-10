from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import re
from bs4 import BeautifulSoup
import feedparser

from app.collectors.base_collector import BaseCollector
from app.core.config import settings

logger = logging.getLogger(__name__)


class GitHubSecurityCollector(BaseCollector):
    """GitHub Security Advisories collector"""
    
    def __init__(self):
        super().__init__(
            name="GitHub Security",
            base_url="https://api.github.com",
            rate_limit=30  # GitHub API rate limit
        )
        self.token = settings.GITHUB_TOKEN
        
        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})
    
    async def collect_vulnerabilities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Collect GitHub security advisories"""
        vulnerabilities = []
        
        if not since:
            since = datetime.utcnow() - timedelta(hours=24)
        
        # GitHub Security Advisories API
        params = {
            "published": f">{since.strftime('%Y-%m-%d')}",
            "per_page": 100,
            "page": 1
        }
        
        url = f"{self.base_url}/advisories"
        
        while True:
            data = await self.fetch_data(url, params)
            
            if not data or not isinstance(data, list):
                break
            
            # Filter for AI tool related advisories
            for advisory in data:
                if self._is_ai_tool_advisory(advisory):
                    vulnerabilities.append(advisory)
            
            # Check for next page
            if len(data) < params["per_page"]:
                break
            
            params["page"] += 1
            
            if params["page"] > 10:  # Prevent infinite loops
                break
        
        logger.info(f"Collected {len(vulnerabilities)} GitHub security advisories")
        return vulnerabilities
    
    def parse_vulnerability(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse GitHub advisory data"""
        try:
            ghsa_id = raw_data.get("ghsa_id", "")
            cve_id = raw_data.get("cve_id")
            
            title = raw_data.get("summary", "")
            description = raw_data.get("description", "")
            
            # Severity mapping
            severity_map = {
                "critical": "CRITICAL",
                "high": "HIGH", 
                "medium": "MEDIUM",
                "low": "LOW"
            }
            severity = severity_map.get(raw_data.get("severity", "").lower(), "MEDIUM")
            
            # CVSS score
            cvss = raw_data.get("cvss", {})
            cvss_score = cvss.get("score") if cvss else None
            cvss_vector = cvss.get("vector_string") if cvss else None
            
            # Dates
            published_at = None
            if raw_data.get("published_at"):
                published_at = datetime.fromisoformat(raw_data["published_at"].replace("Z", "+00:00"))
            
            # References
            references = [raw_data.get("html_url", "")]
            for ref in raw_data.get("references", []):
                if ref.get("url"):
                    references.append(ref["url"])
            
            # Extract affected tools from description and title
            full_text = f"{title} {description}".lower()
            affected_tools = self.extract_affected_tools(full_text)
            
            if not affected_tools:
                return None
            
            return {
                "vulnerability_id": f"github-{ghsa_id}",
                "cve_id": cve_id,
                "title": title,
                "description": description,
                "severity": severity,
                "cvss_score": cvss_score,
                "cvss_vector": cvss_vector,
                "discovery_date": published_at or datetime.utcnow(),
                "public_disclosure": published_at,
                "attack_vectors": self._extract_attack_vectors(description),
                "patch_status": "unpatched",
                "references": references,
                "source": "github",
                "confidence_score": 0.85,
                "affected_tools": affected_tools,
                "tags": ["github", "security-advisory", ghsa_id]
            }
            
        except Exception as e:
            logger.error(f"Error parsing GitHub advisory: {e}")
            return None
    
    def _is_ai_tool_advisory(self, advisory: Dict[str, Any]) -> bool:
        """Check if advisory is related to AI coding tools"""
        text = f"{advisory.get('summary', '')} {advisory.get('description', '')}".lower()
        
        ai_keywords = [
            "cursor", "copilot", "codewhisperer", "tabnine", "codeium",
            "ghostwriter", "replit", "sourcegraph", "cody", "ai assistant"
        ]
        
        return any(keyword in text for keyword in ai_keywords)
    
    def _extract_attack_vectors(self, description: str) -> List[str]:
        """Extract attack vectors from description"""
        vectors = []
        text = description.lower()
        
        vector_keywords = {
            "rce": ["remote code execution", "code execution", "rce"],
            "injection": ["injection", "sql injection", "command injection"],
            "xss": ["cross-site scripting", "xss"],
            "prompt_injection": ["prompt injection", "model injection"]
        }
        
        for vector, keywords in vector_keywords.items():
            if any(keyword in text for keyword in keywords):
                vectors.append(vector)
        
        return vectors


class CursorSecurityCollector(BaseCollector):
    """Cursor.ai security collector"""
    
    def __init__(self):
        super().__init__(
            name="Cursor Security",
            base_url="https://cursor.ai",
            rate_limit=30
        )
    
    async def collect_vulnerabilities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Collect Cursor security information"""
        vulnerabilities = []
        
        # Check Cursor's security page, changelog, and GitHub releases
        sources = [
            "https://cursor.ai/security",
            "https://cursor.ai/changelog",
            "https://api.github.com/repos/cursor/cursor/releases"
        ]
        
        for source in sources:
            try:
                data = await self.fetch_data(source)
                if data:
                    parsed = self._parse_cursor_source(source, data, since)
                    vulnerabilities.extend(parsed)
            except Exception as e:
                logger.error(f"Error collecting from {source}: {e}")
        
        return vulnerabilities
    
    def parse_vulnerability(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Cursor vulnerability data"""
        # Implementation would depend on the specific format
        # This is a placeholder that would need to be customized
        return None
    
    def _parse_cursor_source(self, source: str, data: Any, since: Optional[datetime]) -> List[Dict[str, Any]]:
        """Parse different Cursor data sources"""
        vulnerabilities = []
        
        if "github.com" in source:
            # GitHub releases format
            if isinstance(data, list):
                for release in data:
                    if self._is_security_release(release):
                        vulnerabilities.append(release)
        
        # Add more source parsing logic here
        
        return vulnerabilities
    
    def _is_security_release(self, release: Dict[str, Any]) -> bool:
        """Check if GitHub release is security-related"""
        text = f"{release.get('name', '')} {release.get('body', '')}".lower()
        security_keywords = ["security", "vulnerability", "fix", "patch", "cve"]
        return any(keyword in text for keyword in security_keywords)


class VendorRSSCollector(BaseCollector):
    """Generic RSS/Atom feed collector for vendor security feeds"""
    
    def __init__(self, vendor_name: str, feed_url: str):
        super().__init__(
            name=f"{vendor_name} RSS",
            base_url=feed_url,
            rate_limit=10  # Conservative rate limit for RSS
        )
        self.vendor_name = vendor_name
        self.feed_url = feed_url
    
    async def collect_vulnerabilities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Collect vulnerabilities from RSS/Atom feeds"""
        vulnerabilities = []
        
        try:
            # Fetch RSS feed
            response = await self.session.get(self.feed_url)
            response.raise_for_status()
            
            # Parse feed
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries:
                # Check if entry is recent enough
                if since and hasattr(entry, 'published_parsed'):
                    entry_date = datetime(*entry.published_parsed[:6])
                    if entry_date < since:
                        continue
                
                # Check if entry is security-related
                if self._is_security_entry(entry):
                    vulnerabilities.append(entry)
            
        except Exception as e:
            logger.error(f"Error collecting RSS feed {self.feed_url}: {e}")
        
        return vulnerabilities
    
    def parse_vulnerability(self, raw_data: Any) -> Optional[Dict[str, Any]]:
        """Parse RSS entry data"""
        try:
            title = getattr(raw_data, 'title', '')
            description = getattr(raw_data, 'description', '') or getattr(raw_data, 'summary', '')
            link = getattr(raw_data, 'link', '')
            
            # Extract publication date
            published_date = datetime.utcnow()
            if hasattr(raw_data, 'published_parsed') and raw_data.published_parsed:
                published_date = datetime(*raw_data.published_parsed[:6])
            
            # Clean HTML from description
            if description:
                soup = BeautifulSoup(description, 'html.parser')
                description = soup.get_text(strip=True)
            
            # Extract affected tools
            full_text = f"{title} {description}".lower()
            affected_tools = self.extract_affected_tools(full_text)
            
            if not affected_tools:
                return None
            
            # Generate unique ID
            import hashlib
            vuln_id = f"rss-{self.vendor_name.lower()}-{hashlib.md5(link.encode()).hexdigest()[:8]}"
            
            return {
                "vulnerability_id": vuln_id,
                "cve_id": self._extract_cve_id(f"{title} {description}"),
                "title": title,
                "description": description,
                "severity": self._estimate_severity(f"{title} {description}"),
                "discovery_date": published_date,
                "public_disclosure": published_date,
                "references": [link],
                "source": f"rss-{self.vendor_name.lower()}",
                "confidence_score": 0.7,  # Lower confidence for RSS sources
                "affected_tools": affected_tools,
                "tags": ["rss", self.vendor_name.lower()]
            }
            
        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None
    
    def _is_security_entry(self, entry: Any) -> bool:
        """Check if RSS entry is security-related"""
        text = f"{getattr(entry, 'title', '')} {getattr(entry, 'description', '')}".lower()
        security_keywords = [
            "security", "vulnerability", "cve", "patch", "fix", "update",
            "advisory", "alert", "exploit", "bug fix"
        ]
        return any(keyword in text for keyword in security_keywords)
    
    def _extract_cve_id(self, text: str) -> Optional[str]:
        """Extract CVE ID from text"""
        cve_pattern = r'CVE-\d{4}-\d{4,}'
        match = re.search(cve_pattern, text.upper())
        return match.group(0) if match else None
    
    def _estimate_severity(self, text: str) -> str:
        """Estimate severity from text content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["critical", "urgent", "immediate", "zero-day"]):
            return "CRITICAL"
        elif any(word in text_lower for word in ["high", "important", "severe"]):
            return "HIGH"
        elif any(word in text_lower for word in ["medium", "moderate"]):
            return "MEDIUM"
        elif any(word in text_lower for word in ["low", "minor"]):
            return "LOW"
        else:
            return "MEDIUM"  # Default