
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
