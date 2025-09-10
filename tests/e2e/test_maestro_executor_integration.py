"""
Teste de Integração Final: Arquitetura Maestro-Executor
Valida que o ConductorService consegue descobrir e carregar os agentes Maestro e Executor.
"""

import pytest
from src.ports.conductor_service import IConductorService
from src.container import Container


class TestMaestroExecutorIntegration:
    """Teste de integração final da arquitetura Maestro-Executor."""
    
    def setup_method(self):
        """Configuração inicial do teste."""
        self.container = Container()
        self.conductor_service = self.container.get_conductor_service()
    
    def test_discover_maestro_agent(self):
        """Testa se o Maestro Agent é descoberto corretamente."""
        agents = self.conductor_service.discover_agents()
        
        maestro_agent = next(
            (agent for agent in agents if agent.name == "Maestro_Agent"), 
            None
        )
        
        assert maestro_agent is not None, "Maestro Agent não foi descoberto"
        assert maestro_agent.name == "Maestro_Agent", "Nome do Maestro Agent incorreto"
        assert len(maestro_agent.capabilities) > 0, "Maestro Agent não possui capabilities"
        
        # Validar capabilities específicas do Maestro
        expected_capabilities = [
            "file_management", 
            "state_management", 
            "task_coordination", 
            "communication", 
            "planning"
        ]
        
        for expected_cap in expected_capabilities:
            assert expected_cap in maestro_agent.capabilities, f"Capability {expected_cap} não encontrada no Maestro Agent"
    
    def test_discover_executor_agent(self):
        """Testa se o Executor Agent é descoberto corretamente."""
        agents = self.conductor_service.discover_agents()
        
        executor_agent = next(
            (agent for agent in agents if agent.name == "Executor_Agent"), 
            None
        )
        
        assert executor_agent is not None, "Executor Agent não foi descoberto"
        assert executor_agent.name == "Executor_Agent", "Nome do Executor Agent incorreto"
        assert len(executor_agent.capabilities) > 0, "Executor Agent não possui capabilities"
        
        # Validar capabilities específicas do Executor
        expected_capabilities = [
            "code_execution", 
            "shell_commands", 
            "file_operations", 
            "validation", 
            "reporting"
        ]
        
        for expected_cap in expected_capabilities:
            assert expected_cap in executor_agent.capabilities, f"Capability {expected_cap} não encontrada no Executor Agent"
    
    def test_maestro_executor_communication(self):
        """Testa a comunicação entre Maestro e Executor através do ConductorService."""
        agents = self.conductor_service.discover_agents()
        
        maestro_agent = next(
            (agent for agent in agents if agent.name == "Maestro_Agent"), 
            None
        )
        executor_agent = next(
            (agent for agent in agents if agent.name == "Executor_Agent"), 
            None
        )
        
        assert maestro_agent is not None, "Maestro Agent não encontrado"
        assert executor_agent is not None, "Executor Agent não encontrado"
        
        # Validar que o Maestro tem capability de comunicação
        assert "communication" in maestro_agent.capabilities, "Maestro Agent não possui capability de comunicação"
        
        # Validar que o Executor tem capability de reporting
        assert "reporting" in executor_agent.capabilities, "Executor Agent não possui capability de reporting"
    
    def test_architecture_completeness(self):
        """Testa se a arquitetura de três camadas está completa."""
        agents = self.conductor_service.discover_agents()
        
        # Validar que temos pelo menos os dois agentes principais
        agent_names = [agent.name for agent in agents]
        assert "Maestro_Agent" in agent_names, "Arquitetura incompleta: Maestro Agent não encontrado"
        assert "Executor_Agent" in agent_names, "Arquitetura incompleta: Executor Agent não encontrado"
        
        # Validar que o ConductorService consegue carregar ferramentas
        self.conductor_service.load_tools()
        
        # Validar que o serviço está pronto para execução de tarefas
        assert hasattr(self.conductor_service, 'execute_task'), "ConductorService não possui método execute_task"
        
        print("✅ Arquitetura Maestro-Executor validada com sucesso!")
        print(f"📊 Total de agentes descobertos: {len(agents)}")
        print(f"🎭 Nomes dos agentes: {agent_names}")