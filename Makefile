# Sales OS Makefile
# Common commands for development and deployment

.PHONY: help install dev build start stop restart logs clean test lint db-migrate db-reset

# Default target
help:
	@echo "Sales OS - Available Commands"
	@echo ""
	@echo "Development:"
	@echo "  make install     - Install all dependencies"
	@echo "  make dev         - Start development environment"
	@echo "  make stop        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate  - Run database migrations"
	@echo "  make db-reset    - Reset database (WARNING: destroys data)"
	@echo "  make db-shell    - Open PostgreSQL shell"
	@echo ""
	@echo "Testing:"
	@echo "  make test        - Run all tests"
	@echo "  make test-backend  - Run backend tests"
	@echo "  make test-frontend - Run frontend tests"
	@echo "  make lint        - Run linters"
	@echo ""
	@echo "Production:"
	@echo "  make build       - Build production images"
	@echo "  make start-prod  - Start production environment"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean       - Remove all containers and volumes"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-frontend - Open shell in frontend container"

# ===========================================
# DEVELOPMENT
# ===========================================

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Done!"

# Start development environment
dev:
	@echo "Starting Sales OS development environment..."
	docker-compose up -d db redis
	@echo "Waiting for database..."
	sleep 5
	docker-compose up -d backend worker frontend
	@echo ""
	@echo "Sales OS is running!"
	@echo "  Frontend: http://localhost:3000"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Run 'make logs' to view logs"

# Start only infrastructure (db, redis)
dev-infra:
	@echo "Starting infrastructure services..."
	docker-compose up -d db redis
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

# Start backend locally (without Docker)
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend locally (without Docker)
dev-frontend:
	cd frontend && npm run dev

# Stop all services
stop:
	docker-compose down

# Restart all services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-worker:
	docker-compose logs -f worker

# ===========================================
# DATABASE
# ===========================================

# Run database migrations
db-migrate:
	docker-compose exec backend alembic upgrade head

# Generate new migration
db-migration:
	@read -p "Migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

# Reset database (WARNING: destroys all data)
db-reset:
	@echo "WARNING: This will destroy all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		docker-compose down -v; \
		docker-compose up -d db; \
		sleep 5; \
		echo "Database reset complete."; \
	fi

# Open PostgreSQL shell
db-shell:
	docker-compose exec db psql -U salesos -d salesos

# Backup database
db-backup:
	@mkdir -p backups
	docker-compose exec db pg_dump -U salesos salesos > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup saved to backups/"

# Restore database from backup
db-restore:
	@read -p "Backup file: " file; \
	docker-compose exec -T db psql -U salesos salesos < $$file

# ===========================================
# TESTING
# ===========================================

# Run all tests
test: test-backend test-frontend

# Run backend tests
test-backend:
	docker-compose exec backend pytest -v --cov=app --cov-report=term-missing

# Run frontend tests
test-frontend:
	docker-compose exec frontend npm test

# Run linters
lint: lint-backend lint-frontend

lint-backend:
	docker-compose exec backend flake8 app/ --max-line-length=120
	docker-compose exec backend mypy app/

lint-frontend:
	docker-compose exec frontend npm run lint

# Type checking
type-check:
	docker-compose exec frontend npm run type-check

# ===========================================
# PRODUCTION
# ===========================================

# Build production images
build:
	docker-compose -f docker-compose.yml build

# Start production environment
start-prod:
	docker-compose --profile production up -d

# Deploy (placeholder - customize for your hosting)
deploy:
	@echo "Deploying Sales OS..."
	@echo "Configure this target for your hosting provider"
	# railway up
	# vercel --prod
	# fly deploy

# ===========================================
# UTILITIES
# ===========================================

# Remove all containers and volumes
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Open shell in backend container
shell-backend:
	docker-compose exec backend /bin/bash

# Open shell in frontend container
shell-frontend:
	docker-compose exec frontend /bin/sh

# Open Redis CLI
redis-cli:
	docker-compose exec redis redis-cli

# Check service health
health:
	@echo "Checking services..."
	@curl -s http://localhost:8000/health | jq . || echo "Backend: DOWN"
	@curl -s http://localhost:3000 > /dev/null && echo "Frontend: UP" || echo "Frontend: DOWN"
	@docker-compose exec -T db pg_isready -U salesos > /dev/null && echo "Database: UP" || echo "Database: DOWN"
	@docker-compose exec -T redis redis-cli ping > /dev/null && echo "Redis: UP" || echo "Redis: DOWN"

# Generate API documentation
docs:
	@echo "API documentation available at http://localhost:8000/docs"
	@echo "ReDoc available at http://localhost:8000/redoc"

# Format code
format:
	cd backend && black app/ && isort app/
	cd frontend && npm run format 2>/dev/null || true

# Update dependencies
update-deps:
	cd backend && pip-compile requirements.in -o requirements.txt
	cd frontend && npm update
