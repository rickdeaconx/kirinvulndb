# Kirin VulnDB - Quick Start Guide

## 🚀 Fastest Way to Get Running

### Option 1: Simple Demo (No Database Required)

```bash
# Install basic dependencies
pip3 install fastapi uvicorn pydantic-settings

# Run the simple demo
python3 start_simple.py

# This will create and run minimal_app.py
```

**Access the demo at: http://localhost:8080**

### Option 2: Full System (With Database)

```bash
# 1. Install all dependencies
pip3 install -r requirements.txt

# 2. Start PostgreSQL (if you have it installed)
brew services start postgresql  # macOS
# or: sudo systemctl start postgresql  # Linux

# 3. Create database
createdb kirinvulndb

# 4. Initialize database
python3 scripts/init_db.py

# 5. Start the API server
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## 📋 What Each Option Provides

### Simple Demo (minimal_app.py)
- ✅ FastAPI server with health checks
- ✅ Demo vulnerability endpoints
- ✅ CORS enabled for frontend
- ✅ No database required
- ✅ Works immediately

**Endpoints:**
- `GET /` - Main info
- `GET /api/health` - Health check
- `GET /api/vulnerabilities/demo` - Sample vulnerabilities
- `GET /api/tools/demo` - Sample AI tools
- `GET /docs` - Interactive API documentation

### Full System
- ✅ Complete vulnerability database
- ✅ Real-time WebSocket updates
- ✅ Multi-source data collection
- ✅ React dashboard
- ✅ Kirin plugin APIs

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
pip3 install fastapi uvicorn pydantic-settings
```

### "ModuleNotFoundError: No module named 'pydantic_settings'"
```bash
pip3 install pydantic-settings
```

### Database Connection Issues
```bash
# Use the simple demo instead:
python3 start_simple.py
```

### Port 8080 Already in Use
```bash
# Kill process using port 8080
lsof -ti:8080 | xargs kill -9

# Or use different port
python3 -m uvicorn app.main:app --port 8081
```

## 🎯 Quick Tests

### Test 1: Basic Setup
```bash
python3 test_basic.py
```

### Test 2: API Health
```bash
curl http://localhost:8080/api/health
```

### Test 3: Demo Data
```bash
curl http://localhost:8080/api/vulnerabilities/demo
```

## 🌐 Frontend Setup (Optional)

```bash
cd frontend
npm install
npm start
```

The React dashboard will be available at http://localhost:3000

## 📊 Example API Responses

### Health Check
```json
GET /api/health
{
  "status": "healthy",
  "service": "Kirin VulnDB",
  "version": "1.0.0"
}
```

### Demo Vulnerabilities
```json
GET /api/vulnerabilities/demo
{
  "vulnerabilities": [
    {
      "id": "demo-001",
      "title": "Sample Critical Vulnerability in AI Code Completion",
      "severity": "CRITICAL",
      "cvss_score": 9.8,
      "affected_tools": ["cursor", "copilot"],
      "patch_status": "unpatched"
    }
  ],
  "total": 2
}
```

## 🔑 Key Features Working

- ✅ RESTful API with FastAPI
- ✅ Interactive documentation at `/docs`
- ✅ Health monitoring
- ✅ Demo data for testing
- ✅ CORS support for frontend integration
- ✅ Proper error handling
- ✅ JSON responses

## 🎉 Success Indicators

When working correctly, you should see:

1. **Server startup message**: "🚀 Starting Kirin Vulnerability Database..."
2. **Health check works**: `curl http://localhost:8080/api/health` returns JSON
3. **API docs load**: Visit http://localhost:8080/docs
4. **Demo data available**: Visit http://localhost:8080/api/vulnerabilities/demo

## 📞 Need Help?

If you're still having issues:

1. Run the diagnostic: `python3 test_basic.py`
2. Check the server logs for error messages
3. Verify Python version: `python3 --version` (needs 3.8+)
4. Try the minimal demo first: `python3 start_simple.py`

The system is designed to work even without external dependencies like PostgreSQL, Redis, or Kafka. The minimal version provides a solid foundation for testing and development.

---

🛡️ **Happy vulnerability monitoring!**