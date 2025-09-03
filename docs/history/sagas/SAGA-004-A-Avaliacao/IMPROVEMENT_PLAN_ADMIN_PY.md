# Plano de Melhoria: admin.py e AgentCreator_Agent

## 1. Resumo

Durante um ciclo de avaliação 360, foram identificados múltiplos bugs e inconsistências de design no script `admin.py` e no comportamento do `AgentCreator_Agent`. Este documento detalha os problemas e propõe um plano de ação para corrigi-los, tornando o processo de criação de agentes mais robusto, previsível e automatizável.

---

## 2. Descobertas e Diagnósticos

### Descoberta 1: Falta de Modo de Execução Não-Interativo

- **Problema:** O `admin.py` originalmente não possuía um parâmetro `--input`, forçando o uso do modo interativo (`--repl`). Isso impedia a automação.
- **Status:** **Parcialmente Corrigido.** Adicionamos o parâmetro, mas a lógica do agente subjacente ainda não lida bem com ele.

### Descoberta 2: Resolução de Caminhos Frágil

- **Problema:** Os scripts usavam caminhos relativos baseados no diretório de trabalho atual (`CWD`), causando erros de `FileNotFoundError` quando executados da raiz do monorepo.
- **Status:** **Corrigido.** A lógica em `agent_common.py` foi refatorada para usar caminhos absolutos baseados na localização do próprio arquivo (`__file__`), tornando os scripts resilientes à localização da execução.

### Descoberta 3: Perda de Estado em Modo Não-Interativo

- **Problema:** O `AgentCreator_Agent` não consegue manter o contexto da conversa entre múltiplas chamadas não-interativas. Ele lê o `state.json`, mas sua lógica interna o ignora, reiniciando a conversa e pedindo informações já fornecidas.
- **Causa Provável:** O contexto de execução (CWD) passado para o provedor de IA subjacente (Claude) pode estar incorreto, impedindo-o de acessar o `state.json` do meta-agente.
- **Status:** **Problema Crítico Identificado.**

### Descoberta 4: Ambiguidade na Criação de Agentes (Meta vs. Projeto)

- **Problema:** O `AgentCreator_Agent` não distingue claramente a intenção de criar um meta-agente (em `_common`) de um agente de projeto. Ele se confunde com as pistas da conversa e acaba criando um agente de projeto no lugar errado.
- **Status:** **Problema Crítico de Lógica Identificado.**

### Descoberta 5: Geração de `state.json` "Alucinado"

- **Problema:** Ao criar um novo agente, o `AgentCreator_Agent` não gera um `state.json` limpo. Em vez disso, ele preenche o arquivo com um template de dados, incluindo dependências e configurações padrão que não foram solicitadas.
- **Status:** **Problema Crítico de Lógica Identificado.**

---

## 3. Plano de Ação e Melhorias Propostas

### Ação 1: Refatoração do Processo de Criação de Agentes (Solução Principal)

- **Objetivo:** Eliminar a ambiguidade e a complexidade da criação de agentes.
- **Proposta:** Modificar o `AgentCreator_Agent` e o `admin.py` para adotar uma abordagem mais simples e direta, conforme sugerido pelo usuário.
  1.  **Remover a lógica de descoberta de caminho:** O agente não deve mais perguntar por `ambiente` e `projeto` para tentar adivinhar o caminho.
  2.  **Adicionar parâmetro de caminho final:** O `admin.py` deve ser modificado para aceitar um novo argumento obrigatório: `--destination-path <CAMINHO_ABSOLUTO_DO_AGENTE>`.
  3.  **Instrução Direta:** A única responsabilidade do `AgentCreator_Agent` será criar a estrutura de arquivos do agente (`agent.yaml`, `persona.md`, `state.json` zerado) no caminho exato fornecido por `--destination-path`.
- **Benefício:** Esta abordagem remove toda a ambiguidade, resolve o problema de contexto (Descoberta 3 e 4) e simplifica drasticamente o processo.

### Ação 2: Correção da Criação do `state.json`

- **Objetivo:** Garantir que novos agentes comecem com um estado limpo e bem definido.
- **Proposta:** Modificar o `AgentCreator_Agent` para que, ao criar um novo agente, o arquivo `state.json` seja gerado usando **exatamente** o seguinte conteúdo como template, que representa um estado inicial válido e sem dados pré-existentes:

```json
{
  "agent_id": "{{agent_id}}",
  "version": "2.0",
  "created_at": "{{timestamp}}",
  "last_updated": "{{timestamp}}",
  "execution_stats": {
    "total_executions": 0,
    "last_execution": null
  },
  "conversation_history": []
}
```
O agente deverá substituir as variáveis `{{agent_id}}` e `{{timestamp}}` com os valores corretos no momento da criação.

### Ação 3: Limpeza do Código

- **Objetivo:** Finalizar a refatoração da dependência circular.
- **Proposta:** Remover as classes `LLMClient`, `ClaudeCLIClient`, e `GeminiCLIClient` do arquivo `genesis_agent_v2.py`, uma vez que elas agora residem e são importadas corretamente do `agent_common.py`.

---

## 4. Próximos Passos

O próximo passo é executar este plano de melhoria, começando pela **Ação 1**. Isso envolverá modificar os scripts `admin.py` e a persona do `AgentCreator_Agent` para implementar o novo fluxo de criação baseado em um caminho de destino explícito.

---

## 5. Estratégia de Validação e Testes

Após a implementação das melhorias, a validação deve seguir um roteiro de teste explícito para garantir que os problemas foram resolvidos.

### Comando de Exemplo (Pós-Refatoração)

O comando a ser testado deve se parecer com o seguinte, utilizando o novo parâmetro `--destination-path`:

```bash
python3 projects/conductor/scripts/admin.py \
  --agent AgentCreator_Agent \
  --destination-path "/mnt/ramdisk/primoia-main/primoia-monorepo/projects/conductor/projects/_common/agents/TestAgent_01" \
  --input "Crie um agente de teste simples que lista arquivos." \
  --ai-provider claude
```

### Critérios de Sucesso (Caso de Teste)

O executor do teste (Claude ou Gemini) deve validar programaticamente os seguintes pontos:

1.  **Código de Saída:** O script `admin.py` deve terminar com código de saída `0`.
2.  **Criação de Diretório:** O diretório especificado em `--destination-path` deve existir.
    - `test -d /mnt/ramdisk/primoia-main/primoia-monorepo/projects/conductor/projects/_common/agents/TestAgent_01`
3.  **Criação de Arquivos:** O diretório do agente deve conter os três arquivos essenciais:
    - `test -f .../TestAgent_01/agent.yaml`
    - `test -f .../TestAgent_01/persona.md`
    - `test -f .../TestAgent_01/state.json`
4.  **Estado Inicial Limpo:** O arquivo `state.json` deve estar essencialmente vazio, contendo apenas metadados iniciais, sem histórico de conversas ou dados "alucinados".
    - `grep -q '"conversation_history": []' .../TestAgent_01/state.json`

O executor deve reportar o sucesso ou a falha de cada um desses pontos de verificação.

