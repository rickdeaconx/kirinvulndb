from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode

from app.collectors.base_collector import BaseCollector
from app.core.config import settings

logger = logging.getLogger(__name__)


class NVDCollector(BaseCollector):
    """National Vulnerability Database (NVD) collector"""
    
    def __init__(self):
        super().__init__(
            name="NVD",
            base_url=settings.NVD_BASE_URL,
            rate_limit=50  # NVD allows up to 50 requests per 30 seconds with API key
        )
        self.api_key = settings.NVD_API_KEY
    
    async def collect_vulnerabilities(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Collect vulnerabilities from NVD API"""
        vulnerabilities = []
        
        # Default to last 24 hours if no since date provided
        if not since:
            since = datetime.utcnow() - timedelta(hours=24)
        
        # NVD API parameters
        params = {
            "pubStartDate": since.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "pubEndDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000"),
            "resultsPerPage": 2000,  # Maximum allowed
            "startIndex": 0
        }
        
        # Add API key if available
        if self.api_key:
            headers = {"apiKey": self.api_key}
            self.session.headers.update(headers)
        
        url = f"{self.base_url}/cves/2.0"
        
        while True:
            # Fetch batch of vulnerabilities
            data = await self.fetch_data(url, params)
            
            if not data or "vulnerabilities" not in data:
                break
            
            vulnerabilities.extend(data["vulnerabilities"])
            
            # Check if there are more results
            total_results = data.get("totalResults", 0)
            current_index = params["startIndex"] + params["resultsPerPage"]
            
            if current_index >= total_results:
                break
            
            # Update start index for next batch
            params["startIndex"] = current_index
            
            logger.info(f"Collected {len(vulnerabilities)} vulnerabilities so far from NVD")
        
        # Filter for AI tool related vulnerabilities
        ai_vulnerabilities = []
        for vuln in vulnerabilities:
            if self._is_ai_tool_related(vuln):
                ai_vulnerabilities.append(vuln)
        
        logger.info(f"Found {len(ai_vulnerabilities)} AI tool related vulnerabilities out of {len(vulnerabilities)} total")
        return ai_vulnerabilities
    
    def parse_vulnerability(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse NVD vulnerability data into standard format"""
        try:
            cve = raw_data.get("cve", {})
            cve_id = cve.get("id", "")
            
            # Basic information
            descriptions = cve.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break
            
            if not description and descriptions:
                description = descriptions[0].get("value", "")
            
            # Metrics and severity
            metrics = cve.get("metrics", {})
            cvss_score = None
            cvss_vector = None
            severity = "INFO"
            
            # Try CVSS v3.1 first, then v3.0, then v2.0
            for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV20"]:
                if version in metrics and metrics[version]:
                    metric = metrics[version][0]  # Take first metric
                    cvss_data = metric.get("cvssData", {})
                    cvss_score = cvss_data.get("baseScore")
                    cvss_vector = cvss_data.get("vectorString")
                    break
            
            severity = self.map_severity(cvss_score)
            
            # References
            references = []
            for ref in cve.get("references", []):
                url = ref.get("url")
                if url:
                    references.append(url)
            
            # CPE names for affected products
            cpe_names = []
            configurations = cve.get("configurations", [])
            for config in configurations:
                for node in config.get("nodes", []):
                    for cpe_match in node.get("cpeMatch", []):
                        cpe_name = cpe_match.get("criteria", "")
                        if cpe_name:
                            cpe_names.append(cpe_name)
            
            # Extract affected tools
            affected_tools = self.extract_affected_tools(description, cpe_names)
            
            if not affected_tools:
                # If no tools detected, skip this vulnerability
                return None
            
            # Dates
            published_date = None
            modified_date = None
            
            if "published" in cve:
                published_date = datetime.fromisoformat(cve["published"].replace("Z", "+00:00"))
            
            if "lastModified" in cve:
                modified_date = datetime.fromisoformat(cve["lastModified"].replace("Z", "+00:00"))
            
            # Weakness enumeration (CWE)
            cwe_ids = []
            for weakness in cve.get("weaknesses", []):
                for desc in weakness.get("description", []):
                    cwe_id = desc.get("value", "")
                    if cwe_id.startswith("CWE-"):
                        cwe_ids.append(cwe_id)
            
            # Attack vectors from CVSS
            attack_vectors = []
            if cvss_vector:
                if "AV:N" in cvss_vector:  # Network attack vector
                    attack_vectors.append("rce")
                if "PR:N" in cvss_vector:  # No privileges required
                    attack_vectors.append("injection")
            
            return {
                "vulnerability_id": f"nvd-{cve_id}",
                "cve_id": cve_id,
                "title": f"{cve_id}: AI Coding Assistant Vulnerability",
                "description": description,
                "severity": severity,
                "cvss_score": cvss_score,
                "cvss_vector": cvss_vector,
                "discovery_date": published_date or datetime.utcnow(),
                "public_disclosure": published_date,
                "attack_vectors": attack_vectors,
                "patch_status": "unpatched",  # Default, will be updated later
                "references": references,
                "source": "nvd",
                "confidence_score": 0.9,  # High confidence for NVD data
                "affected_tools": affected_tools,
                "cwe_ids": cwe_ids,
                "tags": ["nvd", "cve"] + cwe_ids
            }
            
        except Exception as e:
            logger.error(f"Error parsing NVD vulnerability {raw_data.get('cve', {}).get('id', 'unknown')}: {e}")
            return None
    
    def _is_ai_tool_related(self, vuln_data: Dict[str, Any]) -> bool:
        """Check if vulnerability is related to AI coding tools"""
        cve = vuln_data.get("cve", {})
        
        # Check descriptions
        descriptions = cve.get("descriptions", [])
        for desc in descriptions:
            description = desc.get("value", "").lower()
            
            # AI tool keywords
            ai_keywords = [
                "cursor", "copilot", "codewhisperer", "tabnine", "codeium",
                "ghostwriter", "replit", "sourcegraph", "cody", "jetbrains",
                "ai assistant", "code completion", "code generation",
                "artificial intelligence", "machine learning", "neural code",
                "intelligent code", "autocomplete", "code suggestion"
            ]
            
            for keyword in ai_keywords:
                if keyword in description:
                    return True
        
        # Check CPE names
        configurations = cve.get("configurations", [])
        for config in configurations:
            for node in config.get("nodes", []):
                for cpe_match in node.get("cpeMatch", []):
                    cpe_name = cpe_match.get("criteria", "").lower()
                    
                    ai_vendors = [
                        "cursor", "github", "amazon", "tabnine", "codeium",
                        "replit", "sourcegraph", "jetbrains"
                    ]
                    
                    for vendor in ai_vendors:
                        if vendor in cpe_name:
                            return True
        
        return False