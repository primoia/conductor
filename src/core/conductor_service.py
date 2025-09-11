# src/core/conductor_service.py
from typing import List
from src.ports.conductor_service import IConductorService
from src.core.domain import AgentDefinition, TaskDTO, TaskResultDTO
from src.core.services import (
    ConfigurationService,
    StorageService,
    AgentDiscoveryService,
    ToolManagementService,
    TaskExecutionService
)


class ConductorService(IConductorService):
    """Orquestrador principal - apenas coordena outros serviços."""

    def __init__(self, config_path: str = "config.yaml"):
        # Inicializa serviços especializados
        self._config_service = ConfigurationService(config_path)
        self._storage_service = StorageService(self._config_service)
        self._agent_service = AgentDiscoveryService(self._storage_service)
        self._tool_service = ToolManagementService(self._config_service)
        self._execution_service = TaskExecutionService(
            self._storage_service, 
            self._tool_service, 
            self._config_service
        )

    def discover_agents(self) -> List[AgentDefinition]:
        """Delega para AgentDiscoveryService."""
        return self._agent_service.discover_agents()

    def execute_task(self, task: TaskDTO) -> TaskResultDTO:
        """Delega para TaskExecutionService."""
        return self._execution_service.execute_task(task)

    def load_tools(self) -> None:
        """Delega para ToolManagementService."""
        self._tool_service.load_tools()