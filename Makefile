# Caminhos e nomes importantes
COMPOSE_FILE=docker-compose.yml
SERVICE_NAME=web
STATIC_DIR=src/static

# Informa ao Makefile que os alvos não representam arquivos
.PHONY: up down ps clean tests logs

## Sobe os containers com build
up:
	docker compose -f $(COMPOSE_FILE) up -d --build

## Derruba todos os containers
down:
	docker compose -f $(COMPOSE_FILE) down --remove-orphans

## Exibe o status dos containers
ps:
	docker compose -f $(COMPOSE_FILE) ps

## Remove diretórios numéricos de static/, preservando css e exports
clean:
	docker compose exec $(SERVICE_NAME) bash -c 'find $(STATIC_DIR) -maxdepth 1 -type d -regex ".*/[0-9].*" ! -name css ! -name exports -exec rm -rf {} +'

## Executa os testes com pytest de forma interativa
tests:
	./run_tests.sh

## Exibe os logs do serviço principal
logs:
	docker compose logs -f $(SERVICE_NAME)
