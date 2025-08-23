#!/bin/bash

# run_agent_evaluation.sh - Interface de Linha de Comando para Avaliação de Agentes
# 
# Este script fornece uma interface simples para executar o sistema de avaliação
# de agentes do Conductor, oferecendo diferentes modos de execução e configurações.

set -e

# Configurações padrão
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDUCTOR_PATH="$(dirname "$SCRIPT_DIR")"
EVALUATION_CASES_DIR="$CONDUCTOR_PATH/evaluation_cases"
WORKING_DIR="/tmp/agent_evaluation_$(date +%Y%m%d_%H%M%S)"
VERBOSE=false
DRY_RUN=false
OUTPUT_FORMAT="both"
QUIET=false

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Função para exibir ajuda
show_help() {
    cat << EOF
$(printf "${BLUE}Agent Evaluation Framework - Interface CLI${NC}")

$(printf "${GREEN}DESCRIÇÃO:${NC}")
    Interface de linha de comando para o sistema de avaliação de agentes do Conductor.
    Permite executar testes, avaliar performance e gerar relatórios automaticamente.

$(printf "${GREEN}USO:${NC}")
    $0 [OPÇÕES]

$(printf "${GREEN}OPÇÕES:${NC}")
    $(printf "${YELLOW}--agent AGENT_NAME${NC}")          Avaliar agente específico
    $(printf "${YELLOW}--all${NC}")                       Avaliar todos os agentes disponíveis
    $(printf "${YELLOW}--test-file FILE${NC}")            Usar arquivo de teste específico
    $(printf "${YELLOW}--test-id ID${NC}")                Executar apenas teste específico
    $(printf "${YELLOW}--working-dir DIR${NC}")           Diretório de trabalho (padrão: /tmp/agent_evaluation_TIMESTAMP)
    $(printf "${YELLOW}--output-format FORMAT${NC}")      Formato do relatório: markdown, json, both (padrão: both)
    $(printf "${YELLOW}--dry-run${NC}")                   Simular sem atualizar arquivos de memória
    $(printf "${YELLOW}--verbose${NC}")                   Saída detalhada
    $(printf "${YELLOW}--quiet${NC}")                     Saída mínima
    $(printf "${YELLOW}--help${NC}")                      Mostrar esta ajuda

$(printf "${GREEN}EXEMPLOS:${NC}")
    # Avaliar agente específico
    $0 --agent AgentCreator_Agent
    
    # Avaliar todos os agentes
    $0 --all
    
    # Execução em modo dry-run com saída detalhada
    $0 --agent AgentCreator_Agent --dry-run --verbose
    
    # Executar teste específico
    $0 --agent AgentCreator_Agent --test-id create_simple_agent
    
    # Gerar apenas relatório JSON
    $0 --agent OnboardingGuide_Agent --output-format json

$(printf "${GREEN}SAÍDA:${NC}")
    Os resultados são salvos automaticamente em:
    $(printf "${YELLOW}projects/conductor/.evaluation_output/TIMESTAMP_AGENTNAME/${NC}")
    
    Cada execução cria um diretório único com timestamp para evitar conflitos.

$(printf "${GREEN}ARQUIVOS DE TESTE:${NC}")
    Os casos de teste devem estar em: $(printf "${YELLOW}$EVALUATION_CASES_DIR${NC}")
    
    Arquivos disponíveis:
$(ls -1 "$EVALUATION_CASES_DIR"/*.yaml 2>/dev/null | sed 's/^/    - /' || echo "    (Nenhum arquivo encontrado)")

$(printf "${GREEN}AGENTES DISPONÍVEIS:${NC}")
$(find "$CONDUCTOR_PATH/projects" -name "*_Agent" -type d | grep -E "(/_common/agents/|/agents/)" | basename -a | sort -u | sed 's/^/    - /' 2>/dev/null || echo "    (Nenhum agente encontrado)")

EOF
}

# Função para log com cores
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%H:%M:%S')
    
    case $level in
        "INFO")
            [[ $QUIET != true ]] && printf "${BLUE}[$timestamp]${NC} $message\n"
            ;;
        "SUCCESS")
            printf "${GREEN}[$timestamp] ✓${NC} $message\n"
            ;;
        "WARNING")
            printf "${YELLOW}[$timestamp] ⚠${NC} $message\n"
            ;;
        "ERROR")
            printf "${RED}[$timestamp] ✗${NC} $message\n" >&2
            ;;
        "RESULT")
            printf "${PURPLE}[$timestamp] 📊${NC} $message\n"
            ;;
    esac
}

# Função para verificar dependências
check_dependencies() {
    log "INFO" "Verificando dependências..."
    
    if ! command -v python3 &> /dev/null; then
        log "ERROR" "Python 3 não encontrado. Instale Python 3.8+ para continuar."
        exit 1
    fi
    
    if ! python3 -c "import yaml" 2>/dev/null; then
        log "ERROR" "Biblioteca PyYAML não encontrada. Execute: pip install pyyaml"
        exit 1
    fi
    
    if [[ ! -f "$SCRIPT_DIR/agent_evaluator.py" ]]; then
        log "ERROR" "Script agent_evaluator.py não encontrado em $SCRIPT_DIR"
        exit 1
    fi
    
    log "SUCCESS" "Dependências verificadas"
}

# Função para listar agentes disponíveis
list_available_agents() {
    log "INFO" "Buscando agentes disponíveis..."
    
    local agents=()
    while IFS= read -r -d '' agent_dir; do
        agent_name=$(basename "$agent_dir")
        if [[ $agent_name == *"_Agent" ]]; then
            agents+=("$agent_name")
        fi
    done < <(find "$CONDUCTOR_PATH/projects" -name "*_Agent" -type d -print0 2>/dev/null)
    
    if [[ ${#agents[@]} -eq 0 ]]; then
        log "WARNING" "Nenhum agente encontrado"
        return 1
    fi
    
    printf "%s\n" "${agents[@]}" | sort -u
}

# Função para encontrar arquivo de teste para um agente
find_test_file() {
    local agent_name=$1
    local test_files=(
        "$EVALUATION_CASES_DIR/test_${agent_name,,}.yaml"
        "$EVALUATION_CASES_DIR/test_$(echo $agent_name | sed 's/_Agent$//' | tr '[:upper:]' '[:lower:]').yaml"
        "$EVALUATION_CASES_DIR/test_$(echo $agent_name | tr '[:upper:]' '[:lower:]').yaml"
    )
    
    for file in "${test_files[@]}"; do
        if [[ -f "$file" ]]; then
            echo "$file"
            return 0
        fi
    done
    
    # Se não encontrou arquivo específico, procura em todos os arquivos
    for file in "$EVALUATION_CASES_DIR"/*.yaml; do
        if [[ -f "$file" ]] && grep -q "target_agent: .*$agent_name" "$file" 2>/dev/null; then
            echo "$file"
            return 0
        fi
    done
    
    return 1
}

# Função para executar avaliação de um agente
evaluate_single_agent() {
    local agent_name=$1
    local test_file=$2
    
    log "INFO" "Iniciando avaliação do agente: $agent_name"
    
    if [[ -z "$test_file" ]]; then
        test_file=$(find_test_file "$agent_name")
        if [[ $? -ne 0 ]]; then
            log "ERROR" "Arquivo de teste não encontrado para $agent_name"
            return 1
        fi
    fi
    
    if [[ ! -f "$test_file" ]]; then
        log "ERROR" "Arquivo de teste não existe: $test_file"
        return 1
    fi
    
    log "INFO" "Usando arquivo de teste: $test_file"
    
    # Preparar argumentos para o script Python
    local python_args=(
        "--agent" "$agent_name"
        "--test-file" "$test_file"
        "--working-dir" "$WORKING_DIR"
        "--conductor-path" "$CONDUCTOR_PATH"
        "--output-format" "$OUTPUT_FORMAT"
    )
    
    [[ $DRY_RUN == true ]] && python_args+=("--dry-run")
    [[ $VERBOSE == true ]] && python_args+=("--verbose")
    [[ -n "$TEST_ID" ]] && python_args+=("--test-id" "$TEST_ID")
    
    # Executar avaliação
    log "INFO" "Executando avaliação..."
    if python3 "$SCRIPT_DIR/agent_evaluator.py" "${python_args[@]}"; then
        log "SUCCESS" "Avaliação concluída para $agent_name"
        return 0
    else
        log "ERROR" "Falha na avaliação de $agent_name"
        return 1
    fi
}

# Função para executar avaliação de todos os agentes
evaluate_all_agents() {
    log "INFO" "Iniciando avaliação de todos os agentes..."
    
    local agents
    local agent_list
    agent_list=$(list_available_agents)
    local list_exit_code=$?
    
    if [[ $list_exit_code -ne 0 ]] || [[ -z "$agent_list" ]]; then
        log "ERROR" "Falha ao listar agentes disponíveis (código: $list_exit_code)"
        return 1
    fi
    
    mapfile -t agents <<< "$agent_list"
    
    if [[ ${#agents[@]} -eq 0 ]]; then
        log "ERROR" "Nenhum agente encontrado para avaliação"
        return 1
    fi
    
    local success_count=0
    local total_count=${#agents[@]}
    
    log "INFO" "Encontrados $total_count agentes para avaliação"
    
    for agent in "${agents[@]}"; do
        log "INFO" "--- Avaliando $agent ($(($success_count + 1))/$total_count) ---"
        
        if evaluate_single_agent "$agent" ""; then
            ((success_count++))
        fi
        
        echo # Linha em branco para separação
    done
    
    log "RESULT" "Avaliação concluída: $success_count/$total_count agentes avaliados com sucesso"
    
    if [[ $success_count -lt $total_count ]]; then
        return 1
    fi
}

# Função para limpar recursos
cleanup() {
    if [[ -d "$WORKING_DIR" ]]; then
        log "INFO" "Limpando diretório temporário: $WORKING_DIR"
        rm -rf "$WORKING_DIR"
    fi
}

# Função principal
main() {
    local agent_name=""
    local test_file=""
    local evaluate_all=false
    
    # Parse dos argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --agent)
                agent_name="$2"
                shift 2
                ;;
            --all)
                evaluate_all=true
                shift
                ;;
            --test-file)
                test_file="$2"
                shift 2
                ;;
            --test-id)
                TEST_ID="$2"
                shift 2
                ;;
            --working-dir)
                WORKING_DIR="$2"
                shift 2
                ;;
            --output-format)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --quiet)
                QUIET=true
                VERBOSE=false
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log "ERROR" "Opção desconhecida: $1"
                echo
                show_help
                exit 1
                ;;
        esac
    done
    
    # Configurar saída silenciosa
    if [[ $QUIET == true ]]; then
        exec 1>/dev/null
    fi
    
    # Validar argumentos
    if [[ $evaluate_all == false && -z "$agent_name" ]]; then
        log "ERROR" "Especifique --agent AGENT_NAME ou --all"
        echo
        show_help
        exit 1
    fi
    
    if [[ $evaluate_all == true && -n "$agent_name" ]]; then
        log "ERROR" "Não é possível usar --all e --agent ao mesmo tempo"
        exit 1
    fi
    
    # Verificar dependências
    check_dependencies
    
    # Criar diretórios
    mkdir -p "$WORKING_DIR"
    mkdir -p "$CONDUCTOR_PATH/.evaluation_output"
    
    # Configurar limpeza automática
    trap cleanup EXIT
    
    # Executar avaliação
    log "INFO" "=== Agent Evaluation Framework - Iniciando ==="
    [[ $DRY_RUN == true ]] && log "WARNING" "Modo DRY-RUN ativado - arquivos de memória não serão alterados"
    
    local exit_code=0
    
    if [[ $evaluate_all == true ]]; then
        evaluate_all_agents || exit_code=1
    else
        evaluate_single_agent "$agent_name" "$test_file" || exit_code=1
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        log "SUCCESS" "=== Avaliação concluída com sucesso ==="
        [[ $QUIET == false ]] && log "RESULT" "Resultados salvos em: $CONDUCTOR_PATH/.evaluation_output/"
    else
        log "ERROR" "=== Avaliação concluída com erros ==="
    fi
    
    exit $exit_code
}

# Executar função principal com todos os argumentos
main "$@"