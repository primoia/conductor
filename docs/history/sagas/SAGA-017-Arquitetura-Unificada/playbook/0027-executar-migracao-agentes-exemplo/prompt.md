# Especificação Técnica e Plano de Execução: 0027-executar-migracao-agentes-exemplo

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal de comandos.

#### **2. OBJETIVO ESTRATÉGico (O "PORQUÊ")**
Esta tarefa valida a generalidade da nossa ferramenta de migração e completa a transição de todos os agentes versionados no projeto para a nova arquitetura. Isso garante que os exemplos e demonstrações do projeto reflitam a arquitetura moderna e unificada.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Consistência de Destino:** A migração **DEVE** usar o mesmo diretório de destino (`.conductor_workspace/agents`) para que todos os agentes migrados coexistam no mesmo local.
- **Verificação Manual:** A conclusão **DEVE** ser validada pela inspeção manual dos novos artefatos gerados.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve executar os seguintes comandos em ordem a partir da raiz do projeto e verificar a saída.

**Comando 1: Executar o script de migração para os agentes de exemplo**
```bash
poetry run python scripts/migrate_legacy_agents.py \
    --source-dir projects/desafio-meli/agents/ \
    --target-dir .conductor_workspace/agents
```

**Comando 2: Verificar a saída do console**
A saída do comando deve mostrar a migração dos agentes específicos do `desafio-meli`, por exemplo:
```
Iniciando migração de agentes de 'projects/desafio-meli/agents/' para '.conductor_workspace/agents'...
Migrando agente de: projects/desafio-meli/agents/ProductAnalyst_Agent...
  -> Sucesso! Artefato salvo em: .conductor_workspace/agents/ProductAnalyst_Agent.json
... (e outros agentes do desafio-meli) ...
Migração concluída.
```

**Comando 3: Listar o conteúdo combinado do diretório de agentes**
```bash
ls -l .conductor_workspace/agents/
```
A saída agora deve mostrar uma lista combinada dos meta-agentes (migrados no estágio anterior) e os agentes do `desafio-meli`.

**Comando 4: Inspecionar um dos novos artefatos**
```bash
cat .conductor_workspace/agents/ProductAnalyst_Agent.json
```
A saída deve ser um JSON bem formatado, confirmando que a migração do agente de exemplo foi bem-sucedida.

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando todos os comandos forem executados com sucesso e a inspeção manual confirmar que os agentes do `desafio-meli` foram migrados e adicionados ao diretório de agentes do workspace.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
