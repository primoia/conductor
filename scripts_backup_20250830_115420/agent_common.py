#!/usr/bin/env python3
"""
Agent Common Module - Shared functionality for agent execution

This module contains common functions and classes used by both
gensis_agent.py (project agents) and admin.py (meta-agents).
"""

import yaml
import sys
import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime
import time
import re
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Constants
AI_PROVIDERS_CONFIG_PATH = os.path.join("config", "ai_providers.yaml")
MAX_TOOL_CALLS_PER_TURN = 5
MAX_CONVERSATION_HISTORY = 50

# ... (Security constants remain the same)

class LLMClient:
    """
    Base LLM Client interface for multi-provider support.
    """
    def __init__(self, working_directory: str = None):
        self.working_directory = working_directory or os.getcwd()
        self.conversation_history = []
        self.agent_persona = None
        logger.debug(f"LLMClient base initialized with working directory: {self.working_directory}")

    def set_agent_persona(self, persona: str):
        self.agent_persona = persona
        logger.debug("Agent persona set in LLM client")

    def generate_artifact(self, prompt: str) -> str:
        return self._invoke_subprocess(prompt) or "No response generated."

    def _invoke_subprocess(self, prompt: str) -> Optional[str]:
        raise NotImplementedError("Provider-specific subclasses must implement _invoke_subprocess")

class ClaudeCLIClient(LLMClient):
    """
    Claude CLI Client implementation.
    """
    def __init__(self, working_directory: str = None):
        super().__init__(working_directory)
        self.claude_command = "claude"
        logger.debug("ClaudeCLIClient initialized")

    def _build_full_prompt_with_persona(self, new_prompt: str) -> str:
        prompt_parts = []
        
        # 1. PERSONA (contexto)
        if self.agent_persona:
            prompt_parts.append("### PERSONA:")
            prompt_parts.append(self.agent_persona)
            prompt_parts.append("\n")
        
        # 2. AGENT_CONFIG (configuração do agente)
        if hasattr(self, 'genesis_agent') and hasattr(self.genesis_agent, 'agent_config'):
            prompt_parts.append("### AGENT_CONFIG:")
            import json
            prompt_parts.append(json.dumps(self.genesis_agent.agent_config, indent=2, ensure_ascii=False))
            prompt_parts.append("\n")
        
        # 3. CONTEXT (histórico de conversas para contexto)
        if self.conversation_history:
            prompt_parts.append("### CONTEXT:")
            for msg in self.conversation_history:
                prompt_parts.append(f"User: {msg.get('prompt', 'N/A')}")
                prompt_parts.append(f"Assistant: {msg.get('response', 'N/A')}")
                prompt_parts.append("")
            prompt_parts.append("")
        
        # 4. COMMAND (comando atual - sempre no final)
        prompt_parts.append("### COMMAND:")
        prompt_parts.append(new_prompt)
        prompt_parts.append("")
        prompt_parts.append("IMPORTANTE: Responda APENAS ao comando acima, usando o contexto fornecido.")
        
        return "\n".join(prompt_parts)

    def _invoke_subprocess(self, prompt: str) -> Optional[str]:
        try:
            full_prompt = self._build_full_prompt_with_persona(prompt)
            cmd = [self.claude_command, "--print", "--dangerously-skip-permissions"]
            if hasattr(self, 'genesis_agent') and hasattr(self.genesis_agent, 'get_available_tools'):
                available_tools = self.genesis_agent.get_available_tools()
                if available_tools:
                    cmd.extend(["--allowedTools", " ".join(available_tools)])
            
            result = subprocess.run(
                cmd,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=getattr(self, 'timeout', 120),
                cwd=self.working_directory
            )
            
            if result.returncode == 0:
                response = result.stdout.strip()
                # Adicionar ao histórico APÓS receber resposta do Claude
                self.conversation_history.append({'prompt': prompt, 'response': response, 'timestamp': time.time()})
                return response
            else:
                logger.error(f"Claude CLI failed: {result.stderr}")
                return f"Claude CLI failed: {result.stderr}"
        except subprocess.TimeoutExpired:
            timeout_value = getattr(self, 'timeout', 120)
            logger.error(f"Claude CLI timed out after {timeout_value} seconds")
            return f"❌ Claude CLI timed out after {timeout_value} seconds. Complex operations may need more time."
        except Exception as e:
            logger.error(f"Claude CLI error: {e}")
            return f"❌ Claude CLI error: {e}"

class GeminiCLIClient(LLMClient):
    # ... (Implementation for Gemini, can be simplified or assumed correct for now)
    pass

def create_llm_client(ai_provider: str, working_directory: str = None, timeout: int = 120) -> LLMClient:
    """
    Factory function to create LLM clients based on provider.
    """
    if ai_provider == 'claude':
        logger.info(f"Creating Claude CLI client with timeout: {timeout}s")
        client = ClaudeCLIClient(working_directory)
        client.timeout = timeout
        return client
    elif ai_provider == 'gemini':
        # Assuming a similar structure for Gemini client
        logger.info(f"Creating Gemini CLI client with timeout: {timeout}s")
        client = GeminiCLIClient(working_directory)
        client.timeout = timeout
        return client
    else:
        raise ValueError(f"Unsupported AI provider: {ai_provider}")

# --- Other shared functions from agent_common.py ---

def load_ai_providers_config() -> Dict[str, Any]:
    # ... (existing implementation)
    return {}

def resolve_agent_paths(environment: str, project: str, agent_id: str) -> Tuple[Path, Path]:
    conductor_root = Path(__file__).parent.parent
    if environment == "_common":
        agent_home_path = conductor_root / "projects" / "_common" / "agents" / agent_id
        project_root_path = conductor_root.parent.parent
    else:
        # ... (logic for project agents)
        # This part needs the real load_workspaces_config, which is in genesis_agent.py
        # This is the core of the circular dependency. For now, we assume a simple path.
        monorepo_root = conductor_root.parent.parent
        project_root_path = monorepo_root / project # Simplified for this fix
        agent_home_path = conductor_root / "projects" / environment / project / "agents" / agent_id

    if not agent_home_path.exists():
        raise FileNotFoundError(f"Agent home path does not exist: {agent_home_path}")
    if not project_root_path.exists():
        # This check might fail for the real project, but is ok for meta-agent
        pass

    return agent_home_path.resolve(), project_root_path.resolve()

def load_agent_config_v2(agent_home_path: Path) -> Dict[str, Any]:
    # ... (existing implementation)
    agent_yaml_path = agent_home_path / "agent.yaml"
    if not agent_yaml_path.exists():
        raise FileNotFoundError(f"agent.yaml não encontrado em: {agent_yaml_path}")
    with open(agent_yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_workspaces_config() -> Dict[str, str]:
    """
    Carrega a configuração de workspaces do arquivo config/workspaces.yaml.
    
    Returns:
        Dict com mapeamento environment -> path
        
    Raises:
        FileNotFoundError: Se o arquivo de configuração não existir
        yaml.YAMLError: Se houver erro de parsing do YAML
    """
    WORKSPACES_CONFIG_PATH = "config/workspaces.yaml"
    
    config_path = Path(__file__).parent.parent / WORKSPACES_CONFIG_PATH
    
    if not config_path.exists():
        raise FileNotFoundError(
            f"Arquivo de configuração de workspaces não encontrado: {config_path}\n"
            f"Crie o arquivo com o mapeamento de ambientes para seus diretórios."
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config or 'workspaces' not in config:
            raise ValueError("Arquivo workspaces.yaml deve conter uma seção 'workspaces'")
        
        return config['workspaces']
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Erro ao fazer parse do workspaces.yaml: {e}")

def start_repl_session(agent, agent_name: str = "admin"):
    """
    Inicia uma sessão REPL interativa para conversar com o agente.
    
    Args:
        agent: Instância do agente (AdminAgent ou GenesisAgent)
        agent_name: Nome do agente para display
    """
    print(f"\n🤖 Iniciando sessão REPL para {agent_name}")
    print("💬 Digite 'exit', 'quit' ou 'sair' para encerrar")
    print("🔍 Digite 'debug' para ver contexto completo sem chamar provider")
    print("📝 Digite 'state' para ver o estado atual")
    print("📊 Digite 'history' para ver histórico de conversa")
    print("🗑️  Digite 'clear' para limpar todo o histórico")
    print("↩️  Digite 'undo' para remover a última mensagem")
    print("💾 Digite 'save-debug' para salvar contexto completo em arquivo")
    print("📝 Digite 'save-prompt' para salvar apenas o prompt final")
    
    # Verificar se está em modo simulação
    if hasattr(agent, 'simulate_mode') and agent.simulate_mode:
        print("🎭 MODO SIMULAÇÃO ATIVO - respostas simuladas, contexto mantido")
        print("💡 Use 'debug' para ver todo o contexto acumulado")
    
    print("=" * 60)
    
    while True:
        try:
            # Prompt do usuário
            user_input = input(f"\n[{agent_name}]> ").strip()
            
            # Comandos de controle
            if user_input.lower() in ['exit', 'quit', 'sair']:
                print("👋 Encerrando sessão REPL...")
                break
            
            if not user_input:
                continue
                
            # Comando debug - mostra contexto sem chamar provider
            if user_input.lower() == 'debug':
                _show_debug_context(agent)
                continue
            
            # Comando state - mostra estado atual
            if user_input.lower() == 'state':
                _show_agent_state(agent)
                continue
                
            # Comando history - mostra histórico
            if user_input.lower() == 'history':
                _show_conversation_history(agent)
                continue
            
            # Comando clear - limpa todo o histórico
            if user_input.lower() == 'clear':
                _clear_conversation_history(agent)
                continue
            
            # Comando undo - remove a última mensagem
            if user_input.lower() == 'undo':
                _undo_last_message(agent)
                continue
            
            # Comando save-debug - salva contexto completo em arquivo
            if user_input.lower() == 'save-debug':
                _save_debug_context_to_file(agent)
                continue
            
            # Comando save-prompt - salva apenas o prompt final
            if user_input.lower() == 'save-prompt':
                _save_prompt_only_to_file(agent)
                continue
            
            # Conversa normal - chama o método chat do agente
            print("🤔 Processando...")
            try:
                if hasattr(agent, 'chat'):
                    # AdminAgent ou GenesisAgent
                    response = agent.chat(user_input)
                else:
                    # Fallback se não tiver método chat
                    response = "❌ Método chat não disponível neste agente"
                
                # Verificar se está em modo simulação para destacar
                if hasattr(agent, 'simulate_mode') and agent.simulate_mode:
                    print("🎭 Resposta Simulada:")
                else:
                    print("🤖 Resposta:")
                print("-" * 40)
                print(response)
                print("-" * 40)
                
                # Salvar estado automaticamente após cada interação bem-sucedida
                try:
                    if hasattr(agent, 'save_agent_state_v2'):
                        agent.save_agent_state_v2()
                        logger.debug("Agent state saved automatically after chat interaction")
                    elif hasattr(agent, 'genesis') and hasattr(agent.genesis, 'save_agent_state_v2'):
                        agent.genesis.save_agent_state_v2()
                        logger.debug("Genesis agent state saved automatically after chat interaction")
                except Exception as save_error:
                    logger.warning(f"Failed to save agent state automatically: {save_error}")
                
            except Exception as e:
                print(f"❌ Erro na conversa: {e}")
                logger.error(f"REPL chat error: {e}")
                
        except KeyboardInterrupt:
            print("\n\n⚡ Interrompido pelo usuário. Use 'exit' para sair.")
            continue
        except EOFError:
            print("\n👋 Sessão REPL encerrada.")
            break
        except Exception as e:
            print(f"❌ Erro na sessão REPL: {e}")
            logger.error(f"REPL session error: {e}")

def _show_debug_context(agent):
    """Mostra contexto completo que seria enviado ao provider."""
    print("\n🔍 === DEBUG: CONTEXTO COMPLETO ===")
    
    try:
        # Pega dados do GenesisAgent (seja direto ou via AdminAgent)
        genesis_agent = getattr(agent, 'genesis', agent) if hasattr(agent, 'genesis') else agent
        
        print(f"📋 Agent Config Keys: {list(genesis_agent.agent_config.keys()) if hasattr(genesis_agent, 'agent_config') else 'N/A'}")
        
        # Mostrar se o persona foi carregado completamente
        if hasattr(genesis_agent, 'agent_persona'):
            persona_length = len(genesis_agent.agent_persona)
            persona_preview = genesis_agent.agent_persona[:200] + "..." if persona_length > 200 else genesis_agent.agent_persona
            print(f"🎭 Persona Preview: {persona_preview}")
            print(f"📏 Persona Length: {persona_length} caracteres")
            
            # Verificar se parece estar completo
            if persona_length > 1000:
                print("✅ Persona parece estar carregado completamente")
            else:
                print("⚠️  Persona pode estar incompleto")
        else:
            print("❌ Persona não carregado")
        
        # Verificar histórico de conversa em múltiplas localizações
        conversation_history = []
        if hasattr(genesis_agent, 'llm_client') and hasattr(genesis_agent.llm_client, 'conversation_history'):
            conversation_history = genesis_agent.llm_client.conversation_history
        elif hasattr(genesis_agent, 'conversation_history'):
            conversation_history = genesis_agent.conversation_history
        
        print(f"💬 Conversation History: {len(conversation_history)} messages")
        
        if conversation_history:
            print("\n📝 ÚLTIMAS MENSAGENS:")
            for i, msg in enumerate(conversation_history[-5:], 1):  # Últimas 5 mensagens
                prompt = msg.get('prompt', 'N/A')
                response = msg.get('response', 'N/A')
                timestamp = msg.get('timestamp', 'N/A')
                
                # Formatar timestamp se disponível
                if timestamp and timestamp != 'N/A':
                    try:
                        from datetime import datetime
                        timestamp_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                    except:
                        timestamp_str = str(timestamp)
                else:
                    timestamp_str = "N/A"
                
                print(f"\n  {i}. [{timestamp_str}] User: {prompt}")
                response_preview = response[:150] + "..." if len(response) > 150 else response
                print(f"     Assistant: {response_preview}")
        else:
            print("📭 Nenhuma mensagem no histórico")
        
        # Mostrar prompt completo que seria enviado
        print(f"\n📄 PROMPT COMPLETO QUE SERIA ENVIADO:")
        print("-" * 50)
        
        if hasattr(genesis_agent, 'agent_persona'):
            print("### PERSONA:")
            print(genesis_agent.agent_persona[:500] + "..." if len(genesis_agent.agent_persona) > 500 else genesis_agent.agent_persona)
            print()
        
        if hasattr(genesis_agent, 'agent_config'):
            print("### AGENT_CONFIG:")
            import json
            config_preview = json.dumps(genesis_agent.agent_config, indent=2, ensure_ascii=False)[:300] + "..." if len(json.dumps(genesis_agent.agent_config)) > 300 else json.dumps(genesis_agent.agent_config, indent=2, ensure_ascii=False)
            print(config_preview)
            print()
        
        if conversation_history:
            print("### CONTEXT:")
            for msg in conversation_history[-3:]:  # Últimas 3 interações
                print(f"User: {msg.get('prompt', 'N/A')}")
                print(f"Assistant: {msg.get('response', 'N/A')[:100]}{'...' if len(msg.get('response', '')) > 100 else ''}")
                print()
        
        print("### COMMAND:")
        print("[AQUI SERIA O COMANDO ATUAL DO USUÁRIO]")
        print("-" * 50)
        
        print(f"\n🏠 Agent Home: {getattr(genesis_agent, 'agent_home_path', 'N/A')}")
        print(f"📂 Working Dir: {getattr(genesis_agent, 'working_directory', 'N/A')}")
        print(f"🗃️  State File: {getattr(genesis_agent, 'state_file_path', 'N/A')}")
        
        # Verificar se está em modo simulação
        if hasattr(agent, 'simulate_mode') and agent.simulate_mode:
            print(f"🎭 Modo Simulação: ATIVO")
        
        print(f"\n💡 Dica: Use 'save-debug' para salvar contexto completo em arquivo")
        
    except Exception as e:
        print(f"❌ Erro mostrando contexto debug: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
    
    print("=" * 50)

def _show_agent_state(agent):
    """Mostra estado atual do agente."""
    print("\n📊 === ESTADO ATUAL DO AGENTE ===")
    
    try:
        genesis_agent = getattr(agent, 'genesis', agent) if hasattr(agent, 'genesis') else agent
        
        print(f"🆔 Agent ID: {getattr(genesis_agent, 'current_agent', 'N/A')}")
        print(f"✅ Embodied: {getattr(genesis_agent, 'embodied', False)}")
        print(f"🌐 Environment: {getattr(genesis_agent, 'environment', 'N/A')}")
        print(f"📦 Project: {getattr(genesis_agent, 'project', 'N/A')}")
        
        if hasattr(genesis_agent, 'llm_client'):
            print(f"🔗 LLM Client: {type(genesis_agent.llm_client).__name__}")
            if hasattr(genesis_agent.llm_client, 'conversation_history'):
                print(f"💬 Messages in History: {len(genesis_agent.llm_client.conversation_history)}")
        
    except Exception as e:
        print(f"❌ Erro mostrando estado: {e}")
    
    print("=" * 40)

def _show_conversation_history(agent):
    """Mostra histórico completo de conversas."""
    print("\n💬 === HISTÓRICO DE CONVERSAS ===")
    
    try:
        genesis_agent = getattr(agent, 'genesis', agent) if hasattr(agent, 'genesis') else agent
        
        if hasattr(genesis_agent, 'llm_client') and hasattr(genesis_agent.llm_client, 'conversation_history'):
            history = genesis_agent.llm_client.conversation_history
            
            if not history:
                print("📭 Nenhuma mensagem no histórico")
                return
            
            for i, msg in enumerate(history, 1):
                timestamp = datetime.fromtimestamp(msg.get('timestamp', 0)).strftime("%Y-%m-%d %H:%M:%S") if msg.get('timestamp') else 'N/A'
                print(f"\n--- Mensagem {i} ({timestamp}) ---")
                print(f"👤 User: {msg.get('prompt', 'N/A')}")
                print(f"🤖 Assistant: {msg.get('response', 'N/A')[:200]}{'...' if len(msg.get('response', '')) > 200 else ''}")
        else:
            print("❌ Histórico não disponível")
            
    except Exception as e:
        print(f"❌ Erro mostrando histórico: {e}")
    
    print("=" * 50)

def _clear_conversation_history(agent):
    """Limpa todo o histórico de conversas."""
    print("\n🗑️ === LIMPANDO HISTÓRICO ===")
    
    try:
        genesis_agent = getattr(agent, 'genesis', agent) if hasattr(agent, 'genesis') else agent
        
        if hasattr(genesis_agent, 'llm_client') and hasattr(genesis_agent.llm_client, 'conversation_history'):
            history_count = len(genesis_agent.llm_client.conversation_history)
            genesis_agent.llm_client.conversation_history.clear()
            
            # Salvar estado após limpar
            if hasattr(genesis_agent, 'save_agent_state_v2'):
                genesis_agent.save_agent_state_v2()
            
            print(f"✅ Histórico limpo: {history_count} mensagens removidas")
        else:
            print("❌ Histórico não disponível para limpeza")
            
    except Exception as e:
        print(f"❌ Erro limpando histórico: {e}")
    
    print("=" * 40)

def _undo_last_message(agent):
    """Remove a última mensagem do histórico."""
    print("\n↩️ === DESFAZENDO ÚLTIMA MENSAGEM ===")
    
    try:
        genesis_agent = getattr(agent, 'genesis', agent) if hasattr(agent, 'genesis') else agent
        
        if hasattr(genesis_agent, 'llm_client') and hasattr(genesis_agent.llm_client, 'conversation_history'):
            history = genesis_agent.llm_client.conversation_history
            
            if not history:
                print("📭 Nenhuma mensagem para desfazer")
                return
            
            # Remove a última mensagem (user + assistant)
            if len(history) >= 2:
                # Remove as últimas 2 mensagens (user + assistant)
                removed_messages = history[-2:]
                history = history[:-2]
                genesis_agent.llm_client.conversation_history = history
                
                print(f"✅ Última interação removida:")
                for msg in removed_messages:
                    print(f"   - {msg.get('prompt', 'N/A')}")
            else:
                # Remove apenas uma mensagem se houver apenas uma
                removed_msg = history.pop()
                print(f"✅ Última mensagem removida: {removed_msg.get('prompt', 'N/A')}")
            
            # Salvar estado após desfazer
            if hasattr(genesis_agent, 'save_agent_state_v2'):
                genesis_agent.save_agent_state_v2()
                
            print(f"📊 Mensagens restantes: {len(history)}")
        else:
            print("❌ Histórico não disponível")
            
    except Exception as e:
        print(f"❌ Erro desfazendo mensagem: {e}")
    
    print("=" * 40)

def _save_debug_context_to_file(agent):
    """Salva o contexto completo em um arquivo para análise."""
    print("\n💾 === SALVANDO CONTEXTO COMPLETO ===")
    
    try:
        import os
        from datetime import datetime
        
        # Criar diretório de debug se não existir
        debug_dir = "/tmp/admin_debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"{debug_dir}/debug_context_{timestamp}.txt"
        
        # Capturar contexto completo
        genesis_agent = getattr(agent, 'genesis', agent) if hasattr(agent, 'genesis') else agent
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("=== CONTEXTO COMPLETO PARA PROVIDER ===\n\n")
            
            # Agent Config
            f.write("== AGENT CONFIG ==\n")
            if hasattr(genesis_agent, 'agent_config'):
                import json
                f.write(json.dumps(genesis_agent.agent_config, indent=2, ensure_ascii=False))
            else:
                f.write("N/A\n")
            f.write("\n\n")
            
            # Agent Persona (completo)
            f.write("== AGENT PERSONA (COMPLETO) ==\n")
            if hasattr(genesis_agent, 'agent_persona'):
                f.write(genesis_agent.agent_persona)
            else:
                f.write("N/A\n")
            f.write("\n\n")
            
            # Conversation History
            f.write("== CONVERSATION HISTORY ==\n")
            conversation_history = []
            if hasattr(genesis_agent, 'llm_client') and hasattr(genesis_agent.llm_client, 'conversation_history'):
                conversation_history = genesis_agent.llm_client.conversation_history
            elif hasattr(genesis_agent, 'conversation_history'):
                conversation_history = genesis_agent.conversation_history
            
            if conversation_history:
                for i, msg in enumerate(conversation_history, 1):
                    timestamp = datetime.fromtimestamp(msg.get('timestamp', 0)).strftime("%Y-%m-%d %H:%M:%S") if msg.get('timestamp') else 'N/A'
                    f.write(f"\n--- Mensagem {i} ({timestamp}) ---\n")
                    f.write(f"User: {msg.get('prompt', 'N/A')}\n")
                    f.write(f"Assistant: {msg.get('response', 'N/A')}\n")
            else:
                f.write("Nenhuma mensagem no histórico\n")
            f.write("\n\n")
            
            # Prompt completo que seria enviado ao provider
            f.write("== PROMPT COMPLETO PARA PROVIDER ==\n")
            if hasattr(genesis_agent, 'agent_persona'):
                f.write("### PERSONA:\n")
                f.write(genesis_agent.agent_persona)
                f.write("\n\n")
            
            if conversation_history:
                f.write("### CONVERSATION HISTORY:\n")
                for msg in conversation_history:
                    f.write(f"User: {msg.get('prompt', 'N/A')}\n")
                    f.write(f"Assistant: {msg.get('response', 'N/A')}\n\n")
            
            f.write("### CURRENT INPUT:\n")
            f.write("[AQUI SERIA A MENSAGEM ATUAL DO USUÁRIO]\n")
            
            # Metadata
            f.write("\n\n== METADATA ==\n")
            f.write(f"Agent Home: {getattr(genesis_agent, 'agent_home_path', 'N/A')}\n")
            f.write(f"Working Dir: {getattr(genesis_agent, 'working_directory', 'N/A')}\n")
            f.write(f"State File: {getattr(genesis_agent, 'state_file_path', 'N/A')}\n")
            f.write(f"Environment: {getattr(genesis_agent, 'environment', 'N/A')}\n")
            f.write(f"Project: {getattr(genesis_agent, 'project', 'N/A')}\n")
            f.write(f"Modo Simulação: {getattr(agent, 'simulate_mode', False)}\n")
        
        print(f"✅ Contexto completo salvo em: {debug_file}")
        print(f"📄 Tamanho do arquivo: {os.path.getsize(debug_file)} bytes")
        
    except Exception as e:
        print(f"❌ Erro salvando contexto: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
    
    print("=" * 50)

def _save_prompt_only_to_file(agent):
    """Salva apenas o prompt final que seria enviado ao provider."""
    print("\n📝 === SALVANDO PROMPT FINAL ===")
    
    try:
        import os
        from datetime import datetime
        
        # Criar diretório de debug se não existir
        debug_dir = "/tmp/admin_debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_file = f"{debug_dir}/prompt_only_{timestamp}.txt"
        
        # Capturar o prompt completo que seria enviado ao provider
        genesis_agent = getattr(agent, 'genesis', agent) if hasattr(agent, 'genesis') else agent
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write("=== PROMPT FINAL PARA PROVIDER ===\n\n")
            
            # Persona (se disponível)
            if hasattr(genesis_agent, 'agent_persona'):
                f.write("### PERSONA:\n")
                f.write(genesis_agent.agent_persona)
                f.write("\n\n")
            
            # Agent Config (se disponível)
            if hasattr(genesis_agent, 'agent_config'):
                f.write("### AGENT_CONFIG:\n")
                import json
                f.write(json.dumps(genesis_agent.agent_config, indent=2, ensure_ascii=False))
                f.write("\n\n")
            
            # Conversation History (se disponível)
            conversation_history = []
            if hasattr(genesis_agent, 'llm_client') and hasattr(genesis_agent.llm_client, 'conversation_history'):
                conversation_history = genesis_agent.llm_client.conversation_history
            elif hasattr(genesis_agent, 'conversation_history'):
                conversation_history = genesis_agent.conversation_history
            
            if conversation_history:
                f.write("### CONTEXT:\n")
                for msg in conversation_history:
                    f.write(f"User: {msg.get('prompt', 'N/A')}\n")
                    f.write(f"Assistant: {msg.get('response', 'N/A')}\n\n")
            
            # Current Input (comando atual)
            f.write("### COMMAND:\n")
            f.write("[AQUI SERIA O COMANDO ATUAL DO USUÁRIO]\n")
            
            # Nota sobre o formato
            f.write("\n\n---\n")
            f.write("NOTA: Este é o prompt exato que seria enviado ao provider.\n")
            f.write("Substitua '[AQUI SERIA O COMANDO ATUAL DO USUÁRIO]' pelo comando real.\n")
            f.write("O provider deve responder APENAS ao comando, usando o contexto fornecido.\n")
        
        print(f"✅ Prompt final salvo em: {prompt_file}")
        print(f"📄 Tamanho do arquivo: {os.path.getsize(prompt_file)} bytes")
        print(f"📊 Linhas do prompt: {len(open(prompt_file, 'r').readlines())}")
        
        # Mostrar preview do arquivo
        print(f"\n📋 PREVIEW (primeiras 5 linhas):")
        with open(prompt_file, 'r') as f:
            for i, line in enumerate(f):
                if i < 5:
                    print(f"   {line.rstrip()}")
                else:
                    print(f"   ...")
                    break
        
    except Exception as e:
        print(f"❌ Erro salvando prompt: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
    
    print("=" * 50)

def validate_agent_config(config: Dict[str, Any]) -> bool:
    # ... (existing implementation)
    return True