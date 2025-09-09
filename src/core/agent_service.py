# src/core/agent_service.py

from typing import List
from src.core.domain import AgentInstance, AgentDefinition
# A classe de armazenamento será usada como uma interface, então importamos para type hinting
from src.infrastructure.filesystem_storage import FileSystemStorage 
from src.config import CURRENT_SUPPORTED_SCHEMA_VERSION

class AgentNotFoundError(Exception):
    pass

class CompatibilityError(Exception):
    pass

class AgentService:
    def __init__(self, storage_repository):
        # Usamos um nome genérico para a dependência, pois pode ser qualquer tipo de armazenamento
        self.storage = storage_repository

    def _validate_schema_version(self, definition: AgentDefinition):
        if definition.schema_version != CURRENT_SUPPORTED_SCHEMA_VERSION:
            raise CompatibilityError(
                f"Agente '{definition.name}' usa a versão de esquema '{definition.schema_version}', "
                f"mas o Conductor atualmente suporta a versão '{CURRENT_SUPPORTED_SCHEMA_VERSION}'."
            )

    def load_agent_instance(self, agent_name: str) -> AgentInstance:
        """
        Orquestra o carregamento completo de uma instância de agente a partir do repositório.
        """
        try:
            # 1. Usa o self.storage para carregar cada artefato individualmente.
            definition = self.storage.load_definition()
            
            # 2. Validate schema version immediately after loading definition
            self._validate_schema_version(definition)
            
            persona = self.storage.load_persona()
            playbook = self.storage.load_playbook()
            knowledge = self.storage.load_knowledge()
            history = self.storage.load_history()
            
            # 3. Constrói e retorna um objeto AgentInstance com os artefatos carregados.
            return AgentInstance(
                definition=definition,
                persona=persona,
                playbook=playbook,
                knowledge=knowledge,
                history=history
            )
        
        except FileNotFoundError as e:
            # 3. Levanta AgentNotFoundError se o agente não for encontrado.
            raise AgentNotFoundError(f"Agent '{agent_name}' not found: {str(e)}") from e

    def list_all_agent_definitions(self) -> List[AgentDefinition]:
        """
        Lista todas as definições de agente disponíveis no repositório.
        """
        return self.storage.list_all_agent_definitions()