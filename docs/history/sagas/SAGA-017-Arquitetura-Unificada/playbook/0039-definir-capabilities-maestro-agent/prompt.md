# Especificação Técnica e Plano de Execução: 0039-A-definir-capabilities-maestro

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa é fundamental para a arquitetura Maestro-Executor da SAGA-017. Seu propósito é definir formalmente as capabilities do Maestro Agent como um agente de coordenação e planejamento de alto nível. O Maestro Agent atua como um "gerente de projeto" que quebra tarefas complexas em subtarefas executáveis e coordena sua execução através do Executor Agent. Esta definição estabelece as ferramentas e capacidades que permitirão ao Maestro cumprir seu papel na hierarquia de três camadas (Orquestrador -> Maestro -> Executor).

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Foco em Coordenação:** As capabilities **DEVEM** focar em manipulação de arquivos, gerenciamento de estado e coordenação de tarefas, conforme especificado no SAGA-017-EXECUTION-PLAN.md.
- **Arquitetura de Três Camadas:** As capabilities **DEVEM** ser projetadas para permitir que o Maestro coordene com o Executor Agent, não executar tarefas diretamente.
- **Padrão de Artefatos:** As capabilities **DEVEM** ser definidas no arquivo `definition.yaml` do Maestro Agent, seguindo o padrão estabelecido na SAGA-016.
- **Documentação Clara:** Cada capability **DEVE** incluir descrição clara de seu propósito e uso.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve localizar o arquivo `definition.yaml` do Maestro Agent (criado em estágio anterior) e definir a seção `capabilities` com as seguintes capabilities específicas:

**Capabilities Obrigatórias:**
1. **File Management:** Manipulação de arquivos e diretórios
2. **State Management:** Gerenciamento de estado de tarefas e projetos
3. **Task Coordination:** Coordenação e divisão de tarefas complexas
4. **Communication:** Comunicação com Executor Agent
5. **Planning:** Planejamento e estruturação de workflows

**Estrutura Esperada no `definition.yaml`:**
```yaml
name: "Maestro_Agent"
version: "1.0.0"
schema_version: "1.0"
description: "Agente orquestrador de alto nível que coordena tarefas complexas"
author: "SAGA-017"
tags: ["maestro", "coordination", "planning"]
capabilities: [
  "file_management",
  "state_management", 
  "task_coordination",
  "communication",
  "planning"
]
allowed_tools: [
  "read_file", "write_file", "list_directory", "create_directory",
  "get_state", "update_state", "save_state", "load_state",
  "decompose_task", "assign_task", "monitor_progress", "aggregate_results",
  "send_task", "receive_result", "query_status", "cancel_task",
  "create_plan", "validate_plan", "execute_plan", "adjust_plan"
]
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho será considerado concluído **somente quando**:
- O arquivo `definition.yaml` do Maestro Agent contiver as capabilities e allowed_tools com todas as 5 capabilities obrigatórias
- Cada capability tiver descrição clara e tools específicos definidos
- As capabilities estiverem alinhadas com o papel de coordenação do Maestro Agent
- A estrutura seguir o padrão YAML especificado

#### **6. SINAL DE CONCLUSÃO**
Uma vez que você tenha cumprido todos os critérios, responda com a única frase: `TASK_COMPLETE`
