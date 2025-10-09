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


def create_seo_title(original_title: str) -> str:
    """Create SEO-friendly title under 60 characters"""
    if len(original_title) <= 60:
        return original_title
    
    # Remove common filler words
    filler_words = ['via', 'through', 'using', 'with', 'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'for', 'by']
    words = original_title.split()
    
    # Try removing filler words first
    filtered_words = [word for word in words if word.lower() not in filler_words]
    filtered_title = ' '.join(filtered_words)
    
    if len(filtered_title) <= 60:
        return filtered_title
    
    # If still too long, try keeping only the most important words
    # Keep first part before colon or dash if exists
    if ':' in filtered_title:
        main_part = filtered_title.split(':')[0].strip()
        if len(main_part) <= 60:
            return main_part
    
    if ' - ' in filtered_title:
        main_part = filtered_title.split(' - ')[0].strip()
        if len(main_part) <= 60:
            return main_part
    
    # Last resort: truncate at word boundary
    words_to_keep = []
    current_length = 0
    for word in filtered_words:
        if current_length + len(word) + 1 <= 57:  # +1 for space, 57 to leave room for ...
            words_to_keep.append(word)
            current_length += len(word) + 1
        else:
            break
    
    if words_to_keep:
        return ' '.join(words_to_keep) + "..."
    
    # Fallback
    return original_title[:57] + "..."

def create_slug(title: str) -> str:
    """Create 3-5 word slug without filler words"""
    # Remove punctuation and convert to lowercase
    import re
    clean_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
    
    # Remove filler words
    filler_words = ['via', 'through', 'using', 'with', 'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'for', 'by', 'to', 'from', 'of']
    words = [word for word in clean_title.split() if word not in filler_words]
    
    # Take first 3-5 most meaningful words
    slug_words = words[:5] if len(words) > 3 else words[:3]
    return '-'.join(slug_words)

def create_meta_description(summary_text: str, title: str) -> str:
    """Create meta description under 150 characters"""
    # Extract first sentence or meaningful part of summary
    sentences = summary_text.split('. ')
    if sentences:
        desc = sentences[0]
        if len(desc) > 145:
            desc = desc[:145] + "..."
        elif len(desc) < 100 and len(sentences) > 1:
            # Add second sentence if first is too short
            second = sentences[1]
            combined = f"{desc}. {second}"
            if len(combined) <= 145:
                desc = combined
            else:
                desc = combined[:145] + "..."
        return desc
    return title[:145] + "..." if len(title) > 145 else title

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

Create content with these exact sections:
1. **Summary**: Clearly identify the SPECIFIC vulnerability type and what makes it unique (avoid generic phrases like "has been identified" - be specific about what the vulnerability actually IS)
2. **Overview**: Context about what this vulnerability affects and why it matters  
3. **Details**: Technical explanation of how the vulnerability works and its implications
4. **Conclusion**: Key takeaways and recommended actions for developers

CRITICAL TITLE REQUIREMENTS:
- Create a concise, SEO-friendly title under 60 characters
- Remove unnecessary words like "and", "with", "via", "through" when possible
- Focus on the core vulnerability concept
- Example: "Jailbreaking LLMs via Semantically Relevant Nested Scenarios with Targeted Toxic Knowledge" becomes "Jailbreaking LLMs with Targeted Toxic Knowledge"

SUMMARY REQUIREMENTS:
- Start with the specific vulnerability type (e.g. "This prompt injection attack allows...", "This jailbreaking technique enables...", "This code execution vulnerability permits...")
- Clearly explain what the attacker can achieve
- Avoid repetitive phrases like "vulnerability has been identified" - be specific about the actual security flaw

Guidelines:
- Write in a professional, informative tone
- Focus on practical implications for developers
- Highlight cybersecurity concerns specific to AI coding assistants
- Keep technical details accessible but thorough
- Emphasize actionable guidance in the conclusion
- Use markdown formatting (##, **, -, etc.) - it will be converted to HTML automatically
- ABSOLUTELY NO EMOJIS - Use only text, no symbols, no Unicode characters
- Strictly professional business writing style only
- Each section should be substantial (2-4 paragraphs each)

VULNERABILITY DATA:
{vuln_context}

Generate the enhanced blog content in markdown format with Summary, Overview, Details, and Conclusion sections:
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
            
            # Create SEO-optimized title and slug
            seo_title = create_seo_title(first_line)
            slug = create_slug(seo_title)
            
            # Extract summary for meta description
            summary_match = re.search(r'## Summary\s*\n(.*?)\n\n', enhanced_content, re.DOTALL)
            summary_text = summary_match.group(1) if summary_match else first_line
            meta_description = create_meta_description(summary_text, seo_title)
            
            return {
                "enhanced_title": seo_title,
                "enhanced_description": html_content,
                "slug": slug,
                "meta_description": meta_description,
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
        
        # Create optimized title and metadata
        seo_title = create_seo_title(vuln.title)
        slug = create_slug(seo_title)
        
        # Identify vulnerability type for better summary
        vuln_type = "security vulnerability"
        if "injection" in vuln.description.lower():
            vuln_type = "injection attack"
        elif "jailbreak" in vuln.description.lower():
            vuln_type = "jailbreaking technique"
        elif "bypass" in vuln.description.lower():
            vuln_type = "security bypass"
        elif "execution" in vuln.description.lower():
            vuln_type = "code execution vulnerability"
        
        enhanced_desc = f"""<h2>Summary</h2>
<p>This {vuln_type} allows attackers to compromise AI coding assistants{affected_tools_text}. The vulnerability enables unauthorized access to sensitive data and potential manipulation of AI-generated code, posing significant risks to development workflows.</p>

<h2>Overview</h2>
<p>This vulnerability affects AI-powered development tools that assist with code generation and development tasks. The issue has been classified with a CVSS score of {vuln.cvss_score or 'pending assessment'} and is currently in {vuln.patch_status.value.replace('_', ' ').lower()} status.</p>
<p>AI coding assistants have become integral to modern software development, making security vulnerabilities in these tools particularly concerning for development teams and organizations.</p>

<h2>Details</h2>
<p>{vuln.description}</p>
<p>The vulnerability presents the following risk characteristics:</p>
<ul>
<li><strong>Severity Level</strong>: {vuln.severity.value}</li>
<li><strong>CVSS Score</strong>: {vuln.cvss_score or 'Under assessment'}</li>
<li><strong>Current Status</strong>: {vuln.patch_status.value.replace('_', ' ').title()}</li>
<li><strong>Detection Confidence</strong>: {vuln.confidence_score * 100:.0f}%</li>
</ul>
{f"<p><strong>Affected Tools:</strong></p><ul>{''.join([f'<li>{tool.display_name} ({tool.vendor})</li>' for tool in vuln.affected_tools])}</ul>" if vuln.affected_tools else "<p>Specific tool impacts are under investigation.</p>"}

<h2>Conclusion</h2>
<p>Development teams using AI coding assistants should monitor this vulnerability closely and implement appropriate security measures. Organizations should review their AI tool usage policies and ensure proper security controls are in place.</p>
<p>Key recommendations include monitoring for patches and updates from affected vendors, reviewing AI coding assistant configurations, and considering additional security measures for development environments. Stay informed about updates to this vulnerability through official security channels.</p>

<hr>
<p><em>This vulnerability analysis was generated by the <strong><a href="https://getkirin.com" target="_blank">Kirin</a></strong> intelligence system.</em></p>
"""
        
        # Create meta description
        summary_text = f"This {vuln_type} allows attackers to compromise AI coding assistants{affected_tools_text}."
        meta_description = create_meta_description(summary_text, seo_title)
        
        return {
            "enhanced_title": seo_title,
            "enhanced_description": enhanced_desc,
            "slug": slug,
            "meta_description": meta_description,
            "blog_format": True,
            "enhanced_by_llm": False,
            "enhancement_timestamp": "2024-01-01T00:00:00Z"
        }


# Global instance
llm_enhancer = LLMVulnerabilityEnhancer()