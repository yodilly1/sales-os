# Sales OS Deployment Guide

This document covers deployment configuration and procedures for Sales OS.

## Table of Contents

- [Quick Start](#quick-start)
- [Local Development](#local-development)
- [Environment Configuration](#environment-configuration)
- [CI/CD Pipeline](#cicd-pipeline)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Database Operations](#database-operations)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git

### One-Command Setup

```bash
./infra/scripts/setup.sh
```

This script will:
1. Check prerequisites
2. Create `.env` from `.env.example`
3. Generate secure secret keys
4. Set up basic backend and frontend structure
5. Start all services

### Manual Setup

```bash
# Clone repository
git clone <repository-url>
cd sales-os

# Create environment file
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## Local Development

### Starting Services

```bash
# Start core services
docker-compose up -d

# Start with development tools (pgAdmin, Redis Commander)
docker-compose --profile dev up -d

# Start specific service
docker-compose up -d backend
```

### Accessing Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |
| pgAdmin | http://localhost:5050 | Database GUI (dev profile) |
| Redis Commander | http://localhost:8081 | Redis GUI (dev profile) |

### Common Commands

```bash
# View logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Rebuild service
docker-compose up -d --build [service]

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Hot Reloading

Both backend and frontend are configured for hot reloading in development:

- **Backend**: Code changes in `./backend` are automatically detected
- **Frontend**: Next.js fast refresh is enabled

---

## Environment Configuration

### Environment Files

| File | Purpose |
|------|---------|
| `.env.example` | Template with all available options |
| `.env` | Local development (not committed) |
| `.env.staging` | Staging defaults |
| `.env.production` | Production defaults |

### Required Variables

```bash
# Application
ENVIRONMENT=development|staging|production
SECRET_KEY=<32-byte-hex-string>

# Database
POSTGRES_USER=sales_os
POSTGRES_PASSWORD=<secure-password>
POSTGRES_DB=sales_os

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Generating Secret Keys

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Or using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### GitHub Secrets for CI/CD

Configure these secrets in GitHub repository settings:

| Secret | Description |
|--------|-------------|
| `STAGING_SSH_KEY` | SSH private key for staging server |
| `STAGING_KNOWN_HOSTS` | SSH known hosts entry |
| `STAGING_HOST` | Staging server IP/hostname |
| `STAGING_USER` | SSH user for deployment |
| `STAGING_API_URL` | API URL for staging |
| `SLACK_WEBHOOK_URL` | (Optional) Slack notifications |

---

## CI/CD Pipeline

### Workflow Overview

```
PR/Push → CI Tests → Build Images → Deploy (on merge)
```

### CI Workflow (`.github/workflows/ci.yml`)

Runs on every pull request and push to main/develop:

1. **Backend Tests**
   - Lint with ruff
   - Type check with mypy
   - Run pytest with coverage

2. **Frontend Tests**
   - Lint with ESLint
   - Type check with TypeScript
   - Run Jest tests

3. **Build Verification**
   - Build Docker images
   - Verify successful build

4. **Security Scanning**
   - Trivy vulnerability scanner
   - Results uploaded to GitHub Security

### Staging Deployment (`.github/workflows/deploy-staging.yml`)

Automatically deploys on merge to main/develop:

1. Build and push Docker images to GitHub Container Registry
2. SSH to staging server
3. Pull new images
4. Perform zero-downtime rolling update
5. Run health checks
6. Notify via Slack

---

## Staging Deployment

### Provisioning New Server

```bash
# Provision a new staging server
./infra/scripts/provision-staging.sh <server-ip>
```

This script:
- Updates system packages
- Installs Docker and Docker Compose
- Configures firewall (UFW)
- Sets up fail2ban
- Creates deploy user
- Configures log rotation
- Installs monitoring agent

### Manual Deployment

```bash
# SSH to staging server
ssh deploy@staging.example.com

# Navigate to app directory
cd /opt/sales-os

# Pull latest images
docker-compose pull

# Deploy with rolling update
docker-compose up -d --remove-orphans

# Verify health
curl http://localhost:8000/health
```

---

## Production Deployment

### Zero-Downtime Strategy

The deployment uses a rolling update strategy:

1. Scale up new containers alongside existing ones
2. Wait for health checks to pass
3. Route traffic to new containers
4. Gracefully terminate old containers
5. Cleanup old images

### Rollback Procedure

```bash
# Quick rollback to previous version
docker-compose down
docker-compose up -d --remove-orphans

# Or restore from backup
./infra/scripts/restore.sh /backups/sales_os_backup_YYYYMMDD.sql.gz
```

### Health Checks

All services have built-in health checks:

- **Backend**: `GET /health` returns 200
- **Frontend**: `GET /api/health` returns 200
- **PostgreSQL**: `pg_isready` command
- **Redis**: `redis-cli ping`

---

## Database Operations

### Backups

```bash
# Create backup
./infra/scripts/backup.sh

# Create named backup
./infra/scripts/backup.sh my-backup-name

# Backups are stored in /backups by default
# Retention: 30 days (configurable via RETENTION_DAYS)
```

### Restore

```bash
# Restore from backup
./infra/scripts/restore.sh /backups/sales_os_backup_20241122_120000.sql.gz
```

### Migrations

```bash
# Run migrations (with Alembic)
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision -m "description"

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

---

## Troubleshooting

### Common Issues

#### Services won't start

```bash
# Check logs
docker-compose logs [service]

# Check if ports are in use
lsof -i :3000
lsof -i :8000

# Restart Docker
sudo systemctl restart docker
```

#### Database connection issues

```bash
# Check PostgreSQL is healthy
docker-compose exec postgres pg_isready

# Check connection from backend
docker-compose exec backend python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://sales_os:sales_os_dev@postgres:5432/sales_os')
conn = engine.connect()
print('Connected!')
conn.close()
"
```

#### Frontend build issues

```bash
# Clear Next.js cache
docker-compose exec frontend rm -rf .next node_modules/.cache

# Rebuild
docker-compose up -d --build frontend
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Since timestamp
docker-compose logs --since="2024-01-01T00:00:00" backend
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Check disk usage
docker system df

# Cleanup unused resources
docker system prune -f
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         NGINX                                │
│                    (Reverse Proxy)                          │
└─────────────────┬──────────────────┬────────────────────────┘
                  │                  │
          ┌───────▼────────┐  ┌──────▼───────┐
          │    Frontend    │  │   Backend    │
          │   (Next.js)    │  │  (FastAPI)   │
          │   Port 3000    │  │  Port 8000   │
          └────────────────┘  └──────┬───────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
           ┌────────▼────────┐              ┌────────▼────────┐
           │   PostgreSQL    │              │      Redis      │
           │   Port 5432     │              │   Port 6379     │
           └─────────────────┘              └─────────────────┘
```

---

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review logs: `docker-compose logs -f`
- Open an issue on GitHub
