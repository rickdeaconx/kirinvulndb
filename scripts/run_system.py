#!/usr/bin/env python3
"""
System startup script for Kirin Vulnerability Database
Starts all services in the correct order
"""

import os
import sys
import time
import subprocess
import signal
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        self.processes = {}
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def start_service(self, name, command, wait_time=2):
        """Start a service with the given command"""
        logger.info(f"Starting {name}...")
        
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            self.processes[name] = process
            logger.info(f"{name} started with PID {process.pid}")
            time.sleep(wait_time)
            
            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"{name} failed to start:")
                logger.error(f"stdout: {stdout.decode()}")
                logger.error(f"stderr: {stderr.decode()}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            return False
    
    def stop_service(self, name):
        """Stop a service"""
        if name in self.processes:
            process = self.processes[name]
            logger.info(f"Stopping {name} (PID {process.pid})...")
            
            try:
                # Send SIGTERM to the process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                
                # Wait for process to terminate
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"{name} didn't stop gracefully, forcing...")
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    process.wait()
                
                logger.info(f"{name} stopped")
                del self.processes[name]
                
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
    
    def start_infrastructure(self):
        """Start infrastructure services (databases, etc.)"""
        logger.info("Starting infrastructure services...")
        
        # Start PostgreSQL (assuming it's installed via Homebrew on macOS)
        if sys.platform == "darwin":
            if not self.start_service("PostgreSQL", "brew services start postgresql", 3):
                logger.error("Failed to start PostgreSQL")
                return False
        
        # Start Redis
        if not self.start_service("Redis", "redis-server --daemonize yes", 2):
            logger.warning("Redis failed to start, some features may not work")
        
        # Start Kafka (if available)
        kafka_command = "kafka-server-start.sh config/server.properties"
        if not self.start_service("Kafka", kafka_command, 5):
            logger.warning("Kafka failed to start, real-time streaming may not work")
        
        logger.info("Infrastructure services started")
        return True
    
    def initialize_database(self):
        """Initialize the database with tables and sample data"""
        logger.info("Initializing database...")
        
        try:
            # Run database initialization script
            result = subprocess.run([
                sys.executable, 
                str(project_root / "scripts" / "init_db.py")
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Database initialized successfully")
                return True
            else:
                logger.error(f"Database initialization failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def start_application_services(self):
        """Start the main application services"""
        logger.info("Starting application services...")
        
        # Start FastAPI application
        api_command = f"{sys.executable} -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload"
        if not self.start_service("API Server", api_command, 3):
            logger.error("Failed to start API server")
            return False
        
        # Start Celery worker
        celery_command = f"{sys.executable} -m celery -A app.celery_app worker --loglevel=info"
        if not self.start_service("Celery Worker", celery_command, 2):
            logger.warning("Failed to start Celery worker, background tasks may not work")
        
        # Start Celery beat scheduler
        beat_command = f"{sys.executable} -m celery -A app.celery_app beat --loglevel=info"
        if not self.start_service("Celery Beat", beat_command, 2):
            logger.warning("Failed to start Celery beat, scheduled tasks may not work")
        
        logger.info("Application services started")
        return True
    
    def start_frontend(self):
        """Start the React frontend"""
        logger.info("Starting React frontend...")
        
        frontend_dir = project_root / "frontend"
        if not frontend_dir.exists():
            logger.warning("Frontend directory not found, skipping frontend start")
            return True
        
        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            logger.info("Installing frontend dependencies...")
            install_result = subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                capture_output=True,
                text=True
            )
            
            if install_result.returncode != 0:
                logger.error(f"Failed to install frontend dependencies: {install_result.stderr}")
                return False
        
        # Start React development server
        frontend_command = "npm start"
        if not self.start_service("React Frontend", f"cd {frontend_dir} && {frontend_command}", 5):
            logger.warning("Failed to start React frontend")
            return False
        
        logger.info("React frontend started")
        return True
    
    def run_health_checks(self):
        """Run health checks on all services"""
        logger.info("Running health checks...")
        
        # Wait a bit for services to fully start
        time.sleep(10)
        
        try:
            # Check API health
            import requests
            response = requests.get("http://localhost:8080/api/health", timeout=10)
            if response.status_code == 200:
                logger.info("✓ API server health check passed")
            else:
                logger.warning(f"✗ API server health check failed: {response.status_code}")
            
            # Check detailed health
            response = requests.get("http://localhost:8080/api/health/detailed", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info("✓ Detailed health check passed")
                logger.info(f"Service status: {health_data.get('status')}")
                
                # Check individual components
                for component, status in health_data.get('checks', {}).items():
                    status_indicator = "✓" if status.get('status') == 'healthy' else "✗"
                    logger.info(f"{status_indicator} {component}: {status.get('status')}")
                    
            else:
                logger.warning("✗ Detailed health check failed")
                
        except Exception as e:
            logger.error(f"Health checks failed: {e}")
    
    def monitor_services(self):
        """Monitor running services"""
        logger.info("Monitoring services... (Press Ctrl+C to stop)")
        
        try:
            while self.running:
                # Check if processes are still running
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        logger.warning(f"Service {name} has stopped unexpectedly")
                        # Could implement restart logic here
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
    
    def shutdown(self):
        """Shutdown all services"""
        logger.info("Shutting down all services...")
        self.running = False
        
        # Stop application services first
        services_to_stop = [
            "React Frontend",
            "Celery Beat", 
            "Celery Worker",
            "API Server"
        ]
        
        for service in services_to_stop:
            self.stop_service(service)
        
        # Stop infrastructure services
        if sys.platform == "darwin":
            try:
                subprocess.run(["brew", "services", "stop", "postgresql"], 
                             capture_output=True, timeout=10)
                logger.info("PostgreSQL stopped")
            except:
                pass
        
        # Stop Redis
        try:
            subprocess.run(["redis-cli", "shutdown"], capture_output=True, timeout=5)
            logger.info("Redis stopped")
        except:
            pass
        
        logger.info("All services stopped")
    
    def run_full_system(self):
        """Run the complete system"""
        logger.info("Starting Kirin Vulnerability Database System")
        
        try:
            # Step 1: Start infrastructure
            if not self.start_infrastructure():
                logger.error("Failed to start infrastructure, aborting")
                return False
            
            # Step 2: Initialize database
            if not self.initialize_database():
                logger.error("Failed to initialize database, aborting")
                return False
            
            # Step 3: Start application services
            if not self.start_application_services():
                logger.error("Failed to start application services, aborting")
                return False
            
            # Step 4: Start frontend
            self.start_frontend()  # Non-critical
            
            # Step 5: Run health checks
            self.run_health_checks()
            
            # Step 6: Display startup information
            self.display_startup_info()
            
            # Step 7: Monitor services
            self.monitor_services()
            
        except Exception as e:
            logger.error(f"System startup failed: {e}")
            return False
        
        return True
    
    def display_startup_info(self):
        """Display system startup information"""
        logger.info("=" * 60)
        logger.info("🚀 Kirin Vulnerability Database System Started!")
        logger.info("=" * 60)
        logger.info("📊 Dashboard: http://localhost:3000")
        logger.info("🔧 API Docs: http://localhost:8080/docs")
        logger.info("💾 API Base: http://localhost:8080/api")
        logger.info("🔌 Kirin Plugin API: http://localhost:8080/api/kirin")
        logger.info("❤️  Health Check: http://localhost:8080/api/health")
        logger.info("=" * 60)
        logger.info("Press Ctrl+C to stop all services")
        logger.info("=" * 60)


def main():
    """Main entry point"""
    manager = ServiceManager()
    
    try:
        success = manager.run_full_system()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Startup interrupted by user")
        manager.shutdown()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        manager.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()