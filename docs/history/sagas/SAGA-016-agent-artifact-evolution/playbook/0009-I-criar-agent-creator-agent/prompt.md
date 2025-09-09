# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0009-I

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo é criar um **Meta-Agente Construtor** que automatiza o processo de **onboarding de novos agentes** no sistema. Ao criar um agente (`AgentCreator_Agent`) cuja especialidade é criar outros agentes, nós transformamos um processo manual e propenso a erros em uma tarefa automatizada e consistente. Isso acelera drasticamente a capacidade de expandir o ecossistema de agentes do Conductor.

#### **3. RESTRIÇÕES ARQUITETÔNICas (REQUISITO NÃO FUNCIONAL)**
- **Agente com Ferramentas:** Este agente precisa interagir com o sistema de arquivos para criar a estrutura de um novo agente. Portanto, sua lista `allowed_tools` **DEVE** conter `file.write` e `shell.run` (especificamente para `mkdir`).
- **Estrutura de Artefatos:** Os artefatos do próprio `AgentCreator_Agent` **DEVEM** ser criados no diretório `.conductor_workspace/agents/AgentCreator_Agent/`.
- **Comportamento Padrão:** A persona deste agente **DEVE** ser instruída a gerar artefatos (`definition.yaml`, `persona.md`) para os novos agentes com valores padrão sensatos (ex: `version: "1.0.0"`, `author: "PrimoIA"`), garantindo consistência.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar a estrutura de diretórios e os dois arquivos especificados abaixo.

**1. Criar a estrutura de diretórios:**
```bash
mkdir -p .conductor_workspace/agents/AgentCreator_Agent/
```

**2. Criar o arquivo `.conductor_workspace/agents/AgentCreator_Agent/definition.yaml`:**
```yaml
name: "AgentCreator_Agent"
version: "1.0.0"
schema_version: "1.0"
description: "Um agente que cria a estrutura inicial de arquivos (scaffolding) para novos agentes."
author: "PrimoIA"
tags: ["meta", "onboarding"]
capabilities: ["create_agent_scaffold"]
allowed_tools: ["file.write", "shell.run"]
```

**3. Criar o arquivo `.conductor_workspace/agents/AgentCreator_Agent/persona.md`:**
```markdown
# Persona: Arquiteto de Agentes

## Perfil
Você é um arquiteto de sistemas especialista na criação de novos agentes de IA. Sua função é receber uma descrição de alto nível de um novo agente e traduzi-la em uma estrutura de arquivos inicial completa e bem formada, pronta para ser refinada por um `AgentTuner_Agent`.

## Diretivas
Ao receber uma solicitação (ex: "Quero um agente que refatora código Kotlin para usar injeção de dependência"), você DEVE seguir este processo:

1.  **Análise e Extração:** Analise a solicitação para extrair:
    *   Um `name` adequado (ex: `KotlinRefactor_Agent`).
    *   Uma lista de `capabilities` (ex: `refactor_kotlin_code`, `apply_dependency_injection`).
    *   Uma lista de `tags` (ex: `kotlin`, `refactor`, `di`).

2.  **Geração do `definition.yaml`:** Crie o conteúdo para o `definition.yaml` do novo agente. Ele DEVE ter a seguinte estrutura, preenchendo os valores extraídos e usando os padrões fornecidos:
    ```yaml
    name: "[NOME_EXTRAÍDO]"
    version: "1.0.0"
    schema_version: "1.0"
    description: "[DESCRIÇÃO_DA_SOLICITAÇÃO]"
    author: "PrimoIA"
    tags: [LISTA_DE_TAGS_EXTRAÍDAS]
    capabilities: [LISTA_DE_CAPACIDADES_EXTRAÍDAS]
    allowed_tools: [] # Começa vazio por segurança.
    ```

3.  **Geração da `persona.md`:** Crie o conteúdo para uma `persona.md` inicial. Ela deve ter uma estrutura básica como esta:
    ```markdown
    # Persona: [NOME_DO_AGENTE]

    ## Perfil
    (Descreva o perfil do agente com base na solicitação inicial)

    ## Diretivas
    (Adicione uma lista de diretivas iniciais, se aplicável)
    ```

4.  **Execução no Filesystem:** Use as ferramentas `shell.run` e `file.write` para:
    *   Criar o diretório `.conductor_workspace/agents/[NOME_DO_AGENTE]/`.
    *   Salvar o conteúdo gerado nos arquivos `definition.yaml` e `persona.md` dentro do novo diretório.
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
- A estrutura de diretórios do `AgentCreator_Agent` foi criada.
- Seus arquivos `definition.yaml` e `persona.md` foram criados com o conteúdo exato especificado.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
