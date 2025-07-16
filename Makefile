# TimeL-E Project Makefile

.PHONY: help build-backend run-backend backend build-db run-db build-all up down clean

# Default target
help:
	@echo "TimeL-E Project Commands:"
	@echo "  build-backend    Build backend Docker image"
	@echo "  run-backend      Run backend container on port 8000"
	@echo "  backend          Build and run backend (shortcut)"
	@echo "  build-db         Build database service image"
	@echo "  run-db           Run database services (postgres + db-service)"
	@echo "  build-all        Build all services"
	@echo "  up               Start all services with docker-compose"
	@echo "  down             Stop all services"
	@echo "  clean            Remove all images and containers"
	@echo "  test-backend     Test backend API endpoints"

# Backend commands
build-backend:
	@echo "Building backend Docker image..."
	docker build -t timel-e-backend ./backend

run-backend:
	@echo "Running backend container on port 8000..."
	docker run -p 8000:8000 --name timel-e-backend-container timel-e-backend

backend: build-backend
	@echo "Starting backend container..."
	@docker stop timel-e-backend-container 2>/dev/null || true
	@docker rm timel-e-backend-container 2>/dev/null || true
	docker run -p 8000:8000 --name timel-e-backend-container timel-e-backend

# Database commands
build-db:
	@echo "Building database service image..."
	docker build -t timel-e-db-service ./db_service

run-db:
	@echo "Starting database services..."
	docker-compose up postgres db-service -d

# Full project commands
build-all:
	@echo "Building all services..."
	docker-compose build

up:
	@echo "Starting all services..."
	docker-compose up --build

down:
	@echo "Stopping all services..."
	docker-compose down

# Utility commands
clean:
	@echo "Cleaning up containers and images..."
	docker-compose down --volumes --remove-orphans
	docker system prune -f

test-backend:
	@echo "Testing backend API..."
	@curl -s http://localhost:8000/health | head -n 1 || echo "Backend not running on port 8000"
	@curl -s http://localhost:8000/ | head -n 1 || echo "Backend API not responding"

# Development shortcuts
dev-backend: backend
	@echo "Backend running on http://localhost:8000"
	@echo "API Documentation: http://localhost:8000/docs"
	@echo "Health Check: http://localhost:8000/health"
	@echo "Press Ctrl+C to stop"
