#!/bin/bash

echo "🚀 Kirin Vulnerability Database - Railway Deployment Script"
echo "=========================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}Installing Railway CLI...${NC}"
    npm install -g @railway/cli || {
        echo -e "${RED}Failed to install Railway CLI. Please install Node.js first.${NC}"
        echo "Visit: https://nodejs.org/"
        exit 1
    }
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo -e "${BLUE}Please log in to Railway:${NC}"
    railway login
fi

# Check if git repo is clean
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${YELLOW}You have uncommitted changes. Committing them now...${NC}"
    git add .
    git commit -m "🚀 Railway deployment configuration

- Added Dockerfile.simple for lightweight Railway deployment
- Configured railway.toml with production settings
- SQLite database for free tier compatibility
- 6-hour vulnerability monitoring with NVD API integration
- WordPress RSS feed ready at /api/rss/vulnerabilities.xml

🤖 Generated with [Claude Code](https://claude.ai/code)"
fi

# Push to GitHub
echo -e "${BLUE}Pushing to GitHub...${NC}"
git push origin main

# Initialize Railway project
echo -e "${BLUE}Setting up Railway project...${NC}"
railway init

# Set environment variables
echo -e "${BLUE}Setting environment variables...${NC}"
railway variables set PORT=8080
railway variables set DATABASE_URL="sqlite:///./kirinvulndb.db"
railway variables set NVD_API_KEY="d9b1e4b4-649a-4fac-93e5-fe808def98ec"
railway variables set API_SECRET_KEY="$(openssl rand -base64 32)"
railway variables set LOG_LEVEL="INFO"
railway variables set CVE_COLLECTION_INTERVAL="21600"  # 6 hours
railway variables set VENDOR_COLLECTION_INTERVAL="43200"  # 12 hours
railway variables set COMMUNITY_COLLECTION_INTERVAL="86400"  # 24 hours

# Deploy
echo -e "${BLUE}Deploying to Railway...${NC}"
railway up --detach

# Get deployment URL
sleep 10
RAILWAY_URL=$(railway status --json | jq -r '.deployments[0].url // "checking..."')

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${BLUE}🔗 Your Kirin VulnDB is live at:${NC}"
echo -e "${GREEN}   https://$RAILWAY_URL${NC}"
echo ""
echo -e "${BLUE}📡 WordPress RSS Feed:${NC}"
echo -e "${GREEN}   https://$RAILWAY_URL/api/rss/vulnerabilities.xml${NC}"
echo ""
echo -e "${BLUE}📊 API Documentation:${NC}"
echo -e "${GREEN}   https://$RAILWAY_URL/docs${NC}"
echo ""
echo -e "${BLUE}❤️  Health Check:${NC}"
echo -e "${GREEN}   https://$RAILWAY_URL/api/health${NC}"
echo ""
echo -e "${BLUE}🔧 Railway Dashboard:${NC}"
railway open
echo ""
echo -e "${YELLOW}⏱️  The system will start collecting AI vulnerabilities within 10 minutes${NC}"
echo -e "${YELLOW}📱 RSS feed updates every 6 hours with fresh vulnerabilities${NC}"