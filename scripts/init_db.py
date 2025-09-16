#!/usr/bin/env python3
"""
Database initialization script
Creates tables and populates initial data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.db.base import Base
from app.db.database import engine, SessionLocal
from app.models.tool import AITool
from app.models.vulnerability import Vulnerability, SeverityEnum, PatchStatusEnum, AttackVectorEnum
from app.core.config import settings
from datetime import datetime
import logging
import sqlite3
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def load_seed_data():
    """Load seed data from SQL dump if database is empty"""
    try:
        # Check if we have historical data already
        with SessionLocal() as db:
            vuln_count = db.query(Vulnerability).count()
            if vuln_count > 2:  # More than sample data
                logger.info(f"Database already has {vuln_count} vulnerabilities, skipping seed data")
                return
        
        # Check if seed data file exists
        seed_file = "/app/seed_data.sql"
        if not os.path.exists(seed_file):
            seed_file = "seed_data.sql"  # Try local path
            
        if os.path.exists(seed_file):
            logger.info("Loading historical vulnerability data from seed file...")
            
            # Get database URL from settings
            db_url = str(engine.url)
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")
                
                # Load seed data into SQLite
                conn = sqlite3.connect(db_path)
                with open(seed_file, 'r') as f:
                    conn.executescript(f.read())
                conn.close()
                
                logger.info("Historical vulnerability data loaded successfully!")
            else:
                logger.info("Non-SQLite database, skipping seed data import")
        else:
            logger.info("No seed data file found, creating sample data only")
            
    except Exception as e:
        logger.error(f"Failed to load seed data: {e}")
        logger.info("Continuing with sample data creation...")


def populate_initial_tools():
    """Populate initial AI tools data"""
    
    with SessionLocal() as db:
        # Check if tools already exist (for Railway pre-populated database)
        existing_count = db.query(AITool).count()
        if existing_count > 0:
            logger.info(f"AI tools already populated ({existing_count} tools found)")
            return
    
    logger.info("Populating initial AI tools...")
    
    tools_data = [
        {
            "name": "cursor",
            "display_name": "Cursor",
            "vendor": "Cursor Inc.",
            "description": "AI-powered code editor with built-in pair programming features",
            "current_version": "0.8.3",
            "supported_languages": ["python", "javascript", "typescript", "react", "go", "rust"],
            "platform_support": ["windows", "macos", "linux"],
            "security_contact": "security@cursor.ai",
            "security_policy_url": "https://cursor.ai/security",
            "is_actively_monitored": True,
            "monitoring_priority": 1.0
        },
        {
            "name": "github_copilot",
            "display_name": "GitHub Copilot",
            "vendor": "GitHub/Microsoft",
            "description": "AI pair programmer that helps write code faster",
            "current_version": "1.2.6",
            "supported_languages": ["python", "javascript", "typescript", "go", "ruby", "java", "c++"],
            "platform_support": ["vscode", "jetbrains", "neovim", "visual_studio"],
            "security_contact": "security@github.com",
            "security_policy_url": "https://github.com/github/copilot-docs/blob/main/SECURITY.md",
            "vulnerability_disclosure_url": "https://bounty.github.com",
            "is_actively_monitored": True,
            "monitoring_priority": 1.0
        },
        {
            "name": "amazon_codewhisperer",
            "display_name": "Amazon CodeWhisperer",
            "vendor": "Amazon Web Services",
            "description": "Machine learning powered code generator",
            "current_version": "2.1.0",
            "supported_languages": ["python", "java", "javascript", "typescript", "c#", "go"],
            "platform_support": ["vscode", "jetbrains", "aws_toolkit"],
            "security_contact": "aws-security@amazon.com",
            "security_policy_url": "https://aws.amazon.com/security/",
            "is_actively_monitored": True,
            "monitoring_priority": 0.9
        },
        {
            "name": "tabnine",
            "display_name": "Tabnine",
            "vendor": "Tabnine Ltd.",
            "description": "AI assistant for code completion",
            "current_version": "4.15.2",
            "supported_languages": ["python", "javascript", "java", "typescript", "go", "php", "rust"],
            "platform_support": ["vscode", "jetbrains", "sublime", "vim", "emacs"],
            "security_contact": "security@tabnine.com",
            "security_policy_url": "https://www.tabnine.com/security",
            "is_actively_monitored": True,
            "monitoring_priority": 0.8
        },
        {
            "name": "codeium",
            "display_name": "Codeium",
            "vendor": "Exafunction Inc.",
            "description": "Free AI-powered code completion",
            "current_version": "1.6.12",
            "supported_languages": ["python", "javascript", "typescript", "java", "go", "rust", "c++"],
            "platform_support": ["vscode", "jetbrains", "vim", "emacs", "chrome"],
            "security_contact": "security@codeium.com",
            "is_actively_monitored": True,
            "monitoring_priority": 0.7
        },
        {
            "name": "replit_ghostwriter",
            "display_name": "Replit Ghostwriter",
            "vendor": "Replit Inc.",
            "description": "AI pair programmer for Replit IDE",
            "supported_languages": ["python", "javascript", "java", "go", "rust", "c++", "html", "css"],
            "platform_support": ["replit"],
            "security_contact": "security@replit.com",
            "is_actively_monitored": True,
            "monitoring_priority": 0.6
        },
        {
            "name": "sourcegraph_cody",
            "display_name": "Sourcegraph Cody",
            "vendor": "Sourcegraph Inc.",
            "description": "AI coding assistant that knows your codebase",
            "supported_languages": ["python", "javascript", "typescript", "go", "java", "c++"],
            "platform_support": ["vscode", "jetbrains"],
            "security_contact": "security@sourcegraph.com",
            "security_policy_url": "https://sourcegraph.com/security",
            "is_actively_monitored": True,
            "monitoring_priority": 0.7
        },
        {
            "name": "jetbrains_ai_assistant",
            "display_name": "JetBrains AI Assistant",
            "vendor": "JetBrains",
            "description": "AI-powered coding assistant for JetBrains IDEs",
            "supported_languages": ["java", "kotlin", "python", "javascript", "go", "rust"],
            "platform_support": ["intellij", "pycharm", "webstorm", "goland"],
            "security_contact": "security@jetbrains.com",
            "security_policy_url": "https://www.jetbrains.com/security/",
            "is_actively_monitored": True,
            "monitoring_priority": 0.8
        }
    ]
    
    with SessionLocal() as db:
        for tool_data in tools_data:
            existing = db.query(AITool).filter(AITool.name == tool_data["name"]).first()
            if not existing:
                tool = AITool(**tool_data)
                db.add(tool)
                logger.info(f"Added tool: {tool_data['name']}")
            else:
                logger.info(f"Tool already exists: {tool_data['name']}")
        
        db.commit()
    
    logger.info("Initial AI tools populated successfully")


def create_sample_vulnerabilities():
    """Create some sample vulnerabilities for testing"""
    
    with SessionLocal() as db:
        # Check if vulnerabilities already exist (for Railway pre-populated database)
        existing_count = db.query(Vulnerability).count()
        if existing_count > 2:  # More than just sample data
            logger.info(f"Vulnerabilities already populated ({existing_count} vulnerabilities found)")
            return
    
    logger.info("Creating sample vulnerabilities...")
    
    sample_vulns = [
        {
            "vulnerability_id": "sample-001",
            "title": "Sample Remote Code Execution in AI Code Completion",
            "description": "A critical vulnerability that allows remote code execution through malicious code suggestions",
            "severity": SeverityEnum.CRITICAL,
            "cvss_score": 9.8,
            "discovery_date": datetime.utcnow(),
            "attack_vectors": [AttackVectorEnum.RCE],
            "patch_status": PatchStatusEnum.UNPATCHED,
            "source": "sample",
            "confidence_score": 1.0,
            "tags": ["sample", "rce", "critical"]
        },
        {
            "vulnerability_id": "sample-002", 
            "title": "Sample Prompt Injection Vulnerability",
            "description": "AI assistant vulnerable to prompt injection attacks that can leak sensitive information",
            "severity": SeverityEnum.HIGH,
            "cvss_score": 7.5,
            "discovery_date": datetime.utcnow(),
            "attack_vectors": [AttackVectorEnum.PROMPT_INJECTION],
            "patch_status": PatchStatusEnum.PATCH_AVAILABLE,
            "source": "sample",
            "confidence_score": 0.9,
            "tags": ["sample", "prompt-injection", "high"]
        }
    ]
    
    with SessionLocal() as db:
        # Get some tools to associate with vulnerabilities
        cursor_tool = db.query(AITool).filter(AITool.name == "cursor").first()
        copilot_tool = db.query(AITool).filter(AITool.name == "github_copilot").first()
        
        for vuln_data in sample_vulns:
            existing = db.query(Vulnerability).filter(
                Vulnerability.vulnerability_id == vuln_data["vulnerability_id"]
            ).first()
            
            if not existing:
                vuln = Vulnerability(**vuln_data)
                
                # Associate with tools
                if cursor_tool:
                    vuln.affected_tools.append(cursor_tool)
                if copilot_tool and vuln_data["vulnerability_id"] == "sample-002":
                    vuln.affected_tools.append(copilot_tool)
                
                db.add(vuln)
                logger.info(f"Added sample vulnerability: {vuln_data['vulnerability_id']}")
            else:
                logger.info(f"Sample vulnerability already exists: {vuln_data['vulnerability_id']}")
        
        db.commit()
    
    logger.info("Sample vulnerabilities created successfully")


def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    try:
        # Create tables
        create_tables()
        
        # Try to load historical data first
        load_seed_data()
        
        # Populate initial data (only if not already present)
        populate_initial_tools()
        
        # Create sample vulnerabilities for testing (only if no historical data)
        create_sample_vulnerabilities()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


if __name__ == "__main__":
    main()