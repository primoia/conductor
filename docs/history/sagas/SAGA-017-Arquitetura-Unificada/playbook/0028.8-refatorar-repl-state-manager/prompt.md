# Especificação Técnica e Plano de Execução: 0028.8-refatorar-repl-state-manager

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção visa eliminar as dependências de `agent_logic` nos módulos compartilhados (`repl_manager.py` e `state_manager.py`), resolvendo o `ImportError` e permitindo que os CLIs refatorados funcionem corretamente com a nova arquitetura baseada em `ConductorService`.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve modificar os arquivos `src/cli/shared/repl_manager.py` e `src/cli/shared/state_manager.py`.

**Arquivo 1 (Modificar): `src/cli/shared/repl_manager.py`**

```python
# src/cli/shared/repl_manager.py
import time
from typing import Dict, Callable, Any
# Remover import de AgentLogic se existir


class REPLManager:
    # ... (manter __init__ e outros métodos)

    def _show_agent_state(self):
        """Show current agent state."""
        print("\n📊 === ESTADO ATUAL DO AGENTE ===")
        print(f"🆔 Agent ID: {self.cli_instance.agent_id}")
        print(f"✅ Embodied: {self.cli_instance.embodied}")

        # Show environment/project if available
        if hasattr(self.cli_instance, "environment"):
            print(f"🌐 Environment: {self.cli_instance.environment}")
        if hasattr(self.cli_instance, "project"):
            print(f"📦 Project: {self.cli_instance.project}")

        # working_directory não é mais um atributo direto do cli_instance para todos os casos
        # Pode ser obtido via ConductorService se necessário, mas para o REPL, pode ser simplificado
        print("📂 Working Dir: N/A (gerenciado pelo ConductorService)")
        print("=" * 40)

    def _show_conversation_history(self):
        """Show conversation history."""
        print("\n💬 === HISTÓRICO DE CONVERSAS ===")

        # Obter histórico diretamente do cli_instance (que delega ao ConductorService)
        history = self.cli_instance.get_conversation_history()
        if not history:
            print("📭 Nenhuma mensagem no histórico")
        else:
            for i, msg in enumerate(history, 1):
                print(f"\n--- Mensagem {i} ---")
                print(f"👤 User: {msg.get('user_input', 'N/A')}") # Usar user_input
                response = msg.get('ai_response', 'N/A') # Usar ai_response
                print(
                    f"🤖 Assistant: {response[:200]}{'...' if len(response) > 200 else ''}"
                )
        print("=" * 50)

    def _clear_conversation_history(self):
        """Clear conversation history."""
        print("\n🗑️ === LIMPANDO HISTÓRICO ===")

        # Delegar limpeza ao cli_instance
        if self.cli_instance.clear_conversation_history():
            print("✅ Histórico limpo")
        else:
            print("❌ Falha ao limpar histórico")

        print("=" * 40)

    def _show_debug_info(self):
        """Show debug information."""
        print("\n🔍 === DEBUG: INFORMAÇÕES DO AGENTE ===")
        print(f"🆔 Agent ID: {self.cli_instance.agent_id}")
        print(f"✅ Embodied: {self.cli_instance.embodied}")
        print(f"🔧 Available Tools: {self.cli_instance.get_available_tools()}")

        if hasattr(self.cli_instance, "simulate_mode"):
            print(f"🎭 Simulation Mode: {self.cli_instance.simulate_mode}")

        print("=" * 50)

    # ... (manter outros métodos)
```

**Arquivo 2 (Modificar): `src/cli/shared/state_manager.py`**

```python
# src/cli/shared/state_manager.py
from typing import Any, Optional
# Remover import de AgentLogic se existir


class StateManager:
    # ... (manter __init__)

    def save_agent_state(self) -> bool:
        """
        Save agent state with proper logging and error handling.

        Returns:
            True if successful, False otherwise
        """
        # Delegar a responsabilidade de salvar estado para o cli_instance
        # O cli_instance (AdminCLI/AgentCLI) agora chama ConductorService.save_state
        return self.cli_instance.save_agent_state()

    def get_agent_status(self) -> dict:
        """
        Get comprehensive agent status.

        Returns:
            Dictionary with agent status information
        """
        status = {
            "embodied": self.cli_instance.embodied,
            "agent_id": self.cli_instance.agent_id,
            "working_directory": "N/A (gerenciado pelo ConductorService)",
            "environment": getattr(self.cli_instance, "environment", None),
            "project": getattr(self.cli_instance, "project", None),
            "available_tools": self.cli_instance.get_available_tools(),
            "output_scope": [],
        }

        if hasattr(self.cli_instance, "get_output_scope"):
            status["output_scope"] = self.cli_instance.get_output_scope()

        return status

    def get_conversation_history(self) -> list:
        """
        Get conversation history if available.

        Returns:
            List of conversation messages or empty list
        """
        # Delegar ao cli_instance
        return self.cli_instance.get_conversation_history()

    def clear_conversation_history(self) -> bool:
        """
        Clear conversation history and save state.

        Returns:
            True if successful, False otherwise
        """
        # Delegar ao cli_instance
        return self.cli_instance.clear_conversation_history()

    # ... (manter outros métodos)
```

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
