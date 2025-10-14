#!/bin/bash

# Claude MongoDB Watcher Runner Script
# Este script facilita a execução do claude-mongo-watcher.py com diferentes configurações

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações padrão (usando variáveis de ambiente)
DEFAULT_MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
DEFAULT_DATABASE="${MONGO_DATABASE:-conductor_state}"
DEFAULT_COLLECTION="${MONGO_COLLECTION:-tasks}"
DEFAULT_POLL_INTERVAL="${POLL_INTERVAL:-1.0}"
DEFAULT_LOG_FILE="${LOG_FILE:-/tmp/claude-watcher.log}"

# Caminho para o script
WATCHER_SCRIPT="poc/container_to_host/claude-mongo-watcher.py"

# Função para mostrar ajuda
show_help() {
    echo -e "${BLUE}Claude MongoDB Watcher Runner${NC}"
    echo ""
    echo "Uso: $0 [OPÇÕES]"
    echo ""
    echo "Opções:"
    echo "  -u, --mongo-uri URI        URI de conexão MongoDB (padrão: $DEFAULT_MONGO_URI)"
    echo "  -d, --database DB          Nome do database (padrão: $DEFAULT_DATABASE)"
    echo "  -c, --collection COL       Nome da collection (padrão: $DEFAULT_COLLECTION)"
    echo "  -i, --poll-interval SEC    Intervalo entre verificações em segundos (padrão: $DEFAULT_POLL_INTERVAL)"
    echo "  -l, --log-file FILE        Arquivo de log (padrão: $DEFAULT_LOG_FILE)"
    echo "  -b, --background           Executar em background (nohup)"
    echo "  -k, --kill                 Matar processos existentes do watcher"
    echo "  -s, --status               Mostrar status dos processos"
    echo "  -t, --tail                 Mostrar últimas linhas do log"
    echo "  --test-connection          Testar conexão MongoDB"
    echo "  -h, --help                 Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0                                    # Usar configurações padrão"
    echo "  $0 -u mongodb://localhost:27017      # URI customizada"
    echo "  $0 -d conductor -c tasks             # Database e collection customizados"
    echo "  $0 -i 2.0 -b                         # Poll interval 2s em background"
    echo "  $0 -k                                 # Parar watchers existentes"
    echo "  $0 -s                                 # Ver status"
    echo "  $0 -t                                 # Ver log"
}

# Função para verificar se o script existe
check_script() {
    if [ ! -f "$WATCHER_SCRIPT" ]; then
        echo -e "${RED}❌ Erro: Script $WATCHER_SCRIPT não encontrado${NC}"
        echo "Execute este script a partir do diretório projects/conductor/"
        exit 1
    fi
}

# Função para matar processos existentes
kill_existing() {
    echo -e "${YELLOW}🔍 Procurando processos existentes do claude-mongo-watcher...${NC}"
    
    PIDS=$(pgrep -f "claude-mongo-watcher" || true)
    
    if [ -z "$PIDS" ]; then
        echo -e "${GREEN}✅ Nenhum processo encontrado${NC}"
    else
        echo -e "${YELLOW}📋 Processos encontrados: $PIDS${NC}"
        echo -e "${YELLOW}🛑 Matando processos...${NC}"
        pkill -f "claude-mongo-watcher" || true
        sleep 2
        
        # Verificar se ainda existem processos
        REMAINING=$(pgrep -f "claude-mongo-watcher" || true)
        if [ -n "$REMAINING" ]; then
            echo -e "${RED}⚠️  Ainda existem processos: $REMAINING${NC}"
            echo -e "${YELLOW}💀 Forçando kill...${NC}"
            pkill -9 -f "claude-mongo-watcher" || true
        fi
        
        echo -e "${GREEN}✅ Processos finalizados${NC}"
    fi
}

# Função para mostrar status
show_status() {
    echo -e "${BLUE}📊 Status do Claude MongoDB Watcher${NC}"
    echo ""
    
    PIDS=$(pgrep -f "claude-mongo-watcher" || true)
    
    if [ -z "$PIDS" ]; then
        echo -e "${RED}❌ Nenhum processo ativo${NC}"
    else
        echo -e "${GREEN}✅ Processos ativos:${NC}"
        ps aux | grep "claude-mongo-watcher" | grep -v grep || true
        echo ""
        echo -e "${BLUE}📋 Argumentos dos processos:${NC}"
        ps aux | grep "claude-mongo-watcher" | grep -v grep | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}' || true
    fi
    
    echo ""
    if [ -f "$DEFAULT_LOG_FILE" ]; then
        echo -e "${BLUE}📄 Log file: $DEFAULT_LOG_FILE${NC}"
        echo -e "${BLUE}📏 Tamanho: $(du -h "$DEFAULT_LOG_FILE" | cut -f1)${NC}"
        echo -e "${BLUE}🕒 Última modificação: $(stat -c %y "$DEFAULT_LOG_FILE")${NC}"
    else
        echo -e "${YELLOW}⚠️  Log file não encontrado: $DEFAULT_LOG_FILE${NC}"
    fi
}

# Função para mostrar tail do log
show_tail() {
    if [ -f "$DEFAULT_LOG_FILE" ]; then
        echo -e "${BLUE}📄 Últimas 20 linhas do log:${NC}"
        echo ""
        tail -20 "$DEFAULT_LOG_FILE"
    else
        echo -e "${RED}❌ Log file não encontrado: $DEFAULT_LOG_FILE${NC}"
    fi
}

# Função para testar conexão
test_connection() {
    local mongo_uri="$1"
    local database="$2"
    local collection="$3"
    
    echo -e "${BLUE}🔍 Testando conexão MongoDB...${NC}"
    echo -e "   URI: $mongo_uri"
    echo -e "   Database: $database"
    echo -e "   Collection: $collection"
    echo ""
    
    # Testar conexão com timeout
    timeout 10 python3 "$WATCHER_SCRIPT" --mongo-uri "$mongo_uri" --database "$database" --collection "$collection" --poll-interval 10.0 &
    local pid=$!
    
    # Aguardar um pouco para ver se conecta
    sleep 3
    
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ Conexão bem-sucedida!${NC}"
        echo -e "${YELLOW}🛑 Parando teste...${NC}"
        kill $pid 2>/dev/null || true
        wait $pid 2>/dev/null || true
    else
        echo -e "${RED}❌ Falha na conexão${NC}"
    fi
}

# Função para executar o watcher
run_watcher() {
    local mongo_uri="$1"
    local database="$2"
    local collection="$3"
    local poll_interval="$4"
    local log_file="$5"
    local background="$6"
    
    echo -e "${BLUE}🚀 Iniciando Claude MongoDB Watcher${NC}"
    echo -e "${BLUE}📊 Configurações:${NC}"
    echo -e "   MongoDB URI: $mongo_uri"
    echo -e "   Database: $database"
    echo -e "   Collection: $collection"
    echo -e "   Poll Interval: ${poll_interval}s"
    echo -e "   Log File: $log_file"
    echo -e "   Background: $background"
    echo ""
    
    # Montar comando
    CMD="python3 $WATCHER_SCRIPT --mongo-uri '$mongo_uri' --database '$database' --collection '$collection' --poll-interval $poll_interval"
    
    if [ "$background" = "true" ]; then
        echo -e "${YELLOW}🔄 Executando em background...${NC}"
        nohup bash -c "$CMD" > "$log_file" 2>&1 &
        echo -e "${GREEN}✅ Watcher iniciado em background (PID: $!)${NC}"
        echo -e "${BLUE}📄 Log sendo escrito em: $log_file${NC}"
        echo -e "${BLUE}💡 Use '$0 -s' para ver status ou '$0 -t' para ver log${NC}"
    else
        echo -e "${YELLOW}🔄 Executando em foreground...${NC}"
        echo -e "${BLUE}💡 Use Ctrl+C para parar${NC}"
        echo ""
        exec bash -c "$CMD"
    fi
}

# Parse dos argumentos
MONGO_URI="$DEFAULT_MONGO_URI"
DATABASE="$DEFAULT_DATABASE"
COLLECTION="$DEFAULT_COLLECTION"
POLL_INTERVAL="$DEFAULT_POLL_INTERVAL"
LOG_FILE="$DEFAULT_LOG_FILE"
BACKGROUND="false"
KILL_ONLY="false"
STATUS_ONLY="false"
TAIL_ONLY="false"
TEST_CONNECTION="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--mongo-uri)
            MONGO_URI="$2"
            shift 2
            ;;
        -d|--database)
            DATABASE="$2"
            shift 2
            ;;
        -c|--collection)
            COLLECTION="$2"
            shift 2
            ;;
        -i|--poll-interval)
            POLL_INTERVAL="$2"
            shift 2
            ;;
        -l|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        -b|--background)
            BACKGROUND="true"
            shift
            ;;
        -k|--kill)
            KILL_ONLY="true"
            shift
            ;;
        -s|--status)
            STATUS_ONLY="true"
            shift
            ;;
        -t|--tail)
            TAIL_ONLY="true"
            shift
            ;;
        --test-connection)
            TEST_CONNECTION="true"
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Opção desconhecida: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Executar ações baseadas nos argumentos
if [ "$KILL_ONLY" = "true" ]; then
    kill_existing
    exit 0
fi

if [ "$STATUS_ONLY" = "true" ]; then
    show_status
    exit 0
fi

if [ "$TAIL_ONLY" = "true" ]; then
    show_tail
    exit 0
fi

if [ "$TEST_CONNECTION" = "true" ]; then
    test_connection "$MONGO_URI" "$DATABASE" "$COLLECTION"
    exit 0
fi

# Verificar se o script existe
check_script

# Se não for apenas teste de conexão, matar processos existentes antes de iniciar
if [ "$TEST_CONNECTION" != "true" ]; then
    echo -e "${YELLOW}🔄 Verificando processos existentes...${NC}"
    kill_existing
    sleep 1  # Aguardar um pouco para garantir que os processos foram finalizados
fi

# Executar o watcher
run_watcher "$MONGO_URI" "$DATABASE" "$COLLECTION" "$POLL_INTERVAL" "$LOG_FILE" "$BACKGROUND"