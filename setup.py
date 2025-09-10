#!/usr/bin/env python3
"""
Quick setup script for Kirin Vulnerability Database
This will install dependencies and perform basic setup
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 Setting up Kirin Vulnerability Database...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version} detected")
    
    # Install Python dependencies
    print("\n📦 Installing Python dependencies...")
    if not run_command("pip install -r requirements.txt", "Installing Python packages"):
        print("❌ Failed to install dependencies. Trying with pip3...")
        if not run_command("pip3 install -r requirements.txt", "Installing Python packages with pip3"):
            print("❌ Could not install dependencies. Please install manually:")
            print("pip3 install -r requirements.txt")
            return False
    
    # Create .env file from template
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            run_command("cp .env.example .env", "Creating environment file")
        else:
            print("⚠️  .env.example not found, creating basic .env")
            with open('.env', 'w') as f:
                f.write("""# Basic configuration for development
DEBUG=True
LOG_LEVEL=INFO
DATABASE_URL=postgresql://kirinuser:kirinpassword@localhost:5432/kirinvulndb
REDIS_URL=redis://localhost:6379
""")
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    print("\n🎉 Basic setup completed!")
    print("\nNext steps:")
    print("1. Start PostgreSQL: brew services start postgresql (macOS) or equivalent")
    print("2. Create database: createdb kirinvulndb")
    print("3. Initialize database: python3 scripts/init_db.py")
    print("4. Start the API: python3 -m uvicorn app.main:app --reload")
    print("\nOr run the full system: python3 scripts/run_system.py")

if __name__ == "__main__":
    main()