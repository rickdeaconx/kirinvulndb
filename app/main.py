from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import time
import logging
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import vulnerabilities, tools, alerts, health, websocket, kirin, monitoring, wordpress, kirin_plugin, rss, admin
from app.db.database import engine
from app.db.base import Base
from app.services.websocket_manager import websocket_manager
from app.services.vulnerability_monitor import start_vulnerability_monitoring, stop_vulnerability_monitoring
from app.utils.logging import setup_logging


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for FastAPI application"""
    # Startup
    logger.info("Starting Kirin Vulnerability Database API")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    
    # Initialize services
    await websocket_manager.startup()
    logger.info("WebSocket manager initialized")
    
    # Start vulnerability monitoring (runs in background)
    if settings.DEBUG == False:  # Only in production
        asyncio.create_task(start_vulnerability_monitoring())
        logger.info("Vulnerability monitoring started (6-hour cycle)")
    else:
        logger.info("Vulnerability monitoring disabled in debug mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kirin Vulnerability Database API")
    await websocket_manager.shutdown()
    await stop_vulnerability_monitoring()


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(vulnerabilities.router, prefix="/api/vulnerabilities", tags=["vulnerabilities"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(websocket.router, prefix="/api/ws", tags=["websocket"])
app.include_router(kirin.router, prefix="/api/kirin", tags=["kirin-plugin"])
app.include_router(kirin_plugin.router, prefix="/api/kirin-plugin", tags=["kirin-cursor-plugin"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(wordpress.router, prefix="/api/wordpress", tags=["wordpress-integration"])
app.include_router(rss.router, prefix="/api/rss", tags=["rss-feeds"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    logger.warning("Static directory not found")

@app.get("/", tags=["root"])
async def root():
    """Serve the main dashboard"""
    try:
        with open("static/index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        # Fallback to JSON API info
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "description": settings.DESCRIPTION,
            "docs": "/docs",
            "health": "/api/health",
            "websocket": "/api/ws/vulnerabilities"
        }


@app.get("/api", tags=["api"])
async def api_info():
    """API information endpoint"""
    return {
        "version": settings.VERSION,
        "endpoints": {
            "vulnerabilities": "/api/vulnerabilities",
            "tools": "/api/tools", 
            "alerts": "/api/alerts",
            "health": "/api/health",
            "websocket": "/api/ws/vulnerabilities"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )