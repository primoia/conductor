# Especificação Técnica e Plano de Execução: 0042-A-teste-integracao-final

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa é o teste de integração final da SAGA-017, validando toda a arquitetura Maestro-Executor construída nos estágios anteriores. Seu propósito é demonstrar que o ConductorService consegue descobrir, carregar e integrar os agentes Maestro e Executor, provando que a arquitetura de três camadas está funcionalmente completa. Este teste é a validação final de que a SAGA-017 cumpriu seu mandato de eliminar o cisma arquitetônico e estabelecer uma base sólida para a futura evolução da plataforma.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Teste de Integração:** O teste **DEVE** ser um teste de integração end-to-end que valide toda a arquitetura.
- **ConductorService:** O teste **DEVE** usar o ConductorService para descobrir e carregar os agentes.
- **Validação Completa:** O teste **DEVE** validar que ambos os agentes (Maestro e Executor) são descobertos e carregados corretamente.
- **Arquitetura de Três Camadas:** O teste **DEVE** demonstrar que a comunicação entre os agentes funciona através do ConductorService.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um teste de integração em `tests/e2e/test_maestro_executor_integration.py` com o seguinte conteúdo:

```python
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
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho será considerado concluído **somente quando**:
- O arquivo `tests/e2e/test_maestro_executor_integration.py` for criado
- O teste contiver todas as validações especificadas
- O teste validar a descoberta do Maestro Agent
- O teste validar a descoberta do Executor Agent
- O teste validar a comunicação entre os agentes
- O teste validar a completude da arquitetura
- O teste estiver pronto para execução

#### **6. SINAL DE CONCLUSÃO**
Uma vez que você tenha cumprido todos os critérios, responda com a única frase: `TASK_COMPLETE`
