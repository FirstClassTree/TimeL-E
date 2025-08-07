# Docker Setup & Deployment

Complete containerization setup for TimeL-E using Docker Compose. This setup includes 5 services that work together to provide the full application stack.

## Quick Start

Start the entire application:
```bash
# Start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ML Service**: http://localhost:8001
- **Database Service**: http://localhost:7000

## Architecture Overview

TimeL-E uses a microservice architecture with 5 containers:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │───▶│   Backend   │───▶│ DB Service  │
│ React+Nginx │    │   FastAPI   │    │   FastAPI   │
│   :3000     │    │    :8000    │    │    :7000    │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                   ┌─────────────┐    ┌─────────────┐
                   │ ML Service  │    │ PostgreSQL  │
                   │   FastAPI   │    │  Database   │
                   │    :8001    │    │    :5432    │
                   └─────────────┘    └─────────────┘
```

### Service Details

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| **frontend** | React + Vite + Nginx | 3000 | User interface |
| **backend** | FastAPI + Python | 8000 | API gateway |
| **ml-service** | FastAPI + Scikit-learn | 8001 | ML predictions |
| **db-service** | FastAPI + SQLAlchemy | 7000 | Database operations |
| **postgres** | PostgreSQL 17 | 5432 | Data storage |

## Environment Configuration

Configuration is managed through the `.env` file. Key variables:

### Service Ports
```bash
FRONTEND_PORT=3000
BACKEND_PORT=8000
ML_SERVICE_PORT=8001
DB_SERVICE_PORT=7000
```

### Database Settings
```bash
POSTGRES_USER=timele_user
POSTGRES_PASSWORD=timele_password
POSTGRES_DB=timele_db
DATABASE_URL=postgresql://timele_user:timele_password@postgres:5432/timele_db
```

### Service URLs (Internal)
```bash
DB_SERVICE_URL=http://db-service:7000
ML_SERVICE_URL=http://ml-service:8001
VITE_API_URL=http://localhost:8000/api
```

### Security
```bash
JWT_SECRET=your-super-secret-jwt-key-for-dev-that-is-at-least-32-chars
JWT_REFRESH_SECRET=your-super-secret-jwt-refresh-key-for-dev-that-is-32-chars
```

## Development Workflow

### Daily Commands
```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up frontend

# Rebuild after code changes
docker-compose up --build backend

# View logs
docker-compose logs -f backend

# Stop everything
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Working with Services
```bash
# Execute commands in running container
docker-compose exec backend python manage.py migrate
docker-compose exec ml-service python train_models.py
docker-compose exec postgres psql -U timele_user -d timele_db

# Shell access
docker-compose exec backend bash
docker-compose exec frontend sh
```

### Data Management
```bash
# Reset database (if RESET_DATABASE_ON_STARTUP=true)
docker-compose restart db-service

# Backup database
docker-compose exec postgres pg_dump -U timele_user timele_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U timele_user -d timele_db < backup.sql
```

## Build Optimization

For faster builds and better caching, use the optimized configuration:

```bash
# Build with optimization
docker-compose -f docker-compose.yml -f docker-compose.build-optimized.yml build

# Run with optimized images
docker-compose -f docker-compose.yml -f docker-compose.build-optimized.yml up
```

### Optimizations Include:
- **Multi-stage builds** - Smaller final images
- **Layer caching** - Faster rebuilds
- **Alpine Linux** - Lightweight base images
- **Build cache sharing** - Reuse layers across services

## Health Checks & Dependencies

Services include health checks and startup dependencies:

```yaml
# Example health check
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval: 30s
  timeout: 30s
  retries: 5
  start_period: 60s
```

**Startup Order:**
1. PostgreSQL starts first
2. DB Service waits for PostgreSQL
3. Backend & ML Service wait for DB Service
4. Frontend waits for Backend

Check service health:
```bash
docker-compose ps
```

## Volume Mounts & Persistence

### Data Persistence
```bash
# PostgreSQL data (persists across restarts)
volumes:
  postgres_data:/var/lib/postgresql/data

# ML models (shared with host)
./ml-service/models:/app/models

# Training data (shared with host)  
./data:/app/training-data
```

### Development Mounts
For development, you can add volume mounts for hot reloading:
```yaml
volumes:
  - ./backend/app:/app/app  # Backend code
  - ./frontend/src:/app/src # Frontend code
```

## Networking

All services communicate through the `timele-network` bridge network:
- Services can reach each other by service name (e.g., `http://backend:8000`)
- Only exposed ports are accessible from the host
- Internal communication happens on service ports

## Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend

# Restart problematic service
docker-compose restart db-service
```

**Database connection errors:**
```bash
# Verify PostgreSQL is running
docker-compose exec postgres pg_isready -U timele_user

# Check database exists
docker-compose exec postgres psql -U timele_user -l
```

**Port conflicts:**
```bash
# Check what's using ports
lsof -i :3000
lsof -i :8000

# Change ports in .env file
FRONTEND_PORT=3001
BACKEND_PORT=8001
```

**Out of disk space:**
```bash
# Clean up Docker resources
docker system prune -a

# Remove unused volumes
docker volume prune

# Check disk usage
docker system df
```

**Build failures:**
```bash
# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build backend

# Check build logs
docker-compose build backend --progress=plain
```

### Performance Issues

**Slow startup:**
- Use `docker-compose.build-optimized.yml` for faster builds
- Ensure you have enough RAM (8GB+ recommended)
- Use SSD storage for Docker data

**High resource usage:**
```bash
# Monitor resource usage
docker stats

# Limit service resources
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
```

## Production Considerations

### Environment Variables
Update these for production:
```bash
NODE_ENV=production
DEBUG=false
JWT_SECRET=<strong-random-secret>
JWT_REFRESH_SECRET=<strong-random-secret>
POSTGRES_PASSWORD=<strong-random-password>
```

### Monitoring
Add monitoring services:
```yaml
services:
  prometheus:
    image: prom/prometheus
  grafana:
    image: grafana/grafana
```

## File Structure

```
.
├── docker-compose.yml                 # Main compose file
├── docker-compose.build-optimized.yml # Build optimizations
├── .env                              # Environment variables
├── .dockerignore                     # Global Docker ignore
├── backend/
│   ├── Dockerfile                    # Backend container
│   └── .dockerignore
├── frontend/
│   ├── Dockerfile                    # Frontend container  
│   └── .dockerignore
├── db_service/
│   ├── Dockerfile                    # DB service container
│   └── .dockerignore
├── ml-service/
│   ├── Dockerfile                    # ML service container
│   └── .dockerignore
└── data/                            # Shared training data
```

## Useful Commands Reference

```bash
# Basic operations
docker-compose up -d                  # Start in background
docker-compose down                   # Stop all services
docker-compose restart <service>      # Restart specific service
docker-compose logs -f <service>      # Follow logs

# Building
docker-compose build                  # Build all services
docker-compose build --no-cache       # Build without cache
docker-compose pull                   # Pull latest base images

# Debugging  
docker-compose exec <service> bash    # Shell access
docker-compose ps                     # Service status
docker-compose top                    # Process list

# Cleanup
docker-compose down -v                # Remove volumes
docker system prune -a               # Clean everything
docker-compose rm -f                 # Remove stopped containers
```

The Docker setup is designed for both development ease and production readiness, with proper health checks, optimized builds, and comprehensive logging.
