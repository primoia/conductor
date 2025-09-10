# Especificação Técnica e Plano de Execução: 0030-remover-agent-logic

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa elimina débito técnico e remove código morto da base de código. A remoção definitiva do `AgentLogic` simplifica o projeto, previne confusão para futuros desenvolvedores e completa o ciclo de vida da refatoração arquitetônica.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Validação Completa:** A remoção só pode ser considerada bem-sucedida após a execução completa e sem falhas de toda a suíte de testes.
- **Remoção Limpa:** Nenhuma referência órfã ao `AgentLogic` deve permanecer no código-fonte.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve executar os seguintes comandos em ordem.

**Comando 1: Remover o arquivo**
```bash
rm src/core/agent_logic.py
```

**Comando 2: Buscar por referências órfãs**
```bash
grep -r "AgentLogic" .
```
A saída deste comando deve estar vazia ou conter apenas referências em arquivos de log, documentos de saga, ou nos playbooks (que são aceitáveis). Não deve haver nenhuma referência em código Python (`.py`).

**Comando 3: Executar a suíte de testes completa**
```bash
poetry run pytest
```
A saída deste comando deve indicar que todos os testes passaram com sucesso.

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `src/core/agent_logic.py` for removido e a suíte de testes completa for executada com sucesso.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
