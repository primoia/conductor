**Para:** Agente Implementador (Claude)
**De:** Arquiteto de Software (Gemini)
**Assunto:** Adendo ao Plano da SAGA-009 - Testes de Ciclo de Vida e Tratamento de Exceções

## 1. Pré-requisito

Este plano de revisão **deve ser executado após a conclusão bem-sucedida** do plano principal `REFACTOR_PLAN.md`. Ele assume que a nova estrutura de diretórios `src/` e a configuração com `Poetry` já estão em vigor.

## 2. Objetivo

Elevar a robustez e a confiabilidade do framework `conductor` implementando duas práticas essenciais observadas no projeto de referência:

1.  **Tratamento de Exceções Global:** Centralizar o tratamento de erros para fornecer feedback claro ao usuário e evitar que exceções do core vazem para a interface.
2.  **Testes de Ciclo de Vida (E2E):** Criar um teste End-to-End que valide o fluxo completo de criação, uso e persistência de um agente.

## 3. Plano de Execução Detalhado

### Fase 1: Implementação do Tratamento de Exceções Global

O objetivo é criar exceções customizadas no domínio e handlers na camada de apresentação (CLI), assim como o `desafio-meli` faz para a camada de API.

**Passo 1.1: Definir Exceções Customizadas do Domínio**
*   **Ação:** Crie um novo arquivo `src/core/exceptions.py`.
*   **Conteúdo:** Adicione classes de exceção customizadas para erros de negócio previsíveis.
    ```python
    # src/core/exceptions.py

    class ConductorException(Exception):
        """Base exception for the application."""
        pass

    class AgentNotFoundError(ConductorException):
        """Raised when a specified agent is not found."""
        def __init__(self, agent_id: str):
            self.agent_id = agent_id
            super().__init__(f"Agent '{agent_id}' not found.")

    class LLMClientError(ConductorException):
        """Raised for errors related to the LLM client."""
        pass

    class StatePersistenceError(ConductorException):
        """Raised for errors related to state persistence."""
        pass
    ```

**Passo 1.2: Integrar Exceções no Core**
*   **Ação:** Refatore a lógica em `src/core/agent_logic.py` e nos `adapters` de infraestrutura para lançar essas exceções específicas em vez de exceções genéricas.
*   **Exemplo em `agent_logic.py`:**
    *   No método `embody_agent_v2`, se o agente não for encontrado, em vez de `FileNotFoundError`, lance `AgentNotFoundError(agent_id)`.
*   **Exemplo em `src/infrastructure/llm/cli_client.py`:**
    *   Se o subprocesso do Claude/Gemini falhar, em vez de retornar uma string de erro, lance `LLMClientError(f"...error details...")`.

**Passo 1.3: Implementar o Handler na Camada de CLI**
*   **Ação:** Modifique os arquivos `src/cli/admin.py` e `src/cli/agent.py`.
*   **Lógica:** Envolva a chamada principal da lógica do agente em um bloco `try...except` que captura as `ConductorException` e imprime mensagens amigáveis para o usuário, sem expor o stack trace.
*   **Exemplo em `src/cli/admin.py`:**
    ```python
    # No final da função main()
    try:
        # ... lógica existente para instanciar e chamar o agent_logic
        agent_logic.run()
    except AgentNotFoundError as e:
        print(f"❌ ERRO: {e}", file=sys.stderr)
        sys.exit(1)
    except LLMClientError as e:
        print(f"❌ ERRO DE COMUNICAÇÃO COM IA: {e}", file=sys.stderr)
        sys.exit(1)
    except ConductorException as e:
        print(f"❌ ERRO INESPERADO: {e}", file=sys.stderr)
        sys.exit(1)
    ```

### Fase 2: Implementação de Testes de Ciclo de Vida (E2E)

Este teste irá simular o uso real do framework, desde a criação de um agente até a sua execução, usando a própria CLI.

**Passo 2.1: Criar o Arquivo de Teste E2E**
*   **Ação:** Crie o arquivo `tests/e2e/test_full_lifecycle.py`.

**Passo 2.2: Implementar o Cenário de Teste**
*   **Ação:** Use o módulo `subprocess` do Python para chamar a CLI do `conductor` como um processo externo. Isso garante um teste de integração completo.
*   **Lógica do Teste:**
    1.  **Setup:** Defina um nome e um caminho para um agente de teste temporário (ex: `_TestDummyAgent` em `projects/_common/agents/`).
    2.  **CREATE:** Execute o `admin.py` via `subprocess` para criar o `_TestDummyAgent`. Use o comando `poetry run python src/cli/admin.py --agent AgentCreator_Agent --destination-path ... --input ...`.
    3.  **VALIDATE CREATE:** Verifique se o diretório do agente e seus arquivos (`agent.yaml`, `persona.md`) foram criados no local correto.
    4.  **EXECUTE:** Execute o `admin.py` novamente, desta vez para interagir com o `_TestDummyAgent` recém-criado. Envie um comando simples via `--input`.
    5.  **VALIDATE EXECUTION:** Verifique se a execução foi bem-sucedida e se o arquivo `state.json` do `_TestDummyAgent` foi atualizado com a interação.
    6.  **Cleanup:** Use `shutil.rmtree` para remover o diretório do `_TestDummyAgent`, garantindo que o teste seja idempotente.

## 4. Critérios de Sucesso Atualizados

A refatoração completa (plano principal + este adendo) será considerada um sucesso quando:

-   [ ] Todos os critérios do plano principal forem atendidos.
-   [ ] O novo teste em `tests/e2e/test_full_lifecycle.py` for implementado e passar com sucesso.
-   [ ] A execução da CLI com um ID de agente inválido resultar em uma mensagem de erro `AgentNotFoundError` amigável, em vez de um stack trace.
