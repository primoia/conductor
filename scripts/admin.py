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
from genesis_agent import GenesisAgent, Toolbelt

# Configure admin logging
def setup_admin_logging(debug_mode: bool = False):
    """Setup logging for admin executor."""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create admin logger
    admin_logger = logging.getLogger('admin_executor')
    admin_logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers to avoid duplicates
    admin_logger.handlers.clear()
    
    # File handler (always logs everything)
    log_file = logs_dir / f"admin_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler (only if debug mode)
    if debug_mode:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        admin_logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    admin_logger.propagate = False
    
    # Detailed file format
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    admin_logger.addHandler(file_handler)
    
    return admin_logger


class AdminAgent:
    """
    Admin Agent class for executing meta-agents that manage the framework.
    
    This class is responsible for loading and executing meta-agents
    that don't require project context.
    """
    
    def __init__(self, agent_id: str = None, ai_provider: str = None, logger = None):
        """
        Initialize the Admin Agent for meta-agent execution.
        
        Args:
            agent_id: ID do meta-agente para embodiment
            ai_provider: AI provider override
            logger: Logger instance for this agent
        """
        # Load AI providers configuration
        self.ai_providers_config = load_ai_providers_config()
        self.ai_provider_override = ai_provider
        self.logger = logger or logging.getLogger('admin_executor')
        
        # Agent state
        self.current_agent = None
        self.embodied = False
        self.agent_config = None
        self.agent_home_path = None
        self.working_directory = None
        self.llm_client = None
        
        # Save original CWD
        self.original_cwd = os.getcwd()
        
        # Meta-agents don't have environment/project context
        self.environment = None
        self.project = None
        
        # Initialize if agent_id is provided
        if agent_id:
            self.embody_meta_agent(agent_id)
    
    def embody_meta_agent(self, agent_id: str) -> bool:
        """
        Embody a meta-agent for framework management.
        
        Args:
            agent_id: ID do meta-agente para embodiment
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        try:
            # Meta-agents are always in _common, no environment/project needed
            self.agent_home_path, _ = resolve_agent_paths("_common", "_common", agent_id)
            
            # Load agent configuration
            self.agent_config = load_agent_config_v2(self.agent_home_path)
            
            # Validate configuration
            validate_agent_config(self.agent_config)
            
            # Initialize LLM client with chat provider
            chat_provider = self.get_chat_provider()
            self.llm_client = create_llm_client(chat_provider, str(Path.cwd()))
            
            # Pass reference to this agent for tool access
            self.llm_client.genesis_agent = self
            
            # Initialize toolbelt with available tools
            self.toolbelt = Toolbelt(str(Path.cwd()), genesis_agent=self)
            
            # Configure available tools from agent config if specified
            if 'available_tools' in self.agent_config:
                # The toolbelt will automatically filter available tools
                pass
            
            # Meta-agents work in the current directory (framework root)
            self.working_directory = str(Path.cwd())
            
            # Load agent state if available
            state_file_path = self.agent_home_path / self.agent_config.get("state_file_path", "state.json")
            self._load_agent_state(str(state_file_path))
            
            # Load agent persona
            persona_path = self.agent_home_path / self.agent_config.get("persona_prompt_path", "persona.md")
            if not self._load_agent_persona(str(persona_path), agent_id):
                return False
            
            # Save state file path
            self.state_file_path = str(state_file_path)
            
            # Mark agent as embodied
            self.current_agent = agent_id
            self.embodied = True
            
            print(f"✅ Successfully embodied meta-agent: {agent_id}")
            self.logger.info(f"Embodied meta-agent: {agent_id}")
            self.logger.debug(f"Agent home: {self.agent_home_path}")
            self.logger.debug(f"Working directory: {self.working_directory}")
            self.logger.debug(f"State file: {self.state_file_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to embody meta-agent {agent_id}: {e}")
            return False
    
    def get_chat_provider(self) -> str:
        """Get chat provider for meta-agent."""
        if self.ai_provider_override:
            return self.ai_provider_override
        
        # Use default provider from config or fallback
        return self.ai_providers_config.get('default_provider', 'claude')
    
    def get_generation_provider(self) -> str:
        """Get generation provider for meta-agent."""
        if self.ai_provider_override:
            return self.ai_provider_override
        
        # Use generation provider from config or fallback to claude
        return self.ai_providers_config.get('generation_provider', 'claude')
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names from agent config."""
        if not self.agent_config:
            return []
        return self.agent_config.get('available_tools', [])
    
    def _load_agent_state(self, state_file_path: str):
        """Load agent state from file."""
        try:
            if os.path.exists(state_file_path):
                with open(state_file_path, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                # Load conversation history if available
                if 'conversation_history' in state_data and isinstance(state_data['conversation_history'], list):
                    self.llm_client.conversation_history = state_data['conversation_history']
                    print(f"📚 Loaded conversation history: {len(self.llm_client.conversation_history)} messages")
                    self.logger.info(f"Loaded {len(self.llm_client.conversation_history)} messages from conversation history")
                else:
                    self.llm_client.conversation_history = []
                    self.logger.debug("No conversation history found in state, starting fresh")
            else:
                self.llm_client.conversation_history = []
                self.logger.debug("No state file found, starting fresh")
        except Exception as e:
            print(f"⚠️  Warning: Could not load agent state: {e}")
            self.logger.warning(f"Could not load agent state from {state_file_path}: {e}")
            self.llm_client.conversation_history = []
    
    def _load_agent_persona(self, persona_path: str, agent_id: str) -> bool:
        """Load agent persona from file."""
        try:
            if not os.path.exists(persona_path):
                print(f"⚠️  Warning: Persona file not found: {persona_path}")
                return True  # Not critical for meta-agents
            
            with open(persona_path, 'r', encoding='utf-8') as f:
                persona_content = f.read()
            
            # Set persona in LLM client
            self.llm_client.set_agent_persona(persona_content)
            print(f"🎭 Loaded persona for {agent_id}")
            self.logger.info(f"Loaded persona for {agent_id} from {persona_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load persona: {e}")
            self.logger.error(f"Failed to load persona from {persona_path}: {e}")
            return False
    
    def chat(self, message: str) -> str:
        """Send a message to the meta-agent."""
        if not self.embodied:
            return "❌ No agent embodied. Use embody_meta_agent() first."
        
        try:
            self.logger.info(f"Processing chat message: {message[:100]}...")
            # Use the correct method to invoke the LLM with native tool support
            response = self.llm_client._invoke_subprocess(message)
            self.logger.info(f"Chat response received: {len(response) if response else 0} chars")
            return response
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            return f"❌ Error in chat: {e}"
    
    def generate_artifact(self, prompt: str) -> str:
        """Generate an artifact using the generation provider with fallback."""
        if not self.embodied:
            return "❌ No agent embodied. Use embody_meta_agent() first."
        
        # First try: Use configured generation provider
        generation_provider = self.get_generation_provider()
        
        try:
            generation_client = create_llm_client(generation_provider, self.working_directory)
            generation_client.genesis_agent = self  # Pass reference for tools
            
            response = generation_client.generate_artifact(prompt)
            return response
            
        except Exception as e:
            self.logger.warning(f"Generation provider {generation_provider} failed: {e}")
            print(f"⚠️  Generation provider {generation_provider} failed: {e}")
            
            # Fallback: Try Claude if original wasn't Claude
            if generation_provider != 'claude':
                try:
                    self.logger.info(f"Falling back to Claude from {generation_provider}")
                    print(f"🔄 Falling back to Claude...")
                    fallback_client = create_llm_client('claude', self.working_directory)
                    fallback_client.genesis_agent = self  # Pass reference for tools
                    
                    response = fallback_client.generate_artifact(prompt)
                    self.logger.info("Fallback to Claude succeeded")
                    return response
                    
                except Exception as fallback_error:
                    self.logger.error(f"Both {generation_provider} and Claude failed. Original: {e}, Fallback: {fallback_error}")
                    return f"❌ Both {generation_provider} and Claude failed. {generation_provider}: {e}, Claude: {fallback_error}"
            else:
                self.logger.error(f"Claude generation failed: {e}")
                return f"❌ Error generating artifact with {generation_provider}: {e}"
    
    def save_agent_state_v2(self):
        """Save agent state to file."""
        if not self.embodied or not hasattr(self, 'state_file_path'):
            print("⚠️  No agent state to save")
            return
        
        try:
            state_data = {
                'agent_id': self.current_agent,
                'timestamp': datetime.now().isoformat(),
                'conversation_history': self.llm_client.conversation_history if self.llm_client else []
            }
            
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            # State saved silently
        except Exception as e:
            print(f"❌ Failed to save state: {e}")
    
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
    python scripts/admin.py --agent migrate_agents_v2
        """
    )
    
    # Admin-specific arguments
    parser.add_argument('--agent', type=str, required=True,
                        help='Meta-agent ID to embody (required)')
    
    # Common arguments
    parser.add_argument('--ai-provider', type=str, default=None, 
                        choices=['claude', 'gemini'], 
                        help='AI provider override (uses dual provider system by default)')
    parser.add_argument('--repl', action='store_true', 
                        help='Start interactive REPL')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode (shows logs in console)')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_admin_logging(debug_mode=args.debug)
    
    # Initialize Admin Agent
    try:
        print(f"🚀 Iniciando Admin Executor")
        print(f"   Meta-agent: {args.agent}")
        if args.debug:
            print(f"   Debug mode: enabled")
            print(f"   Logs: logs/admin_{datetime.now().strftime('%Y%m%d')}.log")
        
        logger.info(f"Starting Admin Executor for meta-agent: {args.agent}")
        logger.debug(f"AI provider override: {args.ai_provider}")
        logger.debug(f"Debug mode: {args.debug}")
        
        agent = AdminAgent(
            agent_id=args.agent,
            ai_provider=args.ai_provider,
            logger=logger
        )
        
        if not agent.embodied:
            print(f"❌ Failed to embody meta-agent: {args.agent}")
            logger.error(f"Failed to embody meta-agent: {args.agent}")
            exit(1)
        
        print(f"🔓 No output restrictions (meta-agent)")
        logger.info("Admin Agent successfully initialized")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        logger.error(f"Admin Agent initialization failed: {e}")
        exit(1)
    
    # Start REPL if requested
    if args.repl:
        logger.info("Starting REPL session")
        start_repl_session(agent, "admin")
        logger.info("REPL session completed")
    else:
        print("\n💡 Tip: Use --repl for interactive mode")
        print("🤖 Meta-agent ready for programmatic use")
        logger.info("Admin Agent ready for programmatic use")
    
    print("\n👋 Admin Executor session completed")
    logger.info("Admin Executor session completed")


if __name__ == "__main__":
    import json
    from datetime import datetime
    main()
