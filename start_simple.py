#!/usr/bin/env python3
"""
Simple starter script that handles common issues
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic_settings']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} - missing")
    
    if missing:
        print(f"\n📦 Installing missing packages...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing + ['redis', 'psycopg2-binary'], check=True)
            print("✅ Packages installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages automatically")
            print("Please run: pip install fastapi uvicorn sqlalchemy pydantic-settings redis psycopg2-binary")
            return False
    
    return True

def setup_minimal_database():
    """Set up a minimal in-memory database for testing"""
    print("🗄️  Setting up minimal database...")
    
    # Modify config to use SQLite for testing
    config_path = Path("app/core/config.py")
    if config_path.exists():
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Replace PostgreSQL URL with SQLite for testing
        content = content.replace(
            'DATABASE_URL: str = "postgresql://kirinuser:kirinpassword@localhost:5432/kirinvulndb"',
            'DATABASE_URL: str = "sqlite:///./test_kirinvulndb.db"'
        )
        
        with open(config_path, 'w') as f:
            f.write(content)
        
        print("✅ Config updated to use SQLite")
    
    return True

def create_minimal_app():
    """Create a minimal working version of the app"""
    print("🚀 Creating minimal app...")
    
    # Create a simple standalone version
    minimal_app_code = '''
import sys
import os
sys.path.insert(0, os.getcwd())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Simple logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal app
app = FastAPI(
    title="Kirin Vulnerability Database",
    description="Real-time vulnerability monitoring for AI coding assistants", 
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "Kirin Vulnerability Database",
        "version": "1.0.0",
        "status": "running",
        "message": "Welcome to Kirin VulnDB - AI Code Security Monitoring"
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "Kirin VulnDB",
        "version": "1.0.0"
    }

@app.get("/api/vulnerabilities/demo")
async def demo_vulnerabilities():
    """Demo endpoint with sample data"""
    return {
        "vulnerabilities": [
            {
                "id": "demo-001",
                "title": "Sample Critical Vulnerability in AI Code Completion",
                "severity": "CRITICAL", 
                "cvss_score": 9.8,
                "affected_tools": ["cursor", "copilot"],
                "description": "Demo vulnerability for testing purposes",
                "patch_status": "unpatched"
            },
            {
                "id": "demo-002", 
                "title": "Sample Prompt Injection Vulnerability",
                "severity": "HIGH",
                "cvss_score": 7.5,
                "affected_tools": ["tabnine"],
                "description": "Sample prompt injection vulnerability",
                "patch_status": "patch_available"
            }
        ],
        "total": 2
    }

@app.get("/api/tools/demo")
async def demo_tools():
    """Demo endpoint with sample tools"""
    return {
        "tools": [
            {
                "name": "cursor",
                "display_name": "Cursor",
                "vendor": "Cursor Inc.",
                "total_vulnerabilities": 5,
                "critical_vulnerabilities": 1
            },
            {
                "name": "github_copilot", 
                "display_name": "GitHub Copilot",
                "vendor": "GitHub/Microsoft",
                "total_vulnerabilities": 3,
                "critical_vulnerabilities": 0
            }
        ],
        "total": 2
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Kirin Vulnerability Database...")
    print("📊 Dashboard will be available at: http://localhost:8080")
    print("🔧 API documentation at: http://localhost:8080/docs")
    print("❤️  Health check at: http://localhost:8080/api/health")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
'''
    
    with open('minimal_app.py', 'w') as f:
        f.write(minimal_app_code)
    
    print("✅ Minimal app created as 'minimal_app.py'")
    return True

def main():
    print("🛠️  Kirin VulnDB - Simple Setup & Start")
    print("=" * 50)
    
    try:
        # Step 1: Check dependencies
        if not check_dependencies():
            return False
        
        # Step 2: Create minimal app
        create_minimal_app()
        
        print("\n🎉 Setup completed successfully!")
        print("\n📋 What was created:")
        print("  • minimal_app.py - Standalone FastAPI application")
        print("  • Basic health and demo endpoints")
        print("  • CORS enabled for frontend access")
        
        print("\n🚀 To start the server:")
        print("  python3 minimal_app.py")
        
        print("\n🔗 Access points:")
        print("  • Main: http://localhost:8080")
        print("  • Health: http://localhost:8080/api/health")  
        print("  • Demo Vulnerabilities: http://localhost:8080/api/vulnerabilities/demo")
        print("  • Demo Tools: http://localhost:8080/api/tools/demo")
        print("  • API Docs: http://localhost:8080/docs")
        
        # Ask if user wants to start now
        response = input("\n❓ Start the server now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            print("\n🚀 Starting server...")
            subprocess.run([sys.executable, 'minimal_app.py'])
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    main()