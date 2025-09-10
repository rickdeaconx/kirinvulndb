#!/bin/bash

# Kirin Vulnerability Database - Automated Setup Script
# Cursor AI Security - Production Ready

set -e

echo "=á  Kirin Vulnerability Database - Setup Script"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root"
    exit 1
fi

# Check for required commands
check_dependencies() {
    print_step "Checking dependencies..."
    
    local deps=("docker" "docker-compose" "python3" "pip3" "curl" "git")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing[*]}"
        echo "Please install the missing dependencies and try again."
        exit 1
    fi
    
    print_status "All dependencies found "
}

# Create environment file
setup_environment() {
    print_step "Setting up environment configuration..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            print_status "Created .env from .env.example"
        else
            print_error ".env.example not found!"
            exit 1
        fi
    else
        print_warning ".env already exists, skipping..."
    fi
    
    # Generate secure API key if using default
    if grep -q "your-super-secret-key-change-this" .env; then
        NEW_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
        sed -i.bak "s/your-super-secret-key-change-this/${NEW_KEY}/" .env
        print_status "Generated secure API secret key"
    fi
    
    # Generate database password if using default
    if grep -q "your_password" .env; then
        NEW_DB_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
        sed -i.bak "s/your_password/${NEW_DB_PASS}/" .env
        print_status "Generated secure database password"
    fi
}

# Install Python dependencies
install_python_deps() {
    print_step "Installing Python dependencies..."
    
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        print_status "Created Python virtual environment"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    print_status "Python dependencies installed "
}

# Setup Docker services
setup_docker() {
    print_step "Setting up Docker services..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p logs monitoring/prometheus monitoring/grafana/dashboards monitoring/grafana/provisioning
    
    # Start infrastructure services only
    docker-compose up -d postgres redis kafka zookeeper elasticsearch prometheus grafana
    
    print_status "Docker infrastructure services started "
    
    # Wait for services to be ready
    print_step "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    local services=("postgres" "redis" "kafka")
    for service in "${services[@]}"; do
        local retries=30
        while [[ $retries -gt 0 ]]; do
            if docker-compose ps "$service" | grep -q "healthy\|Up"; then
                print_status "$service is ready "
                break
            fi
            ((retries--))
            sleep 2
        done
        
        if [[ $retries -eq 0 ]]; then
            print_error "$service failed to start properly"
            docker-compose logs "$service"
            exit 1
        fi
    done
}

# Initialize database
init_database() {
    print_step "Initializing database..."
    
    source venv/bin/activate
    
    # Wait a bit more for PostgreSQL to be fully ready
    sleep 10
    
    # Run database initialization
    if [[ -f "scripts/init_db.py" ]]; then
        python scripts/init_db.py
        print_status "Database initialized "
    else
        # Create basic tables using alembic if available
        if command -v alembic &> /dev/null; then
            alembic upgrade head
            print_status "Database migrations applied "
        else
            print_warning "Database initialization script not found, skipping..."
        fi
    fi
}

# Start application services
start_application() {
    print_step "Starting application services..."
    
    # Start API and worker services
    docker-compose up -d api worker
    
    print_status "Application services started "
    
    # Wait for API to be ready
    local retries=60
    while [[ $retries -gt 0 ]]; do
        if curl -f -s http://localhost:8080/api/health &> /dev/null; then
            print_status "API server is ready "
            break
        fi
        ((retries--))
        sleep 2
    done
    
    if [[ $retries -eq 0 ]]; then
        print_error "API server failed to start"
        docker-compose logs api
        exit 1
    fi
}

# Run health checks
health_check() {
    print_step "Running health checks..."
    
    local endpoints=(
        "http://localhost:8080/api/health"
        "http://localhost:8080/api/vulnerabilities/stats"
        "http://localhost:8080/api/rss/vulnerabilities.xml"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$endpoint" &> /dev/null; then
            print_status " $endpoint"
        else
            print_warning " $endpoint (may need time to initialize)"
        fi
    done
}

# Display access information
show_access_info() {
    echo ""
    echo "<‰ Kirin Vulnerability Database Setup Complete!"
    echo "=============================================="
    echo ""
    echo "= Access Points:"
    echo "  =Ê API Documentation:  http://localhost:8080/docs"
    echo "  =' API Base URL:       http://localhost:8080/api"
    echo "  =á RSS Feed:           http://localhost:8080/api/rss/vulnerabilities.xml"
    echo "  d  Health Check:       http://localhost:8080/api/health"
    echo "  =È Prometheus:         http://localhost:9090"
    echo "  =Ë Grafana:            http://localhost:3001 (admin/admin)"
    echo ""
    echo "= Admin API Key: kirin-admin-2025-v1"
    echo "   Use this for vulnerability submission: X-Admin-Key header"
    echo ""
    echo "=3 Docker Management:"
    echo "  Stop services:   docker-compose down"
    echo "  View logs:       docker-compose logs -f [service]"
    echo "  Restart:         docker-compose restart [service]"
    echo ""
    echo "=ñ WordPress RSS Integration:"
    echo "  Use: http://localhost:8080/api/rss/vulnerabilities.xml"
    echo "  Updates every 6 hours with AI/Cursor vulnerabilities"
    echo ""
}

# Main execution
main() {
    echo "Starting automated setup..."
    echo ""
    
    check_dependencies
    setup_environment
    install_python_deps
    setup_docker
    init_database
    start_application
    health_check
    show_access_info
    
    print_status "Setup completed successfully! =€"
}

# Cleanup function
cleanup() {
    print_warning "Setup interrupted. Cleaning up..."
    docker-compose down &> /dev/null || true
    exit 1
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Run main function
main "$@"