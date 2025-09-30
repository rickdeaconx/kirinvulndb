"""
OpenAI LLM Enhancement Service for Vulnerability Processing
Transforms raw vulnerability data into blog-style summaries for Kirin
"""

import os
import logging
import re
from typing import Optional
from openai import AsyncOpenAI
from app.models.vulnerability import Vulnerability
from app.core.config import settings

logger = logging.getLogger(__name__)


def markdown_to_html(markdown_text: str) -> str:
    """Convert basic markdown formatting to HTML for WordPress compatibility"""
    if not markdown_text:
        return ""
    
    html_text = markdown_text
    
    # Convert headers
    html_text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html_text, flags=re.MULTILINE)
    html_text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html_text, flags=re.MULTILINE)
    html_text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html_text, flags=re.MULTILINE)
    
    # Convert bold text
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)
    
    # Convert italic text
    html_text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_text)
    
    # Convert bullet lists
    lines = html_text.split('\n')
    in_list = False
    converted_lines = []
    
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                converted_lines.append('<ul>')
                in_list = True
            list_item = line.strip()[2:]  # Remove '- '
            converted_lines.append(f'<li>{list_item}</li>')
        else:
            if in_list:
                converted_lines.append('</ul>')
                in_list = False
            # Convert paragraphs (non-empty lines that aren't headers or lists)
            if line.strip() and not line.strip().startswith('<'):
                converted_lines.append(f'<p>{line.strip()}</p>')
            else:
                converted_lines.append(line)
    
    # Close any open list
    if in_list:
        converted_lines.append('</ul>')
    
    # Convert horizontal rules
    html_text = '\n'.join(converted_lines)
    html_text = re.sub(r'<p>---</p>', r'<hr>', html_text)
    
    return html_text


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
- Use markdown formatting (##, **, -, etc.) - it will be converted to HTML automatically
- ABSOLUTELY NO EMOJIS - Use only text, no symbols, no Unicode characters
- Strictly professional business writing style only

VULNERABILITY DATA:
{vuln_context}

Generate the enhanced blog content in markdown format:
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
            
            # Convert markdown to HTML for WordPress compatibility
            html_content = markdown_to_html(enhanced_content)
            
            # Parse the enhanced content into structured format
            first_line = enhanced_content.split('\n')[0].replace('#', '').strip()
            return {
                "enhanced_title": f"{first_line}",
                "enhanced_description": html_content,
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
        
        enhanced_desc = f"""<h2>Executive Summary</h2>
<p>{vuln.title}{affected_tools_text} has been identified with {vuln.severity.value.lower()} severity.</p>

<h2>Technical Details</h2>
<p>{vuln.description}</p>

<h2>Risk Assessment</h2>
<ul>
<li><strong>Severity</strong>: {vuln.severity.value}</li>
<li><strong>CVSS Score</strong>: {vuln.cvss_score or 'Not assessed'}</li>
<li><strong>Patch Status</strong>: {vuln.patch_status.value}</li>
<li><strong>Confidence Level</strong>: {vuln.confidence_score}/1.0</li>
</ul>

<h2>Affected Tools</h2>
{f"<ul>{''.join([f'<li>{tool.display_name} ({tool.vendor})</li>' for tool in vuln.affected_tools])}</ul>" if vuln.affected_tools else "<p>No specific tools identified</p>"}

<h2>Mitigation Guidance</h2>
<p>Monitor for patches and updates from affected vendors. Review your AI coding assistant configurations and consider additional security measures.</p>

<hr>
<p><em>This alert was generated by Kirin vulnerability intelligence system.</em></p>
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