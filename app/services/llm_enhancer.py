"""
OpenAI LLM Enhancement Service for Vulnerability Processing
Transforms raw vulnerability data into blog-style summaries for Kirin
"""

import os
import logging
from typing import Optional
from openai import AsyncOpenAI
from app.models.vulnerability import Vulnerability
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMVulnerabilityEnhancer:
    """OpenAI-powered vulnerability content enhancement service"""
    
    def __init__(self):
        self.client = None
        self.api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if self.api_key and self.api_key != "your_openai_key_here":
            try:
                self.client = AsyncOpenAI(api_key=self.api_key)
                logger.info("OpenAI LLM enhancer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("OpenAI API key not configured - LLM enhancement disabled")
    
    async def enhance_vulnerability(self, vulnerability: Vulnerability) -> dict:
        """
        Transform vulnerability data into blog-style content suitable for RSS
        
        Args:
            vulnerability: Raw vulnerability object from monitoring
            
        Returns:
            Enhanced content dict with blog-style summary, details, and developer guidance
        """
        if not self.client:
            # Return original content if OpenAI not configured
            return self._fallback_formatting(vulnerability)
        
        try:
            # Prepare vulnerability context for LLM
            vuln_context = self._prepare_vulnerability_context(vulnerability)
            
            # Generate enhanced content using OpenAI
            enhanced_content = await self._generate_enhanced_content(vuln_context)
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"LLM enhancement failed for {vulnerability.vulnerability_id}: {e}")
            return self._fallback_formatting(vulnerability)
    
    def _prepare_vulnerability_context(self, vuln: Vulnerability) -> str:
        """Prepare vulnerability data as context for LLM processing"""
        
        # Get affected tools info
        affected_tools = []
        for tool in vuln.affected_tools:
            affected_tools.append(f"- {tool.display_name} ({tool.vendor})")
        
        tools_text = "\n".join(affected_tools) if affected_tools else "No specific tools identified"
        
        # Get attack vectors
        vectors = [vector.value for vector in vuln.attack_vectors] if vuln.attack_vectors else []
        vectors_text = ", ".join(vectors) if vectors else "Not specified"
        
        # Prepare context
        context = f"""
VULNERABILITY DATA:
ID: {vuln.vulnerability_id}
Title: {vuln.title}
Severity: {vuln.severity.value} (CVSS: {vuln.cvss_score or 'N/A'})
Description: {vuln.description}
Discovery Date: {vuln.discovery_date.strftime('%Y-%m-%d') if vuln.discovery_date else 'Unknown'}
Patch Status: {vuln.patch_status.value}
Attack Vectors: {vectors_text}
Source: {vuln.source}
Confidence: {vuln.confidence_score}/1.0

AFFECTED AI TOOLS:
{tools_text}

REFERENCES:
{chr(10).join([f"- {getattr(ref, 'title', str(ref))}: {getattr(ref, 'url', str(ref))}" for ref in vuln.references]) if vuln.references else "No references available"}

TAGS: {', '.join(vuln.tags) if vuln.tags else 'None'}
"""
        return context
    
    async def _generate_enhanced_content(self, vuln_context: str) -> dict:
        """Generate enhanced blog-style content using OpenAI"""
        
        prompt = f"""
You are a cybersecurity expert writing for the Kirin vulnerability intelligence platform. Transform the following AI coding assistant vulnerability into a professional blog post suitable for developers and security professionals.

Create content with these sections:
1. **Executive Summary**: 2-3 sentences capturing the key security impact
2. **Technical Details**: What the vulnerability is and how it works
3. **Risk Assessment**: Why this matters for developers using AI coding tools
4. **Mitigation Guidance**: Specific steps developers should take
5. **Kirin Intelligence**: Brief context on how this fits into the AI security landscape

Guidelines:
- Write in a professional, informative tone
- Focus on practical implications for developers
- Highlight cybersecurity concerns specific to AI coding assistants
- Keep technical details accessible but thorough
- Emphasize actionable guidance
- Use proper markdown formatting for blog readability
- ABSOLUTELY NO EMOJIS - Use only text, no symbols, no Unicode characters
- Strictly professional business writing style only

VULNERABILITY DATA:
{vuln_context}

Generate the enhanced blog content:
"""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert specializing in AI coding assistant vulnerabilities for the Kirin platform."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            enhanced_content = response.choices[0].message.content
            
            # Parse the enhanced content into structured format
            first_line = enhanced_content.split('\n')[0].replace('#', '').strip()
            return {
                "enhanced_title": f"{first_line}",
                "enhanced_description": enhanced_content,
                "blog_format": True,
                "enhanced_by_llm": True,
                "enhancement_timestamp": "2024-01-01T00:00:00Z"  # Will be updated with actual timestamp
            }
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _fallback_formatting(self, vuln: Vulnerability) -> dict:
        """Fallback formatting when LLM is not available"""
        
        # Create basic blog-style formatting without LLM
        affected_tools_text = ""
        if vuln.affected_tools:
            tools = [tool.display_name for tool in vuln.affected_tools]
            affected_tools_text = f" affecting {', '.join(tools)}"
        
        enhanced_title = f"{vuln.title}"
        
        enhanced_desc = f"""
## Executive Summary
{vuln.title}{affected_tools_text} has been identified with {vuln.severity.value.lower()} severity.

## Technical Details
{vuln.description}

## Risk Assessment
- **Severity**: {vuln.severity.value}
- **CVSS Score**: {vuln.cvss_score or 'Not assessed'}
- **Patch Status**: {vuln.patch_status.value}
- **Confidence Level**: {vuln.confidence_score}/1.0

## Affected Tools
{chr(10).join([f"- {tool.display_name} ({tool.vendor})" for tool in vuln.affected_tools]) if vuln.affected_tools else "No specific tools identified"}

## Mitigation Guidance
Monitor for patches and updates from affected vendors. Review your AI coding assistant configurations and consider additional security measures.

---
*This alert was generated by Kirin vulnerability intelligence system.*
"""
        
        return {
            "enhanced_title": enhanced_title,
            "enhanced_description": enhanced_desc,
            "blog_format": True,
            "enhanced_by_llm": False,
            "enhancement_timestamp": "2024-01-01T00:00:00Z"
        }


# Global instance
llm_enhancer = LLMVulnerabilityEnhancer()