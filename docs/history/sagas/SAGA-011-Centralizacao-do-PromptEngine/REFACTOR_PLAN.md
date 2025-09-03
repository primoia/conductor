**Para:** Agente Implementador (Claude)
**De:** Arquiteto de Software (Gemini)
**Assunto:** Plano de Refatoração Arquitetural (v2): `PromptEngine` como Guardião de Contexto
**Saga:** SAGA-011

## 1. Visão e Objetivos

O objetivo desta refatoração é centralizar **toda a lógica de gerenciamento de contexto** em uma única classe dedicada, o `PromptEngine`. Isso evolui a proposta original de um simples "montador de strings" para um componente arquitetural robusto que será o único responsável por carregar, validar, processar e construir o prompt de um agente.

Esta mudança tornará o sistema mais coeso, desacoplado, testável e fácil de manter, representando um salto de maturidade na nossa arquitetura.

## 2. Análise e Proposta de Alteração

Com base em uma análise mais aprofundada, o plano original foi aprimorado para dar mais responsabilidades ao `PromptEngine`, simplificando os outros componentes.

### Alterações Arquiteturais Chave:

1.  **`PromptEngine` como Guardião de Contexto:** A classe não receberá mais o contexto pronto. Em vez disso, ela receberá o caminho do agente (`agent_home_path`) e será responsável por carregar e processar seus próprios dados (`agent.yaml`, `persona.md`).

2.  **Centralização da Lógica:** Métodos de lógica de negócio que estavam no `AgentLogic` (como carregar e validar configurações, processar placeholders da persona) serão movidos para o `PromptEngine`, que é seu lugar de direito.

3.  **Simplificação do `LLMClient`:** A interface do `LLMClient` será simplificada. Como o `PromptEngine` agora lida com todo o contexto, o `LLMClient` não precisa mais saber sobre a "persona". Ele se tornará um cliente "burro" que apenas recebe um prompt final e retorna uma resposta.

## 3. Plano de Execução Detalhado (em Fases)

### Fase 1: Criar o `PromptEngine` e Mover a Lógica de Contexto

1.  **Criar/Modificar `src/core/prompt_engine.py`:** Implemente a classe `PromptEngine` com a seguinte estrutura expandida.

    ```python
    # src/core/prompt_engine.py
    import logging
    from pathlib import Path
    from typing import List, Dict, Any

    logger = logging.getLogger(__name__)

    class PromptEngine:
        """
        Guardião central de todo o contexto de um agente.
        Responsável por carregar, processar e construir prompts.
        """
        def __init__(self, agent_home_path: Path):
            self.agent_home_path = agent_home_path
            self.persona_content: str = None
            self.agent_config: Dict[str, Any] = None
            logger.debug(f"PromptEngine inicializado para o caminho: {agent_home_path}")

        def load_context(self) -> None:
            """
            Carrega e processa todos os artefatos de contexto do agente.
            Esta é a principal função de inicialização.
            """
            self._load_agent_config()
            self._validate_agent_config()
            self._load_agent_persona()
            self._resolve_persona_placeholders()
            logger.info(f"Contexto para o agente em '{self.agent_home_path}' carregado com sucesso.")

        def build_prompt(self, conversation_history: List[Dict[str, Any]], user_input: str) -> str:
            """Constrói o prompt final usando o contexto já carregado."""
            # Implementação existente para formatar e montar o prompt...
            pass

        def _load_agent_config(self) -> None:
            """Lógica movida do AgentLogic para carregar agent.yaml."""
            # ...
            pass

        def _validate_agent_config(self) -> None:
            """Lógica movida do AgentLogic para validar a configuração."""
            # ...
            pass

        def _load_agent_persona(self) -> None:
            """Lógica movida do AgentLogic para carregar persona.md."""
            # ...
            pass

        def _resolve_persona_placeholders(self) -> None:
            """Lógica movida do AgentLogic para resolver placeholders na persona."""
            # ...
            pass
    ```

### Fase 2: Refatorar a Interface e Implementações do `LLMClient`

1.  **Modificar `src/ports/llm_client.py`:**
    *   Remova o método abstrato `set_persona(persona: str)`.
    *   Simplifique o método `invoke` para `invoke(prompt: str) -> str`.

2.  **Modificar `src/infrastructure/llm/cli_client.py`:**
    *   Atualize as classes `ClaudeCLIClient` e `GeminiCLIClient` para implementar a nova interface simplificada.
    *   Remova o atributo `self.agent_persona` e qualquer lógica relacionada a ele.

### Fase 3: Refatorar o `AgentLogic` para Orquestração Pura

1.  **Modificar `src/core/agent_logic.py`:**
    *   Remova os métodos que foram movidos para o `PromptEngine` (`_load_agent_config`, `_load_agent_persona`, etc.).
    *   Atualize o método de inicialização ou `embody_agent` para refletir a nova sequência.

    **Sequência de Inicialização ANTES:**
    ```python
    # Em AgentLogic.embody_agent():
    self.agent_config = self._load_agent_config()
    self.agent_persona = self._load_agent_persona()
    self.llm_client.set_persona(self.agent_persona)
    ```

    **Sequência de Inicialização DEPOIS:**
    ```python
    # Em AgentLogic.embody_agent():
    self.prompt_engine = PromptEngine(self.agent_home_path)
    self.prompt_engine.load_context()
    ```
    *   Atualize o método `chat` para que a chamada ao `llm_client.invoke` não passe mais a persona, apenas o prompt final construído pelo `prompt_engine`.

### Fase 4: Implementar Testes Robustos

1.  **Expandir `tests/core/test_prompt_engine.py`:**
    *   Adicione os seguintes casos de teste para cobrir as novas responsabilidades:
        *   `test_prompt_engine_load_context_happy_path`
        *   `test_prompt_engine_fails_on_missing_config`
        *   `test_prompt_engine_resolves_placeholders_correctly`

2.  **Criar Teste para `LLMClient`:**
    *   Crie um teste para validar que as implementações do `LLMClient` funcionam corretamente sem a lógica de `persona`.

3.  **Executar Testes de Regressão Completos:**
    *   Execute `poetry run pytest` para garantir que a refatoração não introduziu regressões no comportamento de ponta a ponta.

## 4. Critérios de Sucesso Expandidos

A tarefa será considerada um sucesso quando, além dos critérios anteriores:
- [ ] Os métodos de carregamento de contexto (`_load_...`) forem removidos do `AgentLogic` e existirem apenas no `PromptEngine`.
- [ ] A interface `LLMClient` e suas implementações estiverem simplificadas, sem o método `set_persona`.
- [ ] A classe `AgentLogic` estiver visivelmente mais enxuta, focada apenas em orquestração (delegando para o `StateRepository`, `PromptEngine`, e `LLMClient`).
- [ ] A cobertura de testes para o `PromptEngine` for superior a 90%.