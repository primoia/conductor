from abc import ABC, abstractmethod


class LLMClient(ABC):
    """
    Interface abstrata para clientes de modelos de linguagem.
    """

    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """
        Invoca o modelo de linguagem com o prompt fornecido.

        Args:
            prompt: Texto de entrada para o modelo

        Returns:
            Resposta do modelo de linguagem
        """
        pass

    @abstractmethod
    def set_persona(self, persona: str) -> None:
        """
        Define a persona do agente para o cliente LLM.

        Args:
            persona: Texto da persona do agente
        """
        pass