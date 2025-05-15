#!/bin/bash

############################## definição de funções ############################
# Definição de cores para a saída no terminal
GREEN_COLOR='\033[0;32m'   # Cor verde para sucesso
ORANGE_COLOR='\033[0;33m'  # Cor laranja para avisos
RED_COLOR='\033[0;31m'     # Cor vermelha para erros
BLUE_COLOR='\033[0;34m'    # Cor azul para informações
NO_COLOR='\033[0m'         # Cor neutra para resetar as cores no terminal

# Função para exibir avisos com a cor laranja
function echo_warning() {
  echo "${@:3}" -e "$ORANGE_COLOR WARN: $1$NO_COLOR"
}

# Função para exibir erros com a cor vermelha
function echo_error() {
  echo "${@:3}" -e "$RED_COLOR DANG: $1$NO_COLOR"
}

# Função para exibir informações com a cor azul
function echo_info() {
  echo "${@:3}" -e "$BLUE_COLOR INFO: $1$NO_COLOR"
}

# Função para exibir mensagens de sucesso com a cor verde
function echo_success() {
  echo "${@:3}" -e "$GREEN_COLOR SUCC: $1$NO_COLOR"
}

function aguardar_container_healthy() {
  local container_name="$1"
  local timeout="${2:-60}"  # Timeout em segundos (padrão: 60)
  local intervalo=2         # Intervalo entre tentativas
  local tempo_total=0

  echo ""
  echo_info "Aguardando o container '$container_name' ficar com status 'healthy' (timeout: ${timeout}s)..."

  while true; do
    local status
    status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null)

    if [[ "$status" == "healthy" ]]; then
      echo_success "Container '$container_name' está saudável!"
      return 0
    elif [[ "$status" == "unhealthy" ]]; then
      echo_error "Container '$container_name' está com status 'unhealthy'."
      return 1
    elif [[ "$tempo_total" -ge "$timeout" ]]; then
      echo_error "Timeout de $timeout segundos atingido. O container '$container_name' não ficou saudável."
      return 1
    fi

    sleep "$intervalo"
    tempo_total=$((tempo_total + intervalo))
  done
}

function iniciar_e_verificar_servicos() {
  local timeout="${1:-120}"
  shift
  local services=("$@")

  echo ""
  echo "--- Iniciando os containers do ambiente completo..."

  local services_ok=0

  for service in "${services[@]}"; do
    if ! docker compose ps --services --filter "status=running" | grep -q "^$service$"; then
      echo_warning "Serviço '$service' não está em execução."
      services_ok=1
    fi
  done

  if [[ $services_ok -eq 1 ]]; then
    echo_info "--- Tentando subir os serviços ..."
    docker compose up -d --remove-orphans
  fi

  echo ""
  echo "--- Verificando status dos serviços principais..."
  services_ok=0

  for service in "${services[@]}"; do
    if ! aguardar_container_healthy "$service" "$timeout"; then
      services_ok=1
    fi
  done

  return $services_ok
}

####################### Preparação e configuração do ambiente #######################
WORK_DIR="/app"
DIR_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${DIR_ROOT}/.env"
ENV_EXAMPLE="${DIR_ROOT}/.env.example"

# Verifica se o .env existe, se não existir, cria a partir do .env.example
if [[ ! -f "$ENV_FILE" ]]; then
  echo "--- Arquivo .env não encontrado. Criando a partir de .env.example..."
  if [[ ! -f "$ENV_EXAMPLE" ]]; then
    echo "Erro: .env.example não encontrado para gerar o .env"
    exit 1
  fi
  echo "--- Criando .env a partir de .env.example..."
  cp "$ENV_EXAMPLE" "$ENV_FILE"
  echo_success "--- Arquivo .env criado com sucesso."
fi

# Converte .env para LF (Unix)
sed -i 's/\r$//' "$ENV_FILE"

# Gera tokens com Python
TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(16))")
SECRET=$(python3 -c "import secrets; print(secrets.token_hex(16))")

# Substitui valores no .env
sed -i "s|seu_token_aqui|$TOKEN|" "$ENV_FILE"
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET|" "$ENV_FILE"
sed -i "s|https://url.da.aplicacao|http://localhost:5000/|" "$ENV_FILE"

echo_success "--- Variáveis de ambiente atualizadas com sucesso."
# Exibe tokens gerados (opcional para debug)
echo "--- TOKEN gerado: $TOKEN"
echo "--- SECRET_KEY gerado: $SECRET"


echo "--- Carregando variáveis do .env..."
set -o allexport
source "$ENV_FILE"
set +o allexport

################################ Inicialização #################################
echo "--- Gerando arquivos falsos de teste com faker-file..."
docker compose exec web python src/utils/generate_fake_files.py

iniciar_e_verificar_servicos 120 "${COMPOSE_PROJECT_NAME}-web-1"

# Remover somente os diretórios que começam com números dentro de src/static/, garantindo que as pastas css e exports não sejam removidas,
docker compose exec web bash -c 'find src/static -maxdepth 1 -type d -regex ".*/[0-9].*" ! -name css ! -name exports -exec rm -rf {} +'

# --service-ports para que as portas expostas no docker-compose.yml também sejam mapeadas no run.
# --it para que o terminal seja interativo.
docker compose exec -w $WORK_DIR -it web pytest -v --capture=tee-sys --tb=short

echo "--- Apagando arquivos falsos de teste com faker-file..."
docker compose exec web bash -c 'rm -f tests/files/tmp*.*'

