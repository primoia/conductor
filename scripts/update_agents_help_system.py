#!/usr/bin/env python3
"""
Script para adicionar sistema de help padronizado a todos os agentes.
Executa atualizações em massa de forma segura.
"""

import os
import re
from pathlib import Path

AGENTS_DIR = "/mnt/ramdisk/primoia-main/conductor/projects/develop/agents"

# Template base do sistema de help
HELP_SYSTEM_TEMPLATE = '''
## Available Commands

### Help Command
**Commands accepted:**
- `help`
- `ajuda`
- `comandos`
- `?`

**Action:**
Display this list of available commands:

```
🤖 **COMANDOS DISPONÍVEIS:**

📋 **VISUALIZAR (sem salvar):**
• preview
• preview documento
• mostrar documento

💾 **GERAR/SALVAR (com versionamento):**
• gerar documento
• criar artefato
• salvar documento
• executar tarefa
• consolidar

❓ **AJUDA:**
• help / ajuda / comandos / ?

📊 **COMO USAR:**
1. Discuta {context_type} comigo
2. Use "preview" para ver como ficaria {output_type}
3. Use "gerar documento" para salvar (v1.0, v1.1, v1.2...)
4. Continue conversando para refinamentos incrementais

📁 **SAÍDA CONFIGURADA:**
• Arquivo: {output_artifact}
• Diretório: {output_directory}
```

### Preview Command
**Commands accepted:**
- `preview`
- `preview documento`  
- `mostrar documento`

**Action:**
1. Use **Read** to load `state.json`
2. Generate complete content based on conversation history
3. **DO NOT save file** - only display content in chat
4. Start response with: "📋 **PREVIEW do documento de saída:**"

### Generation/Merge Command (Incremental)
**Commands accepted:**
- `gerar documento`
- `criar artefato`
- `salvar documento`
- `executar tarefa`
- `consolidar`

**Action:**
1. Use **Read** to load `state.json`
2. **Determine output configuration**: File name and directory according to agent configuration
3. **Check if document exists**: Use **Read** on complete path

**If document does NOT exist:**
- Create new document based on complete history
- Version: v1.0

**If document ALREADY exists:**
- **INCREMENTAL MERGE**: Combine existing document + new conversations
- **Versioning**: Increment version (v1.0 → v1.1, v1.1 → v1.2, etc.)
- **Preserve previous context** + add new analysis
- **Mark updated sections** with timestamp

4. **CREATE folder structure if needed**: according to agent configuration
5. Use **Write** to save updated document in configured path

**SPECIFIC AUTHORIZATION**: You have TOTAL permission to:
- Create folders according to agent configuration
- Read existing documents for merging
- Write configured output files
- Execute without asking permission!
'''

# Configurações específicas por agente
AGENT_CONFIGS = {
    "KotlinRepositoryCreator_Agent": {
        "context_type": "os requisitos do repository",
        "output_type": "o código Kotlin do repository",
        "output_artifact": "Repository.kt",
        "output_directory": "src/main/kotlin/com/project/repository"
    },
    "KotlinServiceCreator_Agent": {
        "context_type": "os requisitos do service",
        "output_type": "o código Kotlin do service",
        "output_artifact": "Service.kt", 
        "output_directory": "src/main/kotlin/com/project/service"
    },
    "KotlinTestCreator_Agent": {
        "context_type": "os cenários de teste",
        "output_type": "o código Kotlin dos testes",
        "output_artifact": "IntegrationTest.kt",
        "output_directory": "src/test/kotlin/com/project"
    },
    "PlanCreator_Agent": {
        "context_type": "o problema a ser planejado",
        "output_type": "o plano de implementação",
        "output_artifact": "implementation_plan.yaml",
        "output_directory": "workspace/plans"
    },
    "OnboardingGuide_Agent": {
        "context_type": "o perfil e contexto do usuário",
        "output_type": "o relatório de onboarding",
        "output_artifact": "onboarding_report.md",
        "output_directory": "workspace/reports"
    },
    "AgentCreator_Agent": {
        "context_type": "a especificação do agente",
        "output_type": "o relatório de criação",
        "output_artifact": "agent_creation_report.md",
        "output_directory": "workspace/reports"
    },
    "PythonDocumenter_Agent": {
        "context_type": "o código Python a documentar",
        "output_type": "a documentação gerada",
        "output_artifact": "python_documentation.md",
        "output_directory": "docs/generated"
    }
}

def update_agent_persona(agent_name, agent_path):
    """Atualiza a persona de um agente com o sistema de help."""
    persona_file = os.path.join(agent_path, "persona.md")
    
    if not os.path.exists(persona_file):
        print(f"❌ Persona não encontrada: {persona_file}")
        return False
    
    # Verificar se já tem sistema de help
    with open(persona_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "Available Commands" in content or "## Available Commands" in content:
        print(f"✅ {agent_name} já tem sistema de help")
        return True
    
    # Obter configuração específica do agente
    config = AGENT_CONFIGS.get(agent_name, {
        "context_type": "os requisitos",
        "output_type": "o documento",
        "output_artifact": "output.md",
        "output_directory": "workspace/output"
    })
    
    # Gerar help system personalizado
    help_content = HELP_SYSTEM_TEMPLATE.format(**config)
    
    # Adicionar ao final do arquivo
    updated_content = content.rstrip() + help_content
    
    # Fazer backup
    backup_file = persona_file + ".backup"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Escrever conteúdo atualizado
    with open(persona_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✅ {agent_name} atualizado com sistema de help")
    return True

def main():
    """Atualiza todos os agentes com sistema de help."""
    print("🚀 Iniciando atualização do sistema de help para todos os agentes...")
    
    agents_updated = 0
    agents_skipped = 0
    
    for agent_dir in os.listdir(AGENTS_DIR):
        agent_path = os.path.join(AGENTS_DIR, agent_dir)
        
        if not os.path.isdir(agent_path):
            continue
        
        if agent_dir == "ProblemRefiner_Agent":
            print(f"⏭️  {agent_dir} pulado (já atualizado)")
            agents_skipped += 1
            continue
        
        print(f"\n📝 Processando {agent_dir}...")
        
        if update_agent_persona(agent_dir, agent_path):
            agents_updated += 1
        else:
            print(f"❌ Falha ao atualizar {agent_dir}")
    
    print(f"\n🎉 Atualização concluída!")
    print(f"✅ Agentes atualizados: {agents_updated}")
    print(f"⏭️  Agentes pulados: {agents_skipped}")
    print(f"🔧 Total processado: {agents_updated + agents_skipped}")

if __name__ == "__main__":
    main()