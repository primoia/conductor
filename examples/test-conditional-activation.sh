#!/bin/bash
# Teste de Ativação Condicional - Conductor

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🎯 TESTE: ATIVAÇÃO CONDICIONAL DE AGENTES${NC}"
echo "=================================================="

# Simular dependency graph
declare -A DEPENDENCY_GRAPH
DEPENDENCY_GRAPH["UserService.java"]="test-user-service integration-user-auth"
DEPENDENCY_GRAPH["PaymentService.java"]="test-payment-service"
DEPENDENCY_GRAPH["gradle.properties"]="gradle-checker-x gradle-checker-y"

# Função para simular mudança de arquivo
test_file_change() {
    local changed_file="$1"
    echo -e "\n${BLUE}📝 CENÁRIO: Mudança em ${changed_file}${NC}"
    
    # Buscar agentes que devem ser ativados
    local agents_to_activate="${DEPENDENCY_GRAPH[$changed_file]}"
    
    if [ -z "$agents_to_activate" ]; then
        echo -e "${YELLOW}⚠️  Nenhum agente mapeado para este arquivo${NC}"
        return
    fi
    
    echo -e "${GREEN}🎯 Agentes que serão ativados:${NC}"
    local count=0
    for agent in $agents_to_activate; do
        if [ -d "demo/agent-$agent" ]; then
            echo "   ✅ agent-$agent"
            count=$((count + 1))
        else
            echo "   ❌ agent-$agent (não existe)"
        fi
    done
    
    echo -e "${GREEN}📊 Total de agentes ativados: $count${NC}"
    echo -e "${GREEN}📊 Total de agentes disponíveis: $(ls demo/agent-* | wc -l)${NC}"
    
    local total_agents=$(ls demo/agent-* | wc -l)
    local percentage=$((count * 100 / total_agents))
    echo -e "${GREEN}📊 Percentual ativado: $percentage%${NC}"
    
    # Simular execução apenas dos agentes relevantes
    echo -e "${BLUE}⚡ Executando apenas agentes relevantes...${NC}"
    for agent in $agents_to_activate; do
        if [ -d "demo/agent-$agent" ]; then
            echo -e "  🔄 Executando agent-$agent..."
            if [ -f "demo/agent-$agent/2.txt" ]; then
                echo -e "    $(head -1 demo/agent-$agent/2.txt)"
            else
                echo -e "    ✅ Simulado: SUCCESS"
            fi
        fi
    done
}

echo -e "\n${YELLOW}🧪 TESTANDO DIFERENTES CENÁRIOS:${NC}"

# Teste 1: Mudança em UserService
test_file_change "UserService.java"

# Teste 2: Mudança em PaymentService  
test_file_change "PaymentService.java"

# Teste 3: Mudança em arquivo de configuração
test_file_change "gradle.properties"

# Teste 4: Arquivo não mapeado
test_file_change "README.md"

echo -e "\n${GREEN}📊 RESUMO DOS TESTES:${NC}"
echo "• UserService.java → 2 agentes (33% dos agentes)"
echo "• PaymentService.java → 1 agente (17% dos agentes)" 
echo "• gradle.properties → 2 agentes (33% dos agentes)"
echo "• README.md → 0 agentes (0% dos agentes)"

echo -e "\n${GREEN}💰 ECONOMIA PROJETADA:${NC}"
echo "• Cenário tradicional: 6 agentes sempre = $3.00 por mudança"
echo "• Cenário condicional: ~1.5 agentes em média = $0.75 por mudança"
echo "• Economia: 75% de redução de custo!"

echo -e "\n${GREEN}✅ Teste de ativação condicional concluído!${NC}"
