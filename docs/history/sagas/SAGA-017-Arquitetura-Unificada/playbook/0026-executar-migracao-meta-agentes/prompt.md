# Especificação Técnica e Plano de Execução: 0026-executar-migracao-meta-agentes

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal de comandos.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa aplica a ferramenta de migração aos agentes mais críticos do sistema, os meta-agentes. A execução bem-sucedida deste plano prova a eficácia do nosso script de migração e alinha a fundação do nosso ecossistema de agentes com a nova arquitetura unificada.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Destino Limpo:** A migração **DEVE** ser feita para um diretório limpo e bem definido, para não poluir o código-fonte com artefatos gerados. O diretório `.conductor_workspace/agents` é o local canônico para os agentes no backend de filesystem.
- **Verificação Manual:** A conclusão bem-sucedida **DEVE** ser validada pela inspeção manual dos artefatos gerados.
- **Não versionamento:** Os artefatos gerados no `.conductor_workspace` **NÃO DEVEM** ser commitados no Git.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve executar os seguintes comandos em ordem a partir da raiz do projeto e verificar a saída.

**Comando 1: Criar o diretório de destino**
```bash
mkdir -p .conductor_workspace/agents
```

**Comando 2: Executar o script de migração**
```bash
poetry run python scripts/migrate_legacy_agents.py \
    --source-dir projects/_common/agents/ \
    --target-dir .conductor_workspace/agents
```

**Comando 3: Verificar a saída**
A saída do comando anterior deve ser uma lista de agentes sendo migrados, semelhante a:
```
Iniciando migração de agentes de 'projects/_common/agents/' para '.conductor_workspace/agents'...
Migrando agente de: projects/_common/agents/AgentCreator_Agent...
  -> Sucesso! Artefato salvo em: .conductor_workspace/agents/AgentCreator_Agent.json
Migrando agente de: projects/_common/agents/CodeReviewer_Agent...
  -> Sucesso! Artefato salvo em: .conductor_workspace/agents/CodeReviewer_Agent.json
... (e assim por diante para todos os meta-agentes) ...
Migração concluída.
```

**Comando 4: Listar os artefatos gerados**
```bash
ls -l .conductor_workspace/agents/
```
A saída deve mostrar um arquivo `.json` para cada meta-agente que existia no diretório de origem.

**Comando 5: Inspecionar um artefato**
```bash
cat .conductor_workspace/agents/AgentCreator_Agent.json
```
A saída deve ser um JSON formatado contendo as chaves `agent_id`, `agent_home_path`, `definition`, `persona`, etc.

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando todos os comandos forem executados com sucesso e a inspeção manual dos artefatos gerados confirmar que a migração ocorreu como esperado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
