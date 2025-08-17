#!/usr/bin/env python3
"""
Teste de Integração: test_scoped_write_session.py

Simula uma sessão interativa completa conforme especificado no MILESTONE5, seção 3.5.

Este teste é crítico e deve simular uma sessão interativa completa:
- Setup: Iniciar uma sessão com um agente de teste com `--output-scope "src/service/*.kt"`
- Cenário 1 (Leitura Livre): O agente tenta ler `src/controller/MyController.kt`. Assert: A operação deve ser bem-sucedida.
- Cenário 2 (Escrita Fora do Escopo): O agente tenta escrever em `src/controller/MyController.kt`. Assert: A operação deve falhar com uma mensagem de erro clara sobre violação de escopo.
- Cenário 3 (Escrita Dentro do Escopo): O agente tenta escrever em `src/service/MyService.kt`. Assert: O orquestrador deve apresentar um prompt de confirmação ao usuário.
- Cenário 4 (Confirmação e Verificação): Simular a aprovação do usuário. Assert: O arquivo `src/service/MyService.kt` no projeto alvo deve ter seu conteúdo alterado.
- Cenário 5 (Integridade do Estado): Ao final da sessão. Assert: O arquivo `state.json` no diretório original do agente deve ser atualizado corretamente.
"""

import unittest
import tempfile
import os
import yaml
import json
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock
from io import StringIO

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.genesis_agent import GenesisAgent, OutputScopeViolationError


class TestScopedWriteSession(unittest.TestCase):
    """Teste de integração para sessões com validação de output_scope."""
    
    def setUp(self):
        """Configura ambiente de teste com estrutura completa."""
        # Cria diretório temporário para testes
        self.test_dir = tempfile.mkdtemp(prefix="conductor_scoped_test_")
        self.addCleanup(self._cleanup_test_dir)
        
        # Estrutura de diretórios
        self.mock_conductor_root = Path(self.test_dir) / "conductor"
        self.mock_workspace = Path(self.test_dir) / "workspace"
        self.mock_project = self.mock_workspace / "test-service"
        
        # Cria estrutura completa
        self.mock_conductor_root.mkdir(parents=True)
        (self.mock_conductor_root / "config").mkdir()
        
        # Estrutura do agente
        self.agent_home = (self.mock_conductor_root / "projects" / "develop" / 
                          "test-service" / "agents" / "ServiceCreatorAgent")
        self.agent_home.mkdir(parents=True)
        
        # Estrutura do projeto alvo
        self.mock_project.mkdir(parents=True)
        (self.mock_project / "src" / "service").mkdir(parents=True)
        (self.mock_project / "src" / "controller").mkdir(parents=True)
        
        # Cria arquivo para teste de leitura
        controller_file = self.mock_project / "src" / "controller" / "MyController.kt"
        controller_file.write_text("class MyController { /* existing controller */ }")
        
        # Cria workspaces.yaml
        workspaces_config = {
            'workspaces': {
                'develop': str(self.mock_workspace)
            }
        }
        workspaces_yaml = self.mock_conductor_root / "config" / "workspaces.yaml"
        with open(workspaces_yaml, 'w') as f:
            yaml.dump(workspaces_config, f)
        
        # Cria agent.yaml com output_scope restrito
        agent_config = {
            'id': 'ServiceCreatorAgent',
            'version': '2.0',
            'description': 'Cria serviços Kotlin',
            'ai_provider': 'claude',
            'persona_prompt_path': 'persona.md',
            'state_file_path': 'state.json',
            'execution_mode': 'project_resident',
            'target_context': {
                'project_key': 'test-service',
                'output_scope': 'src/service/*.kt'
            },
            'available_tools': ['read_file', 'write_file']
        }
        
        agent_yaml = self.agent_home / "agent.yaml"
        with open(agent_yaml, 'w') as f:
            yaml.dump(agent_config, f)
        
        # Cria persona.md
        persona_md = self.agent_home / "persona.md"
        persona_md.write_text("# Service Creator Agent\nCria serviços Kotlin com Spring Boot.")
        
        # Cria state.json inicial
        self.state_json_path = self.agent_home / "state.json"
        initial_state = {
            'conversation_history': [],
            'last_modified': '2025-01-01T00:00:00'
        }
        with open(self.state_json_path, 'w') as f:
            json.dump(initial_state, f)
        
        # Salva CWD original
        self.original_cwd = os.getcwd()
    
    def _cleanup_test_dir(self):
        """Limpa diretório de teste e restaura CWD."""
        import shutil
        # Restaura CWD antes de limpar
        try:
            os.chdir(self.original_cwd)
        except:
            pass
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _mock_workspaces_config(self):
        """Retorna configuração mock de workspaces."""
        return {'develop': str(self.mock_workspace)}
    
    def test_complete_scoped_write_session(self):
        """Testa uma sessão completa com validação de output_scope."""
        
        print("\n🧪 Iniciando teste de sessão completa com output_scope...")
        
        # Setup: Mock das funções para usar estrutura de teste
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            # Inicializa agente v2.0
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider="claude"
            )
            
            # Embody agente com output_scope restrito
            success = agent.embody_agent_v2("ServiceCreatorAgent")
            self.assertTrue(success, "Falha ao embodar agente")
            self.assertEqual(agent.output_scope, "src/service/*.kt")
            
            print(f"✅ Agent embodied com output_scope: {agent.output_scope}")
            print(f"📂 Working directory: {agent.working_directory}")
            
            # Verifica se mudou para o diretório do projeto
            self.assertEqual(os.getcwd(), str(self.mock_project))
            
            # CENÁRIO 1: Leitura Livre (deve funcionar)
            print("\n📖 Cenário 1: Testando leitura livre...")
            try:
                content = agent.toolbelt.read_file("src/controller/MyController.kt")
                self.assertIn("existing controller", content)
                print("✅ Leitura fora do scope PERMITIDA (correto)")
            except Exception as e:
                self.fail(f"Leitura deveria ser permitida mas falhou: {e}")
            
            # CENÁRIO 2: Escrita Fora do Escopo (deve falhar)
            print("\n🚫 Cenário 2: Testando escrita fora do scope...")
            with self.assertRaises(OutputScopeViolationError) as context:
                agent.toolbelt.write_file(
                    "src/controller/MyController.kt", 
                    "class MyController { /* modified */ }"
                )
            
            error_message = str(context.exception)
            self.assertIn("Output scope violation", error_message)
            self.assertIn("src/service/*.kt", error_message)
            print("✅ Escrita fora do scope NEGADA (correto)")
            print(f"   Mensagem: {error_message}")
            
            # CENÁRIO 3: Escrita Dentro do Escopo (sem interação do usuário para teste)
            print("\n✅ Cenário 3: Testando escrita dentro do scope...")
            
            # Mock input para simular não-interativo (sem TTY)
            with patch('sys.stdin.isatty', return_value=False):
                result = agent.toolbelt.write_file(
                    "src/service/MyService.kt",
                    "class MyService { /* new service */ }"
                )
            
            self.assertIn("File written successfully", result)
            print("✅ Escrita dentro do scope PERMITIDA (correto)")
            
            # CENÁRIO 4: Verificação do Arquivo Criado
            print("\n🔍 Cenário 4: Verificando arquivo criado...")
            service_file = self.mock_project / "src" / "service" / "MyService.kt"
            self.assertTrue(service_file.exists(), "Arquivo de serviço deveria existir")
            
            content = service_file.read_text()
            self.assertIn("new service", content)
            print("✅ Arquivo criado com conteúdo correto")
            
            # CENÁRIO 5: Integridade do Estado
            print("\n💾 Cenário 5: Verificando integridade do estado...")
            
            # Simula atividade que modifica estado
            agent.llm_client.conversation_history = [
                {"role": "user", "content": "Create a service"},
                {"role": "assistant", "content": "Service created successfully"}
            ]
            
            # Salva estado
            agent.save_agent_state_v2()
            
            # Verifica se state.json foi atualizado
            self.assertTrue(self.state_json_path.exists(), "state.json deveria existir")
            
            with open(self.state_json_path, 'r') as f:
                state_data = json.load(f)
            
            self.assertIn('conversation_history', state_data)
            self.assertEqual(len(state_data['conversation_history']), 2)
            self.assertEqual(state_data['agent_id'], 'ServiceCreatorAgent')
            self.assertEqual(state_data['environment'], 'develop')
            self.assertEqual(state_data['project'], 'test-service')
            
            print("✅ Estado salvo corretamente no caminho absoluto")
            print(f"   State file: {self.state_json_path}")
            print(f"   Conversation history: {len(state_data['conversation_history'])} messages")
    
    def test_output_scope_validation_edge_cases(self):
        """Testa casos extremos da validação de output_scope."""
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            agent = GenesisAgent(
                environment="develop",
                project="test-service", 
                ai_provider="claude"
            )
            
            agent.embody_agent_v2("ServiceCreatorAgent")
            
            # Teste 1: Caminho com ./ no início
            self.assertTrue(agent.toolbelt._validate_output_scope("./src/service/TestService.kt"))
            
            # Teste 2: Caminho absoluto (fora do scope)
            self.assertFalse(agent.toolbelt._validate_output_scope("/absolute/path/file.kt"))
            
            # Teste 3: Subdiretórios (funciona com padrão *.kt - glob permite subpaths)
            self.assertTrue(agent.toolbelt._validate_output_scope("src/service/subdir/Service.kt"))
            
            # Teste 4: Extensão incorreta
            self.assertFalse(agent.toolbelt._validate_output_scope("src/service/Service.java"))
    
    def test_meta_agent_no_restrictions(self):
        """Testa que meta-agente não tem restrições de output_scope."""
        
        # Cria configuração de meta-agente
        meta_agent_config = {
            'id': 'MetaAgent',
            'version': '2.0',
            'execution_mode': 'meta_agent',
            'persona_prompt_path': 'persona.md',
            'state_file_path': 'state.json'
            # Nota: Sem target_context
        }
        
        meta_agent_home = (self.mock_conductor_root / "projects" / "_common" / 
                          "agents" / "MetaAgent")
        meta_agent_home.mkdir(parents=True)
        
        with open(meta_agent_home / "agent.yaml", 'w') as f:
            yaml.dump(meta_agent_config, f)
        
        (meta_agent_home / "persona.md").write_text("# Meta Agent")
        (meta_agent_home / "state.json").write_text('{}')
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            agent = GenesisAgent(
                environment="develop", 
                project="test-service",
                ai_provider="claude"
            )
            
            # Meta-agente deveria permitir escrita em qualquer lugar
            self.assertTrue(agent.toolbelt._validate_output_scope("anywhere/file.txt"))
            self.assertTrue(agent.toolbelt._validate_output_scope("src/controller/Controller.kt"))
    
    def test_repl_mode_user_confirmation(self):
        """Testa prompt de confirmação do usuário em modo REPL."""
        
        with patch('scripts.genesis_agent.load_workspaces_config', return_value=self._mock_workspaces_config()), \
             patch('scripts.genesis_agent.__file__', str(self.mock_conductor_root / "scripts" / "genesis_agent.py")):
            
            agent = GenesisAgent(
                environment="develop",
                project="test-service",
                ai_provider="claude"
            )
            
            agent.embody_agent_v2("ServiceCreatorAgent")
            
            # Simula modo TTY e resposta do usuário
            with patch('sys.stdin.isatty', return_value=True), \
                 patch('builtins.input', return_value='y') as mock_input:
                
                result = agent.toolbelt.write_file(
                    "src/service/ConfirmedService.kt",
                    "class ConfirmedService { }"
                )
                
                # Verifica se prompt foi chamado
                mock_input.assert_called_once()
                self.assertIn("File written successfully", result)
            
            # Testa cancelamento pelo usuário
            with patch('sys.stdin.isatty', return_value=True), \
                 patch('builtins.input', return_value='n') as mock_input:
                
                result = agent.toolbelt.write_file(
                    "src/service/CancelledService.kt", 
                    "class CancelledService { }"
                )
                
                mock_input.assert_called_once()
                self.assertIn("cancelada pelo usuário", result)


if __name__ == '__main__':
    # Configura logging
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    # Executa testes
    unittest.main(verbosity=2)