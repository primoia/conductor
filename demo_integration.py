#!/usr/bin/env python3
"""
Demonstração Completa da Integração .bmad-core + conductor

Este script demonstra o fluxo completo de trabalho:
1. Simula uma história sendo criada
2. Simula o agente @dev analisando a história
3. Simula a criação de um plano de implementação
4. Executa o plano com o conductor
5. Valida os resultados
6. Gera um relatório final
"""

import yaml
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_conductor import ConductorExecutor


class IntegrationDemo:
    """Demonstração completa da integração."""
    
    def __init__(self):
        self.demo_story = None
        self.implementation_plan = None
        self.execution_results = None
        self.start_time = None
        
    def print_header(self, title):
        """Imprime um cabeçalho formatado."""
        print("\n" + "=" * 60)
        print(f"🎯 {title}")
        print("=" * 60)
    
    def print_step(self, step_number, title, description=""):
        """Imprime um passo da demonstração."""
        print(f"\n📋 Passo {step_number}: {title}")
        if description:
            print(f"   {description}")
    
    def simulate_story_creation(self):
        """Simula a criação de uma história."""
        self.print_step(1, "Criação da História", "Simulando uma história sendo criada no .bmad-core")
        
        self.demo_story = {
            "id": "story-001",
            "title": "Implementar Sistema de Usuários",
            "description": "Criar um sistema completo de gerenciamento de usuários com autenticação",
            "acceptance_criteria": [
                "Criar entidade User com campos: id, email, name, password_hash, created_at",
                "Implementar UserRepository com operações CRUD",
                "Criar UserService com lógica de negócio e validações",
                "Implementar UserController com endpoints REST",
                "Adicionar autenticação JWT",
                "Criar testes unitários e de integração"
            ],
            "priority": "High",
            "story_points": 8
        }
        
        print(f"✅ História criada:")
        print(f"   - ID: {self.demo_story['id']}")
        print(f"   - Título: {self.demo_story['title']}")
        print(f"   - Critérios de Aceitação: {len(self.demo_story['acceptance_criteria'])}")
        print(f"   - Prioridade: {self.demo_story['priority']}")
        print(f"   - Story Points: {self.demo_story['story_points']}")
    
    def simulate_dev_agent_analysis(self):
        """Simula o agente @dev analisando a história."""
        self.print_step(2, "Análise do Agente @dev", "Simulando o agente @dev analisando a história e quebrando em tarefas")
        
        print("🤖 Agente @dev ativado...")
        time.sleep(1)
        print("📖 Lendo história e critérios de aceitação...")
        time.sleep(1)
        print("🔍 Analisando arquitetura do projeto...")
        time.sleep(1)
        print("📋 Identificando dependências entre componentes...")
        time.sleep(1)
        print("🎯 Quebrando implementação em tarefas atômicas...")
        time.sleep(1)
        
        # Simular análise detalhada
        analysis_results = {
            "components_identified": ["User Entity", "User Repository", "User Service", "User Controller", "JWT Auth", "Tests"],
            "dependencies_mapped": [
                "User Entity → User Repository",
                "User Repository → User Service", 
                "User Service → User Controller",
                "User Service → JWT Auth",
                "All Components → Tests"
            ],
            "estimated_complexity": "Médio",
            "risk_factors": ["Autenticação JWT", "Validações de senha"],
            "parallel_tasks": ["Entity + Repository", "Service + Auth"]
        }
        
        print(f"✅ Análise concluída:")
        print(f"   - Componentes identificados: {len(analysis_results['components_identified'])}")
        print(f"   - Dependências mapeadas: {len(analysis_results['dependencies_mapped'])}")
        print(f"   - Complexidade estimada: {analysis_results['estimated_complexity']}")
        print(f"   - Fatores de risco: {len(analysis_results['risk_factors'])}")
    
    def simulate_plan_generation(self):
        """Simula a geração do plano de implementação."""
        self.print_step(3, "Geração do Plano", "Simulando o agente @dev gerando o plano de implementação YAML")
        
        print("📝 Gerando plano de implementação...")
        time.sleep(1)
        print("🔧 Definindo agentes especializados...")
        time.sleep(1)
        print("📋 Criando estrutura de tarefas...")
        time.sleep(1)
        print("✅ Definindo critérios de validação...")
        time.sleep(1)
        
        # Criar plano baseado na história
        self.implementation_plan = {
            "storyId": f"stories/{self.demo_story['id']}.md",
            "description": self.demo_story['title'],
            "tasks": [
                {
                    "name": "create-user-entity",
                    "description": "Criar entidade User com todos os campos necessários",
                    "agent": "KotlinEntityCreator_Agent",
                    "inputs": [f"stories/{self.demo_story['id']}.md#entity-definition"],
                    "outputs": ["src/main/kotlin/com/example/domain/entities/User.kt"],
                    "validation": ["User class compiles", "All required fields present"]
                },
                {
                    "name": "create-user-repository",
                    "description": "Criar UserRepository com operações CRUD",
                    "agent": "KotlinRepositoryCreator_Agent",
                    "inputs": ["src/main/kotlin/com/example/domain/entities/User.kt"],
                    "outputs": ["src/main/kotlin/com/example/domain/repositories/UserRepository.kt"],
                    "depends_on": "create-user-entity",
                    "validation": ["Repository extends JpaRepository", "CRUD methods available"]
                },
                {
                    "name": "create-user-service",
                    "description": "Criar UserService com lógica de negócio",
                    "agent": "KotlinServiceCreator_Agent",
                    "inputs": [
                        "src/main/kotlin/com/example/domain/entities/User.kt",
                        "src/main/kotlin/com/example/domain/repositories/UserRepository.kt"
                    ],
                    "outputs": ["src/main/kotlin/com/example/domain/services/UserService.kt"],
                    "depends_on": "create-user-repository",
                    "validation": ["Service has dependency injection", "Business logic implemented"]
                },
                {
                    "name": "create-jwt-auth",
                    "description": "Implementar autenticação JWT",
                    "agent": "KotlinAuthCreator_Agent",
                    "inputs": ["src/main/kotlin/com/example/domain/services/UserService.kt"],
                    "outputs": [
                        "src/main/kotlin/com/example/auth/JwtTokenProvider.kt",
                        "src/main/kotlin/com/example/auth/JwtAuthenticationFilter.kt"
                    ],
                    "depends_on": "create-user-service",
                    "validation": ["JWT token generation works", "Authentication filter configured"]
                },
                {
                    "name": "create-user-controller",
                    "description": "Criar UserController com endpoints REST",
                    "agent": "KotlinControllerCreator_Agent",
                    "inputs": [
                        "src/main/kotlin/com/example/domain/services/UserService.kt",
                        "src/main/kotlin/com/example/auth/JwtTokenProvider.kt"
                    ],
                    "outputs": ["src/main/kotlin/com/example/controllers/UserController.kt"],
                    "depends_on": "create-jwt-auth",
                    "validation": ["REST endpoints configured", "Authentication applied"]
                },
                {
                    "name": "create-tests",
                    "description": "Criar testes unitários e de integração",
                    "agent": "KotlinTestCreator_Agent",
                    "inputs": [
                        "src/main/kotlin/com/example/domain/entities/User.kt",
                        "src/main/kotlin/com/example/domain/services/UserService.kt",
                        "src/main/kotlin/com/example/controllers/UserController.kt"
                    ],
                    "outputs": [
                        "src/test/kotlin/com/example/domain/entities/UserTest.kt",
                        "src/test/kotlin/com/example/domain/services/UserServiceTest.kt",
                        "src/test/kotlin/com/example/controllers/UserControllerTest.kt"
                    ],
                    "depends_on": "create-user-controller",
                    "validation": ["All tests compile", "Test coverage > 80%"]
                }
            ],
            "validationCriteria": [
                "All Kotlin files compile without errors",
                "All unit tests pass with coverage above 80%",
                "User entity supports all required CRUD operations",
                "JWT authentication works correctly",
                "REST API endpoints respond correctly"
            ]
        }
        
        # Salvar plano em arquivo temporário
        plan_file = "demo-implementation-plan.yaml"
        with open(plan_file, 'w') as f:
            yaml.dump(self.implementation_plan, f, default_flow_style=False, indent=2)
        
        print(f"✅ Plano de implementação gerado:")
        print(f"   - Arquivo: {plan_file}")
        print(f"   - Tarefas: {len(self.implementation_plan['tasks'])}")
        print(f"   - Critérios de validação: {len(self.implementation_plan['validationCriteria'])}")
        print(f"   - Dependências: {sum(1 for task in self.implementation_plan['tasks'] if 'depends_on' in task)}")
        
        return plan_file
    
    def execute_plan(self, plan_file):
        """Executa o plano com o conductor."""
        self.print_step(4, "Execução do Plano", "Executando o plano com o sistema conductor")
        
        print("🎼 Iniciando Conductor...")
        time.sleep(1)
        
        executor = ConductorExecutor(plan_file)
        success = executor.run()
        
        self.execution_results = {
            "success": success,
            "tasks_executed": len(executor.executed_tasks),
            "tasks_failed": len(executor.failed_tasks),
            "execution_time": time.time() - self.start_time if self.start_time else 0
        }
        
        if success:
            print("✅ Execução concluída com sucesso!")
        else:
            print("❌ Execução falhou!")
        
        return success
    
    def generate_report(self):
        """Gera um relatório final da demonstração."""
        self.print_step(5, "Relatório Final", "Gerando relatório completo da demonstração")
        
        print("📊 RELATÓRIO DA DEMONSTRAÇÃO")
        print("=" * 40)
        
        # Informações da história
        print(f"\n📖 HISTÓRIA:")
        print(f"   - ID: {self.demo_story['id']}")
        print(f"   - Título: {self.demo_story['title']}")
        print(f"   - Prioridade: {self.demo_story['priority']}")
        print(f"   - Story Points: {self.demo_story['story_points']}")
        
        # Informações do plano
        print(f"\n📋 PLANO DE IMPLEMENTAÇÃO:")
        print(f"   - Tarefas: {len(self.implementation_plan['tasks'])}")
        print(f"   - Critérios de validação: {len(self.implementation_plan['validationCriteria'])}")
        
        # Informações da execução
        if self.execution_results:
            print(f"\n🎼 EXECUÇÃO:")
            print(f"   - Sucesso: {'✅ Sim' if self.execution_results['success'] else '❌ Não'}")
            print(f"   - Tarefas executadas: {self.execution_results['tasks_executed']}")
            print(f"   - Tarefas falharam: {self.execution_results['tasks_failed']}")
            print(f"   - Tempo de execução: {self.execution_results['execution_time']:.2f}s")
        
        # Benefícios da integração
        print(f"\n🚀 BENEFÍCIOS DA INTEGRAÇÃO:")
        print(f"   - ✅ Planejamento estruturado e reutilizável")
        print(f"   - ✅ Execução automatizada e consistente")
        print(f"   - ✅ Validação automática de resultados")
        print(f"   - ✅ Rastreabilidade completa")
        print(f"   - ✅ Facilita colaboração entre equipes")
        
        # Próximos passos
        print(f"\n🔮 PRÓXIMOS PASSOS:")
        print(f"   - Implementar agentes reais (substituir simulação)")
        print(f"   - Adicionar interface web para monitoramento")
        print(f"   - Integrar com CI/CD pipelines")
        print(f"   - Adicionar métricas e analytics")
        print(f"   - Expandir para outros tipos de projetos")
    
    def run_demo(self):
        """Executa a demonstração completa."""
        self.print_header("DEMONSTRAÇÃO COMPLETA: .bmad-core + conductor")
        
        self.start_time = time.time()
        
        try:
            # Passo 1: Simular criação da história
            self.simulate_story_creation()
            
            # Passo 2: Simular análise do agente @dev
            self.simulate_dev_agent_analysis()
            
            # Passo 3: Simular geração do plano
            plan_file = self.simulate_plan_generation()
            
            # Passo 4: Executar o plano
            success = self.execute_plan(plan_file)
            
            # Passo 5: Gerar relatório
            self.generate_report()
            
            # Limpeza
            if os.path.exists(plan_file):
                os.remove(plan_file)
            
            print(f"\n🎉 Demonstração concluída com {'sucesso' if success else 'falha'}!")
            return success
            
        except Exception as e:
            print(f"\n❌ Erro durante a demonstração: {e}")
            return False


def main():
    """Função principal."""
    demo = IntegrationDemo()
    success = demo.run_demo()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
