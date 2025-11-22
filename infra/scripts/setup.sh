#!/bin/bash
# =============================================================================
# Sales OS - Development Environment Setup Script
# =============================================================================
# This script sets up the development environment from scratch
# Usage: ./infra/scripts/setup.sh
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check for required tools
check_requirements() {
    print_header "Checking Requirements"

    local missing=()

    if ! command -v docker &> /dev/null; then
        missing+=("docker")
    else
        print_success "Docker is installed: $(docker --version)"
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing+=("docker-compose")
    else
        print_success "Docker Compose is installed"
    fi

    if ! command -v git &> /dev/null; then
        missing+=("git")
    else
        print_success "Git is installed: $(git --version)"
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing[*]}"
        echo "Please install the missing tools and run this script again."
        exit 1
    fi
}

# Setup environment file
setup_env() {
    print_header "Setting Up Environment"

    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_success "Created .env from .env.example"

            # Generate a random secret key
            SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | base64 | tr -d '\n' | head -c 64)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/your-secret-key-here/$SECRET_KEY/" .env
            else
                sed -i "s/your-secret-key-here/$SECRET_KEY/" .env
            fi
            print_success "Generated random SECRET_KEY"
        else
            print_error ".env.example not found!"
            exit 1
        fi
    else
        print_warning ".env already exists, skipping..."
    fi
}

# Setup backend
setup_backend() {
    print_header "Setting Up Backend"

    cd backend

    # Create requirements.txt if it doesn't exist
    if [ ! -f requirements.txt ]; then
        cat > requirements.txt << 'EOF'
# Web framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0

# Database
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.12.0

# Redis
redis>=5.0.0

# Authentication
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Validation
pydantic>=2.5.0
pydantic-settings>=2.1.0
email-validator>=2.1.0

# HTTP client
httpx>=0.25.0

# Utilities
python-multipart>=0.0.6
python-dotenv>=1.0.0
EOF
        print_success "Created requirements.txt"
    fi

    # Create requirements-dev.txt if it doesn't exist
    if [ ! -f requirements-dev.txt ]; then
        cat > requirements-dev.txt << 'EOF'
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.25.0

# Linting & Formatting
ruff>=0.1.0
mypy>=1.7.0

# Development
ipython>=8.18.0
EOF
        print_success "Created requirements-dev.txt"
    fi

    # Create basic app structure if it doesn't exist
    if [ ! -d app ]; then
        mkdir -p app
        cat > app/__init__.py << 'EOF'
"""Sales OS Backend Application."""
EOF

        cat > app/main.py << 'EOF'
"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sales OS API",
    description="Sales Operating System API",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Sales OS API"}
EOF
        print_success "Created basic backend app structure"
    fi

    cd ..
}

# Setup frontend
setup_frontend() {
    print_header "Setting Up Frontend"

    cd frontend

    # Create package.json if it doesn't exist
    if [ ! -f package.json ]; then
        cat > package.json << 'EOF'
{
  "name": "sales-os-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "test": "jest"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.3.0",
    "eslint": "^8.55.0",
    "eslint-config-next": "^14.0.0",
    "jest": "^29.7.0",
    "@testing-library/react": "^14.1.0"
  }
}
EOF
        print_success "Created package.json"
    fi

    # Create next.config.js if it doesn't exist
    if [ ! -f next.config.js ] && [ ! -f next.config.mjs ]; then
        cat > next.config.js << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
}

module.exports = nextConfig
EOF
        print_success "Created next.config.js"
    fi

    cd ..
}

# Start services
start_services() {
    print_header "Starting Services"

    echo "Starting Docker services..."

    # Use docker compose (v2) or docker-compose (v1)
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi

    print_success "Services started!"
}

# Print final instructions
print_instructions() {
    print_header "Setup Complete!"

    echo "Your Sales OS development environment is ready!"
    echo ""
    echo "Services:"
    echo "  - Frontend:    http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs:    http://localhost:8000/docs"
    echo "  - PostgreSQL:  localhost:5432"
    echo "  - Redis:       localhost:6379"
    echo ""
    echo "Development tools (start with: docker-compose --profile dev up -d):"
    echo "  - pgAdmin:     http://localhost:5050"
    echo "  - Redis Commander: http://localhost:8081"
    echo ""
    echo "Useful commands:"
    echo "  docker-compose logs -f          # View logs"
    echo "  docker-compose down             # Stop services"
    echo "  docker-compose restart backend  # Restart backend"
    echo ""
    print_success "Happy coding!"
}

# Main execution
main() {
    print_header "Sales OS Development Setup"

    check_requirements
    setup_env
    setup_backend
    setup_frontend
    start_services
    print_instructions
}

# Run main
main "$@"
