from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import logging
from datetime import datetime

from app.db.database import get_db
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Kirin Vulnerability Database",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check including database and external services"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "checks": {}
    }
    
    overall_healthy = True
    
    # Database check
    try:
        result = db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time": "< 1ms"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Redis check
    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time": "< 1ms"
        }
        redis_client.close()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["checks"]["redis"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        overall_healthy = False
    
    # Update overall status
    if not overall_healthy:
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/metrics")
async def metrics():
    """Application metrics"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "uptime": "0d 0h 0m 0s",  # TODO: Implement actual uptime tracking
            "requests_total": 0,      # TODO: Implement request counting
            "active_websockets": 0,   # TODO: Get from websocket manager
            "database_connections": 0 # TODO: Get from connection pool
        }
    }


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Kubernetes readiness probe"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}