# src/core/orchestrator.py

from typing import List

from src.core.domain import AgentDefinition
from src.core.agent_service import AgentService

class NoSuitableAgentFoundError(Exception):
    pass

class Orchestrator:
    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service
        # O LLM para a decisão semântica seria injetado aqui também
        # self.llm_client = llm_client 

    def find_best_agent_for_task(self, task_description: str) -> AgentDefinition:
        """
        Encontra o agente mais adequado para uma tarefa usando um processo de duas etapas.
        """
        # Etapa 0 (Simplificada): Extrair palavras-chave da tarefa.
        # Numa implementação real, isso usaria um LLM ou NLP. Aqui, faremos uma busca simples.
        required_capabilities = self._extract_keywords(task_description)

        # Etapa 1: Filtragem Rápida
        all_definitions = self.agent_service.list_all_agent_definitions()
        
        candidates = [
            defn for defn in all_definitions
            if any(cap in defn.capabilities for cap in required_capabilities)
        ]

        if not candidates:
            raise NoSuitableAgentFoundError(f"Nenhum agente encontrado com as capacidades: {required_capabilities}")

        if len(candidates) == 1:
            return candidates[0]

        # Etapa 2: Decisão Semântica (Placeholder)
        # Se tivéssemos múltiplos candidatos, aqui leríamos suas personas
        # e usaríamos um LLM para decidir qual é o melhor.
        # Por enquanto, retornamos o primeiro candidato encontrado.
        print(f"Múltiplos candidatos encontrados. Selecionando o primeiro: {[c.name for c in candidates]}")
        return candidates[0]

    def _extract_keywords(self, task_description: str) -> List[str]:
        """
        Placeholder para a lógica de extração de palavras-chave.
        """
        # Lógica simples para o exemplo.
        # Ex: "criar um scaffold para um agente" -> ["create_agent_scaffold"]
        if "scaffold" in task_description or "create agent" in task_description:
            return ["create_agent_scaffold"]
        if "commit message" in task_description:
            return ["generate_commit_message_from_diff"]
        return [word for word in task_description.split() if not word.isspace()]