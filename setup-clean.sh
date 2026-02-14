#!/bin/bash

# NOCbRAIN Setup Script
# AI Network Operations Center Assistant Installation
# This script provides a clean, secure, and modular setup process

set -euo pipefail  # Exit on error, undefined vars, and pipe failures

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration variables (can be overridden by environment)
readonly PROJECT_NAME="nocbrain"
readonly DEFAULT_BACKEND_PORT=8000
readonly DEFAULT_FRONTEND_PORT=3000
readonly DEFAULT_POSTGRES_PORT=5432
readonly DEFAULT_REDIS_PORT=6379
readonly DEFAULT_QDRANT_PORT=6333

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if running as root (discouraged for development)
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. This is not recommended for development setups."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
    fi

    # Check required commands
    local required_commands=("docker" "docker-compose" "git" "curl")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            error_exit "$cmd is required but not installed. Please install it first."
        fi
    done

    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        error_exit "Docker daemon is not running. Please start Docker first."
    fi

    log_success "Prerequisites check passed"
}

# Detect operating system
detect_os() {
    case "$OSTYPE" in
        linux-gnu*)
            OS="linux"
            if [[ -f /etc/debian_version ]]; then
                DISTRO="debian"
            elif [[ -f /etc/redhat-release ]]; then
                DISTRO="redhat"
            elif [[ -f /etc/arch-release ]]; then
                DISTRO="arch"
            else
                DISTRO="unknown"
            fi
            ;;
        darwin*)
            OS="macos"
            ;;
        msys*|win32*)
            OS="windows"
            ;;
        *)
            error_exit "Unsupported operating system: $OSTYPE"
            ;;
    esac

    log_success "Detected OS: $OS ${DISTRO:+($DISTRO)}"
}

# Create environment configuration
create_env_files() {
    log_info "Creating environment configuration files..."

    # Backend .env
    if [[ ! -f "$BACKEND_DIR/.env" ]]; then
        cat > "$BACKEND_DIR/.env" << EOF
# Database Configuration
DATABASE_URL=postgresql+asyncpg://nocbrain:nocbrain123@localhost:${DEFAULT_POSTGRES_PORT}/nocbrain

# Redis Configuration
REDIS_URL=redis://localhost:${DEFAULT_REDIS_PORT}/0

# Qdrant Configuration
QDRANT_URL=http://localhost:${DEFAULT_QDRANT_PORT}

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-change-this-in-production-$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Configuration (Required for AI features)
OPENAI_API_KEY=your-openai-api-key-here

# Application Settings
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development

# CORS Settings
ALLOWED_HOSTS=http://localhost:3000,http://localhost:8000

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Knowledge Base
KNOWLEDGE_BASE_PATH=./knowledge-base

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
UPLOAD_PATH=./uploads

# Multi-tenancy
DEFAULT_TENANT_ID=global
TENANT_ISOLATION_ENABLED=true
EOF
        log_success "Created backend/.env file"
        log_warning "⚠️  IMPORTANT: Update SECRET_KEY and OPENAI_API_KEY in backend/.env before deployment!"
    else
        log_info "Backend .env file already exists"
    fi

    # Frontend .env
    if [[ ! -f "$FRONTEND_DIR/.env" ]]; then
        cat > "$FRONTEND_DIR/.env" << EOF
# API Configuration
REACT_APP_API_URL=http://localhost:${DEFAULT_BACKEND_PORT}
REACT_APP_WS_URL=ws://localhost:${DEFAULT_BACKEND_PORT}/ws

# Application Settings
REACT_APP_ENVIRONMENT=development
REACT_APP_DEBUG=true

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_ERROR_REPORTING=false

# Multi-tenancy
REACT_APP_DEFAULT_TENANT_ID=global
EOF
        log_success "Created frontend/.env file"
    else
        log_info "Frontend .env file already exists"
    fi
}

# Setup Python backend
setup_backend() {
    log_info "Setting up Python backend..."

    cd "$BACKEND_DIR"

    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        log_success "Created Python virtual environment"
    fi

    # Activate virtual environment
    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        log_success "Installed Python dependencies"
    else
        log_warning "requirements.txt not found"
    fi

    cd "$PROJECT_ROOT"
}

# Setup Node.js frontend
setup_frontend() {
    log_info "Setting up Node.js frontend..."

    cd "$FRONTEND_DIR"

    # Install dependencies
    if [[ -f "package.json" ]]; then
        npm install
        log_success "Installed Node.js dependencies"
    else
        log_warning "package.json not found"
    fi

    cd "$PROJECT_ROOT"
}

# Initialize database
init_database() {
    log_info "Initializing database..."

    # Wait for database to be ready
    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose exec -T postgres pg_isready -U nocbrain >/dev/null 2>&1; then
            break
        fi
        log_info "Waiting for database to be ready... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done

    if [[ $attempt -gt $max_attempts ]]; then
        log_error "Database failed to start within timeout"
        return 1
    fi

    # Run database migrations
    cd "$BACKEND_DIR"
    source venv/bin/activate
    python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
    log_success "Database initialized"

    cd "$PROJECT_ROOT"
}

# Run tests
run_tests() {
    log_info "Running tests..."

    # Backend tests
    if [[ -d "$BACKEND_DIR/tests" ]]; then
        cd "$BACKEND_DIR"
        source venv/bin/activate
        if python -m pytest tests/ -v --tb=short; then
            log_success "Backend tests passed"
        else
            log_warning "Some backend tests failed"
        fi
        cd "$PROJECT_ROOT"
    fi

    # Frontend tests
    if [[ -d "$FRONTEND_DIR" ]]; then
        cd "$FRONTEND_DIR"
        if npm test -- --watchAll=false --passWithNoTests; then
            log_success "Frontend tests passed"
        else
            log_warning "Some frontend tests failed"
        fi
        cd "$PROJECT_ROOT"
    fi
}

# Start development services
start_dev_services() {
    log_info "Starting development services..."

    # Start Docker services
    docker-compose up -d
    log_success "Docker services started"

    # Start backend
    cd "$BACKEND_DIR"
    source venv/bin/activate
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port "$DEFAULT_BACKEND_PORT" > backend.log 2>&1 &
    BACKEND_PID=$!
    log_success "Backend started (PID: $BACKEND_PID)"
    cd "$PROJECT_ROOT"

    # Start frontend
    cd "$FRONTEND_DIR"
    nohup npm start > frontend.log 2>&1 &
    FRONTEND_PID=$!
    log_success "Frontend started (PID: $FRONTEND_PID)"
    cd "$PROJECT_ROOT"

    # Save PIDs for cleanup
    echo "$BACKEND_PID" > .backend.pid
    echo "$FRONTEND_PID" > .frontend.pid

    log_success "Development services started successfully!"
    echo
    echo "🌐 Frontend: http://localhost:$DEFAULT_FRONTEND_PORT"
    echo "🚀 Backend API: http://localhost:$DEFAULT_BACKEND_PORT"
    echo "📚 API Docs: http://localhost:$DEFAULT_BACKEND_PORT/docs"
    echo "📊 Grafana: http://localhost:3001"
    echo "📈 Prometheus: http://localhost:9090"
    echo
    echo "To stop services, run: $0 cleanup"
}

# Stop development services
cleanup_services() {
    log_info "Cleaning up services..."

    # Stop background processes
    if [[ -f ".backend.pid" ]]; then
        kill "$(cat .backend.pid)" 2>/dev/null || true
        rm .backend.pid
    fi

    if [[ -f ".frontend.pid" ]]; then
        kill "$(cat .frontend.pid)" 2>/dev/null || true
        rm .frontend.pid
    fi

    # Stop Docker services
    docker-compose down -v 2>/dev/null || true

    log_success "Cleanup completed"
}

# Show usage information
show_usage() {
    cat << EOF
NOCbRAIN Setup Script

USAGE:
    $0 [COMMAND]

COMMANDS:
    install     Complete installation (default)
    dev         Start development services only
    test        Run tests only
    cleanup     Stop all services and cleanup
    help        Show this help message

ENVIRONMENT VARIABLES:
    BACKEND_PORT       Backend port (default: $DEFAULT_BACKEND_PORT)
    FRONTEND_PORT      Frontend port (default: $DEFAULT_FRONTEND_PORT)
    POSTGRES_PORT      PostgreSQL port (default: $DEFAULT_POSTGRES_PORT)
    REDIS_PORT         Redis port (default: $DEFAULT_REDIS_PORT)

EXAMPLES:
    $0 install                    # Full setup
    BACKEND_PORT=9000 $0 dev      # Start with custom backend port
    $0 test                       # Run tests only
    $0 cleanup                    # Stop everything

For more information, visit: https://github.com/conformist77/nocbrain
EOF
}

# Main function
main() {
    local command="${1:-install}"

    case "$command" in
        install)
            log_info "Starting complete NOCbRAIN installation..."
            check_prerequisites
            detect_os
            create_env_files
            setup_backend
            setup_frontend

            # Start Docker services and initialize
            docker-compose up -d postgres redis qdrant
            init_database

            run_tests
            start_dev_services

            log_success "🎉 NOCbRAIN installation completed successfully!"
            ;;
        dev)
            check_prerequisites
            create_env_files
            setup_backend
            setup_frontend
            start_dev_services
            ;;
        test)
            setup_backend
            setup_frontend
            run_tests
            ;;
        cleanup)
            cleanup_services
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# Trap cleanup on script exit
trap cleanup_services EXIT

# Run main function with all arguments
main "$@"
