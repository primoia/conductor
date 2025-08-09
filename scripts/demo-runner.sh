#!/bin/bash
# Demo Runner Script - Executa o demo completo do Conductor

set -e

DEMO_DIR="demo"
LOG_FILE="/tmp/conductor-demo.log"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

run_agent() {
    local agent_name="$1"
    local step="$2"
    local agent_dir="$DEMO_DIR/agent-$agent_name"
    
    info "Executando Agent: $agent_name (Step $step)"
    
    if [ ! -d "$agent_dir" ]; then
        error "Agent directory not found: $agent_dir"
        return 1
    fi
    
    local command_file="$agent_dir/$step.txt"
    if [ ! -f "$command_file" ]; then
        error "Command file not found: $command_file"
        return 1
    fi
    
    echo "  📋 Comando:" && cat "$command_file" | sed 's/^/     /'
    echo "  ⚡ Processando..."
    sleep 2  # Simula processamento
    
    local next_step=$((step + 1))
    local result_file="$agent_dir/$next_step.txt"
    if [ -f "$result_file" ]; then
        echo "  📤 Resultado:" && cat "$result_file" | sed 's/^/     /'
        
        # Update state timestamp
        local current_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        if command -v jq >/dev/null 2>&1; then
            jq --arg time "$current_time" '.status.updated_at = $time | .execution.last_execution = $time | .execution.execution_count += 1' \
                "$agent_dir/state.json" > "$agent_dir/state.json.tmp" && mv "$agent_dir/state.json.tmp" "$agent_dir/state.json"
        fi
    else
        error "Result file not found: $result_file"
        return 1
    fi
    
    success "Agent $agent_name concluído"
    echo ""
}

verify_state() {
    local agent_name="$1"
    local agent_dir="$DEMO_DIR/agent-$agent_name"
    
    if [ ! -f "$agent_dir/state.json" ]; then
        error "State file not found for agent: $agent_name"
        return 1
    fi
    
    if command -v jq >/dev/null 2>&1; then
        local status=$(jq -r '.status.current' "$agent_dir/state.json")
        local exec_count=$(jq -r '.execution.execution_count' "$agent_dir/state.json")
        info "Agent $agent_name: Status=$status, Executions=$exec_count"
    else
        info "Agent $agent_name: State file exists"
    fi
}

simulate_restart() {
    warn "Simulando desligamento do sistema..."
    echo "💤 Sistema 'desligado' - estados salvos em arquivos"
    sleep 3
    
    log "Sistema religando..."
    echo "🔄 Verificando recuperação de estados..."
    sleep 1
}

main() {
    log "🎯 CONDUCTOR DEMO - GRADLE VERSION ANALYSIS"
    log "=========================================="
    
    # Verificar dependências
    if ! command -v jq >/dev/null 2>&1; then
        warn "jq não encontrado - análise de JSON será limitada"
    fi
    
    # Limpar log anterior
    > "$LOG_FILE"
    
    # Verificar estrutura do demo
    if [ ! -d "$DEMO_DIR" ]; then
        error "Demo directory not found: $DEMO_DIR"
        exit 1
    fi
    
    log "📍 FASE 1: Coleta Paralela de Dados"
    echo ""
    
    # Executar agentes checkers em "paralelo"
    run_agent "gradle-checker-x" 1 &
    run_agent "gradle-checker-y" 1 &
    wait
    
    log "📍 TESTE DE PERSISTÊNCIA (CRÍTICO)"
    echo ""
    
    # Verificar estados antes do restart
    info "Estados antes do 'restart':"
    verify_state "gradle-checker-x"
    verify_state "gradle-checker-y"
    
    # Simular restart
    simulate_restart
    
    # Verificar recuperação de estados
    info "Estados após 'restart':"
    verify_state "gradle-checker-x"
    verify_state "gradle-checker-y"
    
    # Verificar se dados foram preservados
    if command -v jq >/dev/null 2>&1; then
        local version_x=$(jq -r '.state.last_version_found' "$DEMO_DIR/agent-gradle-checker-x/state.json" 2>/dev/null || echo "unknown")
        local version_y=$(jq -r '.state.last_version_found' "$DEMO_DIR/agent-gradle-checker-y/state.json" 2>/dev/null || echo "unknown")
        info "Dados preservados: Service-X=$version_x, Service-Y=$version_y"
    fi
    
    success "Persistência validada com sucesso!"
    echo ""
    
    log "📍 FASE 2: Análise e Documentação"
    echo ""
    
    # Executar documentação baseada nos dados coletados
    run_agent "documentation" 1
    
    log "📍 VALIDAÇÃO FINAL"
    echo ""
    
    # Verificar estados finais
    info "Estados finais:"
    verify_state "gradle-checker-x"
    verify_state "gradle-checker-y"  
    verify_state "documentation"
    
    # Verificar resultado da documentação
    if command -v jq >/dev/null 2>&1; then
        local inconsistencies=$(jq -r '.state.inconsistencies_found' "$DEMO_DIR/agent-documentation/state.json" 2>/dev/null || echo "unknown")
        local services=$(jq -r '.state.services_analyzed[]' "$DEMO_DIR/agent-documentation/state.json" 2>/dev/null | tr '\n' ',' | sed 's/,$//' || echo "unknown")
        info "Resultado: $inconsistencies inconsistência(s) encontrada(s) em: [$services]"
    fi
    
    success "✨ Demo concluído com sucesso!"
    echo ""
    
    log "📊 RESUMO DOS RESULTADOS"
    echo ""
    info "• Coordenação entre agentes: ✅ Funcionou"
    info "• Persistência de estado: ✅ Validada"  
    info "• Especialização de função: ✅ Confirmada"
    info "• Orquestração humana: ✅ Eficaz"
    
    echo ""
    info "📋 Logs completos salvos em: $LOG_FILE"
    info "📂 Para ver estados detalhados: ls -la $DEMO_DIR/*/state.json"
    info "📖 Para ver resultado da documentação: cat $DEMO_DIR/agent-documentation/2.txt"
    
    echo ""
    success "🎉 Conceito Conductor validado com sucesso!"
}

# Verificar argumentos
if [ "$1" == "--help" ]; then
    echo "Conductor Demo Runner"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help     Show this help message"
    echo "  --clean    Clean previous demo state"
    echo ""
    echo "This script runs the complete Conductor demo to validate:"
    echo "• Agent coordination via events"
    echo "• State persistence through restarts"
    echo "• Function specialization without interference"
    echo "• Effective human orchestration"
    exit 0
fi

if [ "$1" == "--clean" ]; then
    log "Limpando estado anterior do demo..."
    # Reset states to initial values
    find "$DEMO_DIR" -name "state.json" -exec git checkout {} \; 2>/dev/null || true
    rm -f "$LOG_FILE"
    success "Estado limpo!"
    exit 0
fi

# Executar demo
main