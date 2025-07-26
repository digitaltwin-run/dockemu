.PHONY: help build up down clean logs status test-all restart
.DEFAULT_GOAL := help

# Project configuration
PROJECT_NAME := c20-hardware-simulator
COMPOSE_FILE := docker-compose.yml

help: ## Show this help message
	@echo "$(PROJECT_NAME) - Docker Environment Management"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	@echo "🔨 Building all containers..."
	docker-compose -f $(COMPOSE_FILE) build

up: build ## Build and start all services
	@echo "🚀 Starting all services..."
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo ""
	@echo "✅ Services are starting up!"
	@echo "📱 Access points:"
	@echo "   • Main Dashboard: http://localhost:8088"
	@echo "   • LCD Display:    http://localhost:8091"
	@echo "   • HUI Keyboard:   http://localhost:8092"
	@echo "   • Modbus Visual:  http://localhost:8084"
	@echo "   • Unified View:   http://localhost:8085"
	@echo ""

down: ## Stop and remove all containers
	@echo "🛑 Stopping all services..."
	docker-compose -f $(COMPOSE_FILE) down

clean: down ## Stop containers and remove images, volumes
	@echo "🧹 Cleaning up containers, images, and volumes..."
	docker-compose -f $(COMPOSE_FILE) down -v --rmi all
	docker system prune -f

logs: ## Show logs from all services
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-service: ## Show logs from specific service (usage: make logs-service SERVICE=rpi)
	@if [ -z "$(SERVICE)" ]; then echo "❌ Please specify SERVICE, e.g.: make logs-service SERVICE=rpi"; exit 1; fi
	docker-compose -f $(COMPOSE_FILE) logs -f $(SERVICE)

status: ## Show status of all containers
	@echo "📊 Container Status:"
	docker-compose -f $(COMPOSE_FILE) ps

restart: ## Restart all services
	@echo "🔄 Restarting all services..."
	docker-compose -f $(COMPOSE_FILE) restart

restart-service: ## Restart specific service (usage: make restart-service SERVICE=rpi)
	@if [ -z "$(SERVICE)" ]; then echo "❌ Please specify SERVICE, e.g.: make restart-service SERVICE=rpi"; exit 1; fi
	docker-compose -f $(COMPOSE_FILE) restart $(SERVICE)

shell: ## Open shell in specific container (usage: make shell SERVICE=rpi)
	@if [ -z "$(SERVICE)" ]; then echo "❌ Please specify SERVICE, e.g.: make shell SERVICE=rpi"; exit 1; fi
	docker-compose -f $(COMPOSE_FILE) exec $(SERVICE) /bin/bash

test-all: ## Run all test procedures
	@echo "🧪 Running all test procedures..."
	docker-compose -f $(COMPOSE_FILE) exec rpi python3 /shared/test_all.py

test-bls: ## Run BLS mask tests
	@echo "🧪 Running BLS mask tests..."
	docker-compose -f $(COMPOSE_FILE) exec rpi python3 -m pytest /app/test-procedures/bls_tests.py -v

test-modbus: ## Test Modbus communication
	@echo "🧪 Testing Modbus communication..."
	docker-compose -f $(COMPOSE_FILE) exec modbus-io-8ch python3 /app/test_modbus.py

dev: ## Start services in development mode (with file watching)
	@echo "🛠️  Starting in development mode..."
	docker-compose -f $(COMPOSE_FILE) -f docker-compose.dev.yml up

install: ## Install project dependencies and setup
	@echo "📦 Setting up project..."
	@if [ ! -d "./mosquitto/config" ]; then mkdir -p ./mosquitto/config; fi
	@if [ ! -f "./mosquitto/config/mosquitto.conf" ]; then \
		echo "listener 1883" > ./mosquitto/config/mosquitto.conf; \
		echo "listener 9001" >> ./mosquitto/config/mosquitto.conf; \
		echo "protocol websockets" >> ./mosquitto/config/mosquitto.conf; \
		echo "allow_anonymous true" >> ./mosquitto/config/mosquitto.conf; \
	fi
	@echo "✅ Project setup complete!"

monitoring: ## Show real-time resource usage
	@echo "📈 Resource monitoring (Press Ctrl+C to exit):"
	watch -n 2 'docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.PIDs}}"'

backup: ## Create backup of project data
	@echo "💾 Creating backup..."
	@mkdir -p ./backups
	@tar -czf ./backups/c20-backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		--exclude='./backups' \
		--exclude='./.git' \
		--exclude='./.mypy_cache' \
		--exclude='./.idea' \
		.
	@echo "✅ Backup created in ./backups/"

quick-start: install up ## Quick project setup and start
	@echo ""
	@echo "🎉 C20 Hardware Simulator is ready!"
	@echo "Open http://localhost:8085 for the unified dashboard"
