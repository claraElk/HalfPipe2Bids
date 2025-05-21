.PHONY:help

help: ## Prints this help message
	@grep -E '^[a-zA-Z_-]+:.*## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build_dev: ## Build the dev image
	@docker build -t halfpipetobids:dev -f docker/Dockerfile.dev .

run_dev: ## Run the dev image
	@docker compose -f docker-compose_dev.yml up

stop_dev: ## Stop the dev image
	@docker compose -f docker-compose_dev.yml down