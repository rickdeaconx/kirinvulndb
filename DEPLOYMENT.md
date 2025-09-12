# 🚀 Deployment Guide - Kirin Vulnerability Database

## 🌟 **Recommended: Render.com (Free)**

### One-Click Deploy to Render:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/rickdeaconx/kirinvulndb)

### Manual Render Deployment:

1. **Go to**: https://render.com
2. **Click "New +"** → "Web Service"
3. **Connect GitHub**: Select `rickdeaconx/kirinvulndb`
4. **Configure**:
   - **Name**: `kirin-vulndb`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `Dockerfile.simple`
   - **Plan**: Free
5. **Environment Variables** (click "Add Environment Variable"):
   ```
   DATABASE_URL = sqlite:///./kirinvulndb.db
   NVD_API_KEY = d9b1e4b4-649a-4fac-93e5-fe808def98ec
   LOG_LEVEL = INFO
   CVE_COLLECTION_INTERVAL = 21600
   ```
6. **Deploy**

---

## 🚂 **Railway Deployment (If CLI works)**

### Requirements:
- Node.js installed
- Railway CLI: `npm install -g @railway/cli`

### Steps:
```bash
# 1. Login to Railway
railway login

# 2. Initialize project
railway init

# 3. Set environment variables
railway variables set DATABASE_URL="sqlite:///./kirinvulndb.db"
railway variables set NVD_API_KEY="d9b1e4b4-649a-4fac-93e5-fe808def98ec"
railway variables set LOG_LEVEL="INFO"

# 4. Deploy
railway up
```

---

## 🌐 **Alternative: Fly.io**

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy
flyctl auth login
flyctl launch --dockerfile Dockerfile.simple
flyctl deploy
```

---

## 🐳 **Local Docker Deployment**

```bash
# Build and run locally
docker build -f Dockerfile.simple -t kirin-vulndb .
docker run -p 8080:8080 \
  -e DATABASE_URL="sqlite:///./kirinvulndb.db" \
  -e NVD_API_KEY="d9b1e4b4-649a-4fac-93e5-fe808def98ec" \
  kirin-vulndb
```

---

## 🔗 **After Deployment - What You Get:**

### Access Points:
- **📊 API Docs**: `https://your-app.onrender.com/docs`
- **📡 RSS Feed**: `https://your-app.onrender.com/api/rss/vulnerabilities.xml`
- **❤️ Health Check**: `https://your-app.onrender.com/api/health`
- **📈 Stats**: `https://your-app.onrender.com/api/vulnerabilities/stats`

### Features:
- ✅ **6-hour vulnerability monitoring** with NVD API
- ✅ **WordPress RSS integration** ready
- ✅ **Real-time AI vulnerability detection**
- ✅ **Cursor IDE prioritization**
- ✅ **110+ vulnerabilities** from 33+ sources
- ✅ **Auto-restart** on failures

### WordPress Integration:
```
RSS Feed URL: https://your-app.onrender.com/api/rss/vulnerabilities.xml
Update Frequency: Every 6 hours
Content: AI coding vulnerabilities with full descriptions
```

---

## 🚨 **Troubleshooting**

### Railway "Train not arrived" Error:
- Build still in progress (wait 5-10 minutes)
- Check Railway dashboard for build logs
- Ensure environment variables are set
- Verify Dockerfile.simple exists

### Common Issues:
- **Port errors**: Railway uses dynamic ports via `$PORT` env var
- **Database**: SQLite creates file automatically
- **Memory limits**: Free tiers have 512MB RAM limits

---

## 💡 **Recommended Approach:**

1. **Try Render first** - has best free tier and one-click deploy
2. **Railway backup** - if you can use CLI in your terminal
3. **Fly.io alternative** - good performance, slightly more complex

**Choose the platform that works best for your setup!**