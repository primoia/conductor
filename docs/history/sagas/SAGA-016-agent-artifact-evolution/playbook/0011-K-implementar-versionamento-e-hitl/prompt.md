# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0011-K

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo é introduzir duas **Travas de Segurança e Qualidade** no sistema. O **Versionamento de Esquema** protege o sistema contra instabilidade, agindo como uma "verificação de compatibilidade" que impede o carregamento de agentes construídos com uma estrutura antiga e quebrada. O **Human-in-the-Loop (HITL)** implementa uma "pausa para aprovação", garantindo que nenhuma ação crítica seja executada sem a supervisão e o consentimento explícito de um operador humano, servindo como a principal barreira de segurança da V1.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITO NÃO FUNCIONAL)**
- **Falha Rápida:** A verificação de versão do esquema **DEVE** ocorrer durante o carregamento do agente (`AgentService`). Se a verificação falhar, o sistema **DEVE** levantar uma exceção `CompatibilityError` imediatamente, evitando que um agente incompatível seja carregado na memória.
- **Ponto de Verificação Central:** A confirmação HITL **DEVE** ser implementada como uma função utilitária reutilizável (`confirm_action`) e chamada pelo `Orchestrator` como o último passo antes de delegar a execução a um agente.
- **Localização de Utilitários:** A função `confirm_action` **DEVE** residir em um módulo compartilhado, como `src/cli/shared/utils.py`, para ser acessível a diferentes partes da aplicação de linha de comando.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**

**1. Definir a Versão do Esquema e a Lógica de Verificação:**
```python
# Em um local central de configuração, como src/config.py
CURRENT_SUPPORTED_SCHEMA_VERSION = "1.0"

# Em src/core/agent_service.py
from src.config import CURRENT_SUPPORTED_SCHEMA_VERSION

class CompatibilityError(Exception):
    pass

# Dentro da classe AgentService, no método load_agent_instance ou similar
# ...
    def _validate_schema_version(self, definition: AgentDefinition):
        if definition.schema_version != CURRENT_SUPPORTED_SCHEMA_VERSION:
            raise CompatibilityError(
                f"Agente '{definition.name}' usa a versão de esquema '{definition.schema_version}', "
                f"mas o Conductor atualmente suporta a versão '{CURRENT_SUPPORTED_SCHEMA_VERSION}'."
            )
# ...
# Este método deve ser chamado após carregar a AgentDefinition.
```

**2. Criar a Função de Confirmação HITL:**
```python
# Em src/cli/shared/utils.py

def confirm_action(prompt_message: str) -> bool:
    """
    Exibe um prompt de confirmação [y/N] para o usuário e retorna sua decisão.
    """
    full_prompt = f"{prompt_message} [y/N]: "
    while True:
        try:
            response = input(full_prompt).lower().strip()
            if response == 'y':
                return True
            elif response == 'n':
                return False
            else:
                print("Resposta inválida. Por favor, digite 'y' ou 'n'.")
        except (EOFError, KeyboardInterrupt):
            # Trata Ctrl+D ou Ctrl+C como um "Não"
            print("\nConfirmação cancelada.")
            return False
```

**3. Integrar HITL no Orquestrador:**
```python
# Em src/core/orchestrator.py
from src.cli.shared.utils import confirm_action

# ... na classe Orchestrator
    def execute_task(self, task_description: str):
        agent_def = self.find_best_agent_for_task(task_description)
        
        prompt = f"Delegar a tarefa '{task_description}' ao agente '{agent_def.name}'?"
        if confirm_action(prompt):
            # ... Lógica para invocar o agente executor ...
            print("Execução aprovada. Delegando...")
        else:
            print("Execução abortada pelo usuário.")
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
- A lógica de validação de `schema_version` foi adicionada ao `AgentService`.
- A função `confirm_action` foi implementada corretamente.
- O `Orchestrator` foi modificado para usar `confirm_action` antes de delegar a execução de uma tarefa.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
