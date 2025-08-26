# Plano de Refatoração: AgentCreator_Agent para Modelo Baseado em Templates

**Saga:** SAGA-007-Validacao-Admin-Executor
**Status:** Proposto

## 1. Análise do Problema

O `AgentCreator_Agent` foi projetado para gerar novos agentes a partir de um prompt de alto nível. Um teste A/B (criando dois agentes com o mesmo prompt) revelou que o processo é **altamente não-determinístico**. 

Os agentes gerados diferiram não apenas em palavras, mas em estrutura, idioma e funcionalidades (`available_tools`). Esta inconsistência impede a padronização, a confiabilidade e a escalabilidade da criação de agentes, que é uma função central do framework.

A causa raiz é o uso de uma IA generativa para "criar" a configuração e a persona do zero a cada vez, em vez de preencher um padrão definido.

## 2. Solução Proposta: Modelo Baseado em Templates

A solução é refatorar o `AgentCreator_Agent` para que ele deixe de ser um "criador" e se torne um "preenchedor de templates" (template filler). O processo será determinístico e padronizado.

### 2.1. Criação dos Arquivos de Template

Dois arquivos de template serão criados no diretório do `AgentCreator_Agent`:

1.  **`agent.yaml.template`**: Uma cópia do `agent.yaml` padrão, com placeholders para valores variáveis.
    ```yaml
    id: {{AGENT_ID}}
    version: '1.0'
    description: {{AGENT_DESCRIPTION}}
    ai_provider: {{AI_PROVIDER}}
    # ... etc
    ```

2.  **`persona.md.template`**: Um template para a persona com placeholders.
    ```markdown
    # Persona: {{AGENT_ID}}

    ## Role
    {{AGENT_ROLE_DESCRIPTION}}
    # ... etc
    ```

### 2.2. Lógica de Refatoração

A lógica interna do `AgentCreator_Agent` será modificada para:

1.  Receber os parâmetros do usuário (ID do agente, descrição, etc.) via `--input` ou modo interativo.
2.  Ler os arquivos `.template`.
3.  Executar uma operação de busca e substituição para preencher os placeholders com os valores fornecidos.
4.  Salvar os arquivos resultantes (`agent.yaml`, `persona.md`) no diretório de destino.

## 3. Plano de Testes para a Refatoração

Para garantir que a refatoração seja bem-sucedida e não introduza regressões, o seguinte plano de testes será implementado.

### 3.1. Teste de Regressão (Teste A/B Automatizado)

-   **Objetivo:** Garantir que a nova versão seja determinística.
-   **Método:** Criar um script de teste que:
    1.  Chama o `AgentCreator_Agent` refatorado para criar um Agente A.
    2.  Chama o `AgentCreator_Agent` refatorado com os mesmos parâmetros para criar um Agente B.
    3.  Usa o comando `diff` para comparar `agent.yaml` e `persona.md` dos dois agentes.
    4.  O teste passa se o `diff` não encontrar diferenças.

### 3.2. Teste de Funcionalidade

-   **Objetivo:** Garantir que o agente criado seja funcional.
-   **Método:** Após a criação de um agente de teste, executar um comando simples com ele (ex: pedir para listar um diretório) para garantir que ele carrega e opera corretamente.

## 4. Passos de Implementação (Alto Nível)

1.  Criar os arquivos `agent.yaml.template` e `persona.md.template`.
2.  Modificar o código-fonte do `AgentCreator_Agent` para implementar a lógica de preenchimento de template.
3.  Criar o script de teste de regressão automatizado (A/B).
4.  Executar todos os testes para validar a nova implementação.
