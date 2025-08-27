#!/usr/bin/env python3
"""
Admin Executor - Meta-Agent Management CLI

This script implements the Admin Executor for meta-agents that manage the framework itself.
Following the Single Responsibility Principle, this script is focused exclusively on
administrative tasks and metadata management.

Meta-agents are located in projects/_common/agents/ and don't require project context.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import List
from datetime import datetime
import time # Added for time.time()

# Add the scripts directory to the path to import from genesis_agent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_common import (
    load_ai_providers_config,
    load_agent_config_v2,
    resolve_agent_paths,
    create_llm_client,
    start_repl_session,
    validate_agent_config
)

# Import GenesisAgent class for meta-agent execution
from core import GenesisAgent

# Configure admin logging
def setup_admin_logging(debug_mode: bool = False):
    """Setup logging for admin executor."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    admin_logger = logging.getLogger('admin_executor')
    admin_logger.setLevel(logging.DEBUG)
    admin_logger.handlers.clear()
    log_file = logs_dir / f"admin_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    if debug_mode:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        admin_logger.addHandler(console_handler)
    admin_logger.propagate = False
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    admin_logger.addHandler(file_handler)
    return admin_logger


class AdminAgent:
    """
    Admin Agent class for executing meta-agents that manage the framework.
    Uses GenesisAgent internally for consistent behavior.
    """
    
    def __init__(self, agent_id: str = None, ai_provider: str = None, logger = None, timeout: int = 90):
        """
        Initialize the Admin Agent for meta-agent execution.
        """
        self.logger = logger or logging.getLogger('admin_executor')
        self.timeout = timeout
        self.ai_provider_override = ai_provider
        self.destination_path = None
        self.simulate_mode = False  # Novo: modo de simulação
        self.genesis = GenesisAgent()
        
        if agent_id:
            self.embody_meta_agent(agent_id)
    
    def embody_meta_agent(self, agent_id: str) -> bool:
        """
        Embody a meta-agent for framework management using GenesisAgent.
        """
        try:
            # Override AI provider if specified
            if self.ai_provider_override:
                self.genesis.ai_provider_override = self.ai_provider_override
                
            # Set timeout
            self.genesis.timeout = self.timeout
            
            # Set environment and project for GenesisAgent
            self.genesis.environment = "_common"
            self.genesis.project = "_common"
            
            # Embody the agent using GenesisAgent v2
            success = self.genesis.embody_agent_v2(agent_id)
            
            if success:
                print(f"✅ Successfully embodied meta-agent: {agent_id}")
                self.logger.info(f"Embodied meta-agent: {agent_id}")
                
                # DEBUG: Log detalhado de carregamento
                if hasattr(self.genesis, 'agent_config'):
                    self.logger.info(f"Agent config loaded: {len(str(self.genesis.agent_config))} chars")
                    print(f"📋 Agent config: {list(self.genesis.agent_config.keys())}")
                
                if hasattr(self.genesis, 'agent_persona'):
                    persona_preview = str(self.genesis.agent_persona)[:100] + "..." if len(str(self.genesis.agent_persona)) > 100 else str(self.genesis.agent_persona)
                    self.logger.info(f"Agent persona loaded: {len(str(self.genesis.agent_persona))} chars")
                    print(f"🎭 Persona preview: {persona_preview}")
                
                if hasattr(self.genesis, 'llm_client') and hasattr(self.genesis.llm_client, 'conversation_history'):
                    hist_len = len(self.genesis.llm_client.conversation_history)
                    self.logger.info(f"Conversation history loaded: {hist_len} messages")
                    print(f"💬 History: {hist_len} messages loaded")
                
                return True
            else:
                print(f"❌ Failed to embody meta-agent {agent_id}")
                return False
        except Exception as e:
            print(f"❌ Failed to embody meta-agent {agent_id}: {e}")
            self.logger.error(f"Failed to embody meta-agent {agent_id}: {e}")
            return False
    
    @property
    def embodied(self) -> bool:
        """Check if agent is embodied."""
        return hasattr(self.genesis, 'current_agent') and self.genesis.current_agent is not None
        
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names from agent config."""
        if not hasattr(self.genesis, 'agent_config') or not self.genesis.agent_config:
            return []
        return self.genesis.agent_config.get('available_tools', [])
    
    
    def chat(self, message: str, debug_save_input: bool = False) -> str:
        """Send a message to the meta-agent."""
        if not self.embodied:
            return "❌ No agent embodied. Use embody_meta_agent() first."
        try:
            self.logger.info(f"Processing chat message: {message[:100]}...")
            
            # Adicionar DESTINATION_PATH se disponível
            enhanced_message = message
            if self.destination_path:
                enhanced_message = f"DESTINATION_PATH={self.destination_path}\n\n{message}"
                self.logger.info(f"Enhanced message with destination path: {self.destination_path}")
            
            # DEBUG: Salvar input completo antes de enviar ao provider
            if debug_save_input:
                import os
                from datetime import datetime
                debug_dir = "/tmp/admin_debug"
                os.makedirs(debug_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_file = f"{debug_dir}/input_final_{timestamp}.txt"
                
                # Capturar contexto completo que seria enviado
                debug_context = {
                    "timestamp": timestamp,
                    "agent_config": getattr(self.genesis, 'agent_config', {}),
                    "agent_persona": getattr(self.genesis, 'agent_persona', 'Not loaded'),
                    "conversation_history": getattr(self.genesis.llm_client, 'conversation_history', []) if hasattr(self.genesis, 'llm_client') else [],
                    "user_input": enhanced_message,
                    "destination_path": self.destination_path,
                    "environment": getattr(self.genesis, 'environment', 'unknown'),
                    "project": getattr(self.genesis, 'project', 'unknown'),
                    "agent_home_path": str(getattr(self.genesis, 'agent_home_path', 'unknown'))
                }
                
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write("=== DEBUG: INPUT COMPLETO PARA PROVIDER ===\n\n")
                    for key, value in debug_context.items():
                        f.write(f"== {key.upper()} ==\n")
                        f.write(f"{value}\n\n")
                
                self.logger.info(f"DEBUG: Input completo salvo em {debug_file}")
                print(f"🔍 DEBUG: Contexto completo salvo em {debug_file}")
                
                # Retornar sem chamar o provider para análise
                return f"✅ DEBUG MODE: Input capturado e salvo em {debug_file}. Provider NÃO foi chamado."
            
            # MODO SIMULAÇÃO: Retorna resposta simulada sem chamar provider
            if self.simulate_mode:
                # Adiciona à conversa history para manter contexto
                if hasattr(self.genesis, 'llm_client') and hasattr(self.genesis.llm_client, 'conversation_history'):
                    self.genesis.llm_client.conversation_history.append({
                        'prompt': enhanced_message,
                        'response': f"[SIMULATED] Resposta simulada para: {enhanced_message}",
                        'timestamp': time.time()
                    })
                    
                    # Salvar estado automaticamente após adicionar ao histórico
                    try:
                        self.genesis.save_agent_state_v2()
                        self.logger.debug("State saved automatically in simulation mode")
                    except Exception as save_error:
                        self.logger.warning(f"Failed to save state in simulation mode: {save_error}")
                
                # Retorna resposta simulada
                simulated_response = f"""🎭 [MODO SIMULAÇÃO] 

Olá! Sou o {getattr(self.genesis, 'current_agent', 'AgentCreator_Agent')} em modo simulação.

Recebi sua mensagem: "{enhanced_message}"

Esta é uma resposta simulada que não chama o provider real. O contexto da conversa está sendo mantido para que você possa usar o comando 'debug' para ver todo o histórico acumulado.

Para ver o contexto completo, digite 'debug' no REPL.

---
💡 Dica: Use 'debug' para ver todo o contexto que seria enviado ao provider
📊 Use 'history' para ver o histórico de conversas simuladas
"""
                self.logger.info(f"SIMULATION: Generated simulated response for: {enhanced_message[:50]}...")
                return simulated_response
            
            response = self.genesis.chat(enhanced_message)
            self.logger.info(f"Chat response received: {len(response) if response else 0} chars")
            return response
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            return f"❌ Error in chat: {e}"
    
    def generate_artifact(self, prompt: str) -> str:
        """Generate an artifact using the generation provider with fallback."""
        if not self.embodied:
            return "❌ No agent embodied. Use embody_meta_agent() first."
        try:
            # Use GenesisAgent's chat method with generation-specific prompt
            enhanced_prompt = f"GENERATE ARTIFACT: {prompt}"
            response = self.genesis.chat(enhanced_prompt)
            return response
        except Exception as e:
            self.logger.error(f"Artifact generation failed: {e}")
            return f"❌ Error generating artifact: {e}"
    
    def save_agent_state_v2(self):
        """Save agent state to file using GenesisAgent."""
        if not self.embodied:
            print("⚠️  No agent state to save")
            return
        try:
            self.genesis.save_agent_state_v2()
            self.logger.info("Agent state saved successfully")
        except Exception as e:
            print(f"❌ Failed to save state: {e}")
            self.logger.error(f"Failed to save state: {e}")
    
    @staticmethod
    def create_initial_state_file(agent_id: str, state_file_path: str):
        """Create initial state.json for a new agent."""
        from datetime import datetime
        import json
        try:
            state_data = {
                'agent_id': agent_id,
                'timestamp': datetime.now().isoformat(),
                'conversation_history': []
            }
            with open(state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Created initial state.json: {state_file_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create state.json: {e}")
            return False

def main():
    """Main function for admin.py CLI."""
    parser = argparse.ArgumentParser(
        description='Admin Executor CLI - Meta-Agent Management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/admin.py --agent AgentCreator_Agent --repl
    python scripts/admin.py --agent AgentCreator_Agent --repl --simulate-chat
    python scripts/admin.py --agent AgentCreator_Agent --destination-path "/path/to/new/agent" --input "Create an agent"
    python scripts/admin.py --agent migrate_agents_v2
        """
    )
    parser.add_argument('--agent', type=str, required=True,
                        help='Meta-agent ID to embody (required)')
    parser.add_argument('--ai-provider', type=str, default=None, 
                        choices=['claude', 'gemini'], 
                        help='AI provider override (uses dual provider system by default)')
    parser.add_argument('--repl', action='store_true', 
                        help='Start interactive REPL')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode (shows logs in console)')
    parser.add_argument('--input', type=str, default=None,
                        help='Input message to send to agent (non-interactive mode)')
    parser.add_argument('--destination-path', type=str, default=None,
                        help='Absolute path where the agent should be created (required for AgentCreator_Agent)')
    parser.add_argument('--timeout', type=int, default=90,
                        help='Timeout in seconds for AI operations (default: 90)')
    parser.add_argument('--debug-input', action='store_true',
                        help='DEBUG: Salva input completo sem chamar provider')
    parser.add_argument('--simulate-chat', action='store_true',
                        help='Simula respostas do agente sem chamar o provider (útil para construir contexto)')
    args = parser.parse_args()
    
    # Explicação do modo simulação
    if args.simulate_chat:
        print("""
🎭 MODO SIMULAÇÃO ATIVADO

Este modo permite:
- Simular conversas sem chamar o provider real
- Manter contexto da conversa para análise
- Usar 'debug' para ver todo o contexto acumulado
- Testar fluxos de conversa sem custo de API

Uso recomendado:
1. Inicie com --simulate-chat --repl
2. Faça várias interações para construir contexto
3. Use 'debug' para ver todo o contexto que seria enviado
4. Use 'history' para ver o histórico de conversas simuladas
""")
    logger = setup_admin_logging(debug_mode=args.debug)
    try:
        print(f"🚀 Iniciando Admin Executor")
        print(f"   Meta-agent: {args.agent}")
        if args.debug:
            print(f"   Debug mode: enabled")
            print(f"   Logs: logs/admin_{datetime.now().strftime('%Y%m%d')}.log")
        logger.info(f"Starting Admin Executor for meta-agent: {args.agent}")
        agent = AdminAgent(
            agent_id=args.agent,
            ai_provider=args.ai_provider,
            logger=logger,
            timeout=args.timeout
        )
        if not agent.embodied:
            print(f"❌ Failed to embody meta-agent: {args.agent}")
            logger.error(f"Failed to embody meta-agent: {args.agent}")
            exit(1)
        
        # Configurar modo de simulação se ativado
        if args.simulate_chat:
            agent.simulate_mode = True
            print(f"🎭 Modo simulação ativado - respostas simuladas sem chamar provider")
        
        print(f"🔓 No output restrictions (meta-agent)")
        logger.info("Admin Agent successfully initialized")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        logger.error(f"Admin Agent initialization failed: {e}")
        exit(1)
    if args.repl:
        logger.info("Starting REPL session")
        # Passar informação sobre modo de simulação para o REPL
        if args.simulate_chat:
            print(f"🎭 REPL iniciado em modo simulação - use 'debug' para ver contexto completo")
        start_repl_session(agent, "admin")
        logger.info("REPL session completed")
    elif args.input and agent.embodied:
        logger.info(f"Processing input message: {args.input[:100]}...")
        
        # Set destination path if provided for AgentCreator_Agent
        if args.destination_path and args.agent == 'AgentCreator_Agent':
            agent.destination_path = args.destination_path
            # Add destination path to the agent's environment for the LLM client
            if hasattr(agent.genesis, 'llm_client') and agent.genesis.llm_client:
                # Store in a way that the agent can access it
                if not hasattr(agent.genesis.llm_client, 'genesis_agent'):
                    agent.genesis.llm_client.genesis_agent = agent
                # The input will include the destination path information
                enhanced_input = f"DESTINATION_PATH={args.destination_path}\n\n{args.input}"
                logger.info(f"Enhanced input with destination path: {args.destination_path}")
        else:
            enhanced_input = args.input
            
        print(f"\n🤖 Processing input for {args.agent}:")
        print(f"📝 Input: {args.input}")
        if args.destination_path:
            print(f"📍 Destination: {args.destination_path}")
        print("-" * 60)
        try:
            # Ativar modo debug para interceptar input
            debug_mode = "--debug-input" in sys.argv
            # Verificar se modo simulação está ativo
            if args.simulate_chat:
                agent.simulate_mode = True
                print(f"🎭 Modo simulação ativado para input único")
            response = agent.chat(enhanced_input, debug_save_input=debug_mode)
            print("\n📄 Response:")
            print("=" * 60)
            print(response)
            print("=" * 60)
            agent.save_agent_state_v2()
            logger.info("Agent state saved after processing input")
        except Exception as e:
            print(f"\n❌ Error processing input: {e}")
            logger.error(f"Error processing input: {e}")
    else:
        print("\n💡 Tip: Use --repl for interactive mode or --input for single message")
        print("🤖 Meta-agent ready for programmatic use")
        logger.info("Admin Agent ready for programmatic use")
    print("\n👋 Admin Executor session completed")
    logger.info("Admin Executor session completed")

if __name__ == "__main__":
    import json
    from datetime import datetime
    main()