# ═══════════════════════════════════════════════════════════════════
# Makefile for DRDO Equipment Maintenance System
# Simplified Docker management commands
# ═══════════════════════════════════════════════════════════════════

.PHONY: help build up down restart logs status clean test health prune

# Default target
.DEFAULT_GOAL := help

# Colors
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

##@ General

help: ## Display this help message
	@echo "$(CYAN)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(CYAN)  DRDO Equipment Maintenance - Docker Commands$(NC)"
	@echo "$(CYAN)═══════════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make $(CYAN)<target>$(NC)\n\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Build & Deploy

build: ## Build all Docker images
	@echo "$(CYAN)Building Docker images...$(NC)"
	@docker-compose build --parallel

build-no-cache: ## Build all Docker images without cache
	@echo "$(CYAN)Building Docker images (no cache)...$(NC)"
	@docker-compose build --no-cache --parallel

up: ## Start all services in detached mode
	@echo "$(CYAN)Starting all services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@make status

down: ## Stop and remove all containers
	@echo "$(YELLOW)Stopping all services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

restart: ## Restart all services
	@echo "$(CYAN)Restarting all services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

##@ Monitoring

logs: ## View logs from all services (follow mode)
	@docker-compose logs -f

logs-service: ## View logs from specific service (usage: make logs-service SERVICE=sensor-ingestion)
	@docker-compose logs -f $(SERVICE)

status: ## Show status of all services
	@echo "$(CYAN)Service Status:$(NC)"
	@docker-compose ps

ps: status ## Alias for status

health: ## Check health of all services
	@echo "$(CYAN)Health Checks:$(NC)"
	@echo "Sensor Ingestion:  $$(curl -s http://localhost:8001/health | grep -q status && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)')"
	@echo "ML Prediction:     $$(curl -s http://localhost:8002/health | grep -q status && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)')"
	@echo "Alert Maintenance: $$(curl -s http://localhost:8003/health | grep -q status && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)')"
	@echo "Dashboard:         $$(curl -s http://localhost:8004/_stcore/health | grep -q healthy && echo '$(GREEN)✓$(NC)' || echo '$(RED)✗$(NC)')"

##@ Database

db-shell: ## Open PostgreSQL shell
	@docker-compose exec postgres psql -U drdo -d equipment_maintenance

db-backup: ## Backup PostgreSQL database
	@echo "$(CYAN)Creating database backup...$(NC)"
	@docker-compose exec -T postgres pg_dump -U drdo equipment_maintenance > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Backup created$(NC)"

redis-cli: ## Open Redis CLI
	@docker-compose exec redis redis-cli

##@ Cleanup

clean: ## Stop containers and remove volumes
	@echo "$(YELLOW)Stopping services and removing volumes...$(NC)"
	@docker-compose down -v
	@echo "$(GREEN)✓ Cleaned up$(NC)"

prune: ## Remove unused Docker resources
	@echo "$(YELLOW)Pruning Docker system...$(NC)"
	@docker system prune -f
	@echo "$(GREEN)✓ Pruned$(NC)"

prune-all: ## Remove ALL unused Docker resources (including volumes)
	@echo "$(RED)⚠️  WARNING: This will remove ALL unused Docker resources!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker system prune -af --volumes; \
		echo "$(GREEN)✓ All unused resources removed$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

##@ Development

shell: ## Open shell in specific service (usage: make shell SERVICE=sensor-ingestion)
	@docker-compose exec $(SERVICE) /bin/bash

test: ## Run health checks on all services
	@echo "$(CYAN)Running health checks...$(NC)"
	@make health

dev: ## Start services and follow logs
	@make up
	@make logs

##@ Quick Actions

stop-service: ## Stop specific service (usage: make stop-service SERVICE=sensor-ingestion)
	@docker-compose stop $(SERVICE)
	@echo "$(GREEN)✓ $(SERVICE) stopped$(NC)"

start-service: ## Start specific service (usage: make start-service SERVICE=sensor-ingestion)
	@docker-compose start $(SERVICE)
	@echo "$(GREEN)✓ $(SERVICE) started$(NC)"

restart-service: ## Restart specific service (usage: make restart-service SERVICE=sensor-ingestion)
	@docker-compose restart $(SERVICE)
	@echo "$(GREEN)✓ $(SERVICE) restarted$(NC)"

##@ Information

images: ## List all Docker images
	@docker images | grep drdo

volumes: ## List all Docker volumes
	@docker volume ls | grep drdo

networks: ## List all Docker networks
	@docker network ls | grep drdo

stats: ## Show container resource usage
	@docker stats --no-stream
