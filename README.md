# 🛡️ Kirin Vulnerability Database - Cursor AI Security

**Real-time vulnerability monitoring system specifically designed for Cursor IDE and AI coding assistants**

## Overview

The Kirin Vulnerability Database is a comprehensive security monitoring platform that continuously tracks vulnerabilities across ALL major AI coding assistants including Cursor, GitHub Copilot, Amazon CodeWhisperer, Tabnine, Codeium, and more. It provides real-time alerts, automated remediation suggestions, and seamless integration with security workflows.

### Key Features

- 🔍 **Multi-Source Intelligence**: Aggregates from CVE databases, vendor advisories, GitHub security alerts, and community sources
- ⚡ **Real-Time Monitoring**: WebSocket-based live updates with sub-second latency
- 🤖 **AI-Powered Analysis**: Intelligent vulnerability classification and risk assessment
- 🔧 **Automated Remediation**: Kirin plugin integration for automatic vulnerability fixes
- 📊 **Rich Dashboard**: React-based monitoring interface with charts and analytics
- 🔌 **Plugin Architecture**: Extensible system with Kirin Cursor plugin integration
- 🚀 **High Performance**: Kafka-based streaming with Redis caching
- 📈 **Analytics & Reporting**: Comprehensive metrics and trend analysis

## Architecture

```mermaid
graph TB
    A[CVE/NVD APIs] --> D[Collection Engine]
    B[Vendor APIs] --> D
    C[Community Sources] --> D
    D --> E[Kafka Stream]
    E --> F[PostgreSQL + TimescaleDB]
    E --> G[Redis Cache]
    F --> H[FastAPI Backend]
    G --> H
    H --> I[React Dashboard]
    H --> J[WebSocket Real-time]
    H --> K[Kirin Plugin API]
    K --> L[Cursor Plugin]
```

### Technology Stack

- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL 16 with TimescaleDB extension
- **Caching**: Redis 7.x
- **Streaming**: Apache Kafka
- **Search**: Elasticsearch (optional)
- **Frontend**: React 18 with Material-UI
- **Background Tasks**: Celery with Redis broker
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker + Kubernetes ready

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/kirinvulndb.git
cd kirinvulndb

# Run the automated setup script
python scripts/run_system.py
```

This will:
- Start all infrastructure services (PostgreSQL, Redis, Kafka)
- Initialize the database with sample data
- Start the API server and background workers
- Launch the React dashboard
- Run health checks

### Option 2: Manual Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 3. Start infrastructure services
docker-compose up -d postgres redis kafka elasticsearch

# 4. Initialize database
python scripts/init_db.py

# 5. Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# 6. Start background workers
celery -A app.celery_app worker --loglevel=info

# 7. Start the frontend (in another terminal)
cd frontend
npm install
npm start
```

### Option 3: Docker (Full Stack)

```bash
# Start the entire stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the stack
docker-compose down
```

## Access Points

After startup, you can access:

- 📊 **Dashboard**: http://localhost:3000
- 🔧 **API Documentation**: http://localhost:8080/docs
- 💾 **API Base**: http://localhost:8080/api
- 🔌 **Kirin Plugin API**: http://localhost:8080/api/kirin
- ❤️ **Health Check**: http://localhost:8080/api/health
- 📈 **Metrics**: http://localhost:9090 (Prometheus)
- 📋 **Logs**: http://localhost:3001 (Grafana)

## API Documentation

### Core Endpoints

#### Vulnerabilities API
```http
GET /api/vulnerabilities/latest
GET /api/vulnerabilities/critical
GET /api/vulnerabilities/by-tool/{tool_name}
GET /api/vulnerabilities/search?q={query}
GET /api/vulnerabilities/trending
GET /api/vulnerabilities/stats
```

#### Tools API
```http
GET /api/tools
GET /api/tools/{tool_name}
GET /api/tools/{tool_name}/vulnerabilities
```

#### Alerts API
```http
GET /api/alerts
GET /api/alerts/critical
POST /api/alerts/{alert_id}/acknowledge
POST /api/alerts/{alert_id}/resolve
```

#### Real-time WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8080/api/ws/vulnerabilities');
ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log('Vulnerability update:', update);
};
```

### Kirin Plugin API

The Kirin Plugin API provides specialized endpoints for the Kirin Cursor plugin:

#### Get Vulnerability Feed
```http
GET /api/kirin/vulnerabilities/feed
```
**Query Parameters:**
- `since`: ISO timestamp for incremental updates
- `tools`: Comma-separated tool names
- `severity`: Minimum severity level
- `unpatched_only`: Boolean, default true

**Response:**
```json
{
    "vulnerabilities": [...],
    "total_count": 42,
    "last_updated": "2025-01-16T10:30:00Z",
    "next_update_eta": "2025-01-16T10:35:00Z"
}
```

#### Request Remediation
```http
POST /api/kirin/remediation/request
```
**Body:**
```json
{
    "vulnerability_id": "nvd-CVE-2025-12345",
    "context": {
        "project_type": "typescript",
        "environment": "development"
    },
    "priority": "high"
}
```

#### Apply Security Policy
```http
POST /api/kirin/policy/apply
```
**Body:**
```json
{
    "request_id": "req_123",
    "vulnerability_ids": ["vuln_1", "vuln_2"],
    "context": {
        "user_id": "dev_001",
        "project_id": "proj_abc"
    }
}
```

#### Check Tool Compatibility
```http
GET /api/kirin/tools/compatibility?tool_name=cursor&tool_version=0.8.3
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/kirinvulndb

# Redis
REDIS_URL=redis://localhost:6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# External APIs
NVD_API_KEY=your_nvd_api_key
GITHUB_TOKEN=your_github_token

# Collection Intervals (seconds)
CVE_COLLECTION_INTERVAL=300
VENDOR_COLLECTION_INTERVAL=600
COMMUNITY_COLLECTION_INTERVAL=3600
```

### Monitored AI Tools

The system actively monitors these AI coding assistants:

- **Cursor** - AI-powered code editor
- **GitHub Copilot** - AI pair programmer
- **Amazon CodeWhisperer** - ML-powered code generator
- **Tabnine** - AI assistant for code completion
- **Codeium** - Free AI-powered code acceleration
- **Replit Ghostwriter** - AI pair programmer for Replit
- **Sourcegraph Cody** - AI coding assistant
- **JetBrains AI Assistant** - AI-powered coding for JetBrains IDEs

## Development

### Project Structure

```
kirinvulndb/
├── app/
│   ├── api/              # FastAPI route handlers
│   ├── collectors/       # Vulnerability data collectors
│   ├── core/            # Core configuration and utilities
│   ├── db/              # Database models and connection
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic models
│   ├── services/        # Business logic services
│   ├── tasks/           # Celery background tasks
│   └── utils/           # Utility functions
├── frontend/            # React dashboard
├── scripts/             # Management and setup scripts
├── tests/              # Test suites
├── monitoring/         # Prometheus/Grafana configs
└── docker-compose.yml  # Container orchestration
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app tests/

# Run specific test file
python -m pytest tests/test_collectors.py

# Test collectors (integration tests)
python scripts/test_collectors.py
```

### Adding New Data Sources

1. Create a new collector in `app/collectors/`:
```python
from app.collectors.base_collector import BaseCollector

class MyCollector(BaseCollector):
    async def collect_vulnerabilities(self, since=None):
        # Implementation
        pass
    
    def parse_vulnerability(self, raw_data):
        # Implementation
        pass
```

2. Register in `collector_manager.py`:
```python
self.collectors.append(MyCollector())
```

### API Rate Limits

Default rate limits:
- **General API**: 1000 requests/hour per IP
- **Kirin Plugin API**: 10000 requests/hour per API key
- **WebSocket**: 10000 connections per server

## Deployment

### Production Deployment

1. **Environment Setup**:
```bash
# Set production environment
export ENVIRONMENT=production

# Configure secrets
export DATABASE_PASSWORD=secure_password
export API_SECRET_KEY=super-secret-key
export REDIS_PASSWORD=redis_password
```

2. **Database Setup**:
```bash
# Run migrations
alembic upgrade head

# Create production data
python scripts/init_db.py --production
```

3. **Service Deployment**:
```bash
# Build and deploy with Docker
docker-compose -f docker-compose.prod.yml up -d

# Or deploy to Kubernetes
kubectl apply -f k8s/
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl create namespace kirinvulndb
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/database.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/frontend.yaml
```

### Monitoring Setup

```bash
# Deploy monitoring stack
kubectl apply -f monitoring/prometheus/
kubectl apply -f monitoring/grafana/

# Access Grafana dashboard
kubectl port-forward svc/grafana 3001:3000
# Visit: http://localhost:3001
```

## Security Considerations

### API Security
- JWT-based authentication for sensitive endpoints
- API key authentication for plugin integrations
- Rate limiting and DDoS protection
- Input validation and sanitization

### Data Security
- Encryption at rest for sensitive vulnerability data
- TLS encryption for all network communication
- Secure credential management with environment variables
- Regular security audits and updates

### Plugin Security
- Signed requests for plugin communications
- Sandbox execution for automated remediation
- Audit logging for all plugin actions
- Permission-based access control

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

3. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

4. Set up pre-commit hooks:
```bash
pre-commit install
```

5. Run tests to ensure everything works:
```bash
python -m pytest
```

### Coding Standards

- **Python**: Follow PEP 8, use Black for formatting
- **TypeScript**: Use ESLint and Prettier
- **Git**: Conventional Commits format
- **Documentation**: Docstrings for all public functions

### Submitting Changes

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make changes and add tests
3. Ensure tests pass: `python -m pytest`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Create a Pull Request

## Troubleshooting

### Common Issues

**Database Connection Failed**:
```bash
# Check PostgreSQL status
brew services list | grep postgresql

# Restart if needed
brew services restart postgresql
```

**Redis Connection Issues**:
```bash
# Check Redis status
redis-cli ping

# Start Redis if needed
redis-server --daemonize yes
```

**Kafka Issues**:
```bash
# Check if Kafka is running
jps | grep Kafka

# Start Kafka (after Zookeeper)
kafka-server-start.sh config/server.properties
```

**Frontend Won't Start**:
```bash
# Clear cache and reinstall
rm -rf frontend/node_modules
cd frontend && npm install
npm start
```

### Logs and Debugging

```bash
# API server logs
tail -f logs/kirinvulndb_$(date +%Y%m%d).log

# Database logs
tail -f /usr/local/var/log/postgresql@16.log

# Docker container logs
docker-compose logs -f api
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📧 **Email**: support@kirinvulndb.com
- 💬 **Discord**: [KirinVulnDB Community](https://discord.gg/kirinvulndb)
- 📖 **Documentation**: [https://docs.kirinvulndb.com](https://docs.kirinvulndb.com)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-org/kirinvulndb/issues)

## Acknowledgments

- **MITRE Corporation** for CVE database standards
- **NIST** for the National Vulnerability Database
- **OWASP** for security best practices
- **FastAPI** and **React** communities
- All contributors and security researchers

---

🛡️ **Stay secure, code confidently with Kirin Vulnerability Database!**