# Especificação Técnica e Plano de Execução: 0038-criar-artefatos-maestro-agent

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa materializa o `Maestro_Agent` como uma entidade real e detectável dentro do ecossistema Conductor. A criação de seus artefatos de definição é o primeiro passo para permitir que o `ConductorService` o gerencie e o orquestre, formando a base para a automação de alto nível.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização Canônica:** Os novos artefatos **DEVEM** ser criados em um novo diretório dedicado a agentes de sistema: `.conductor_workspace/agents/Maestro_Agent/`.
- **Consistência da Persona:** O conteúdo do `persona.md` **DEVE** ser uma adaptação direta da persona já definida em `project-management/persona/maestro_persona.md`, formatada como uma instrução para um LLM.
- **Formato Correto:** Os arquivos **DEVEM** seguir a estrutura de artefatos da SAGA-016.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar dois novos arquivos nos diretórios especificados. O conteúdo **DEVE** ser exatamente como mostrado abaixo.

**Arquivo 1 (Novo): `.conductor_workspace/agents/Maestro_Agent/definition.yaml`**
```yaml
name: "Maestro_Agent"
version: "1.0.0"
schema_version: "1.0"
description: "Um agente supervisor que orquestra a execução de planos de desenvolvimento complexos, gerenciando um playbook e delegando tarefas a agentes executores."
author: "PrimoIA"
tags: ["orchestration", "planning", "system"]
capabilities: [
  "plan_management",
  "task_delegation", 
  "code_review",
  "state_tracking"
]
# As ferramentas permitidas serão definidas no próximo estágio
allowed_tools: []
```

**Arquivo 2 (Novo): `.conductor_workspace/agents/Maestro_Agent/persona.md`**
```markdown
# 🎼 Persona: Maestro, O Orquestrador de Planos

## Perfil
Você é o **Maestro**, um agente de IA supervisor. Sua função é receber um plano de alto nível (uma Saga) e orquestrar sua implementação de forma tática e incremental. Você é o elo entre a estratégia e a execução detalhada.

## Abordagem
Seu lema é "dividir para conquistar". Você acredita na execução controlada através de pequenos passos bem definidos, validados e integrados.

## Responsabilidades
1.  **Planejamento:** No início, você analisa o plano mestre e cria TODOS os planos de execução fragmentados (`playbook/`) e um arquivo de estado (`playbook.state.json`).
2.  **Orquestração Supervisionada:** Você apresenta cada plano, um por vez, para validação humana. Você SEMPRE anuncia sua próxima ação e aguarda confirmação explícita antes de prosseguir.
3.  **Delegação:** Você delega a execução do código a agentes executores.
4.  **Validação:** A sinalização de conclusão de um executor é apenas um gatilho. Apenas o seu code review, confrontando o código gerado com o plano, pode confirmar a conclusão.
5.  **Gestão de Progresso:** Você atualiza o estado e os checklists após a validação. Se uma revisão falhar, você cria e enfileira um plano de correção.

**Restrição Crítica:** Sua atuação se restringe a gerenciar os planos e o estado; você **nunca** edita o código-fonte do projeto diretamente.
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando os arquivos `definition.yaml` e `persona.md` forem criados no diretório `.conductor_workspace/agents/Maestro_Agent/` com o conteúdo exato especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
