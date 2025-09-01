"""
Debug Utilities - Shared Debug and Information Functions

Provides debugging and information display functionality for CLI interfaces.
"""

import os
from datetime import datetime
from typing import Any


class DebugUtilities:
    """Provides debug and information utilities for CLI applications."""
    
    def __init__(self, cli_instance: Any, logger: Any):
        """
        Initialize debug utilities.
        
        Args:
            cli_instance: CLI instance
            logger: Logger instance
        """
        self.cli_instance = cli_instance
        self.logger = logger
    
    def save_debug_input(self, message: str, debug_dir: str = "/tmp/admin_debug") -> str:
        """
        Save debug input to file for analysis.
        
        Args:
            message: Message to save
            debug_dir: Directory to save debug files
            
        Returns:
            Path to saved debug file
        """
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = f"{debug_dir}/input_final_{timestamp}.txt"
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write("=== DEBUG: INPUT COMPLETO PARA PROVIDER ===\n\n")
            f.write(f"Enhanced Input: {message}\n\n")
            f.write(f"Agent ID: {self.cli_instance.agent_logic.get_current_agent()}\n")
            f.write(f"Embodied: {self.cli_instance.embodied}\n")
            f.write(f"Available Tools: {self.cli_instance.get_available_tools()}\n")
            
            # Add simulation mode info if available
            if hasattr(self.cli_instance, 'simulate_mode'):
                f.write(f"Simulation Mode: {self.cli_instance.simulate_mode}\n")
            
            # Add conversation history if available
            if hasattr(self.cli_instance.agent_logic.llm_client, 'conversation_history'):
                history = self.cli_instance.agent_logic.llm_client.conversation_history
                f.write(f"\nConversation History ({len(history)} messages):\n")
                for i, msg in enumerate(history, 1):
                    f.write(f"\n--- Message {i} ---\n")
                    f.write(f"Prompt: {msg.get('prompt', 'N/A')[:500]}\n")
                    f.write(f"Response: {msg.get('response', 'N/A')[:500]}\n")
        
        self.logger.info(f"DEBUG: Input completo salvo em {debug_file}")
        print(f"🔍 DEBUG: Contexto completo salvo em {debug_file}")
        return debug_file
    
    def generate_simulation_response(self, message: str) -> str:
        """
        Generate simulated response for testing.
        
        Args:
            message: Input message
            
        Returns:
            Simulated response string
        """
        # Add to conversation history to maintain context
        if hasattr(self.cli_instance.agent_logic.llm_client, 'conversation_history'):
            import time
            self.cli_instance.agent_logic.llm_client.conversation_history.append({
                'prompt': message,
                'response': f"[SIMULATED] Resposta simulada para: {message}",
                'timestamp': time.time()
            })
            
            # Save state automatically
            try:
                self.cli_instance.agent_logic.save_agent_state()
                self.logger.debug("State saved automatically in simulation mode")
            except Exception as save_error:
                self.logger.warning(f"Failed to save state in simulation mode: {save_error}")
        
        agent_name = self.cli_instance.agent_logic.get_current_agent() or 'Unknown_Agent'
        
        return f"""🎭 [MODO SIMULAÇÃO] 

Olá! Sou o {agent_name} em modo simulação.

Recebi sua mensagem: "{message}"

Esta é uma resposta simulada que não chama o provider real. O contexto da conversa está sendo mantido para que você possa usar o comando 'debug' para ver todo o histórico acumulado.

Para ver o contexto completo, digite 'debug' no REPL.

---
💡 Dica: Use 'debug' para ver todo o contexto que seria enviado ao provider
📊 Use 'history' para ver o histórico de conversas simuladas
"""
    
    def show_comprehensive_debug_info(self):
        """Show comprehensive debug information."""
        print("\n🔍 === DEBUG: INFORMAÇÕES COMPLETAS ===")
        
        # Basic agent info
        print(f"🆔 Agent ID: {self.cli_instance.agent_logic.get_current_agent()}")
        print(f"✅ Embodied: {self.cli_instance.embodied}")
        print(f"🔧 Available Tools: {self.cli_instance.get_available_tools()}")
        
        # Environment info if available
        if hasattr(self.cli_instance.agent_logic, 'environment'):
            print(f"🌐 Environment: {self.cli_instance.agent_logic.environment}")
        if hasattr(self.cli_instance.agent_logic, 'project'):
            print(f"📦 Project: {self.cli_instance.agent_logic.project}")
        
        print(f"📂 Working Dir: {self.cli_instance.agent_logic.working_directory}")
        
        # CLI-specific info
        if hasattr(self.cli_instance, 'simulate_mode'):
            print(f"🎭 Simulation Mode: {self.cli_instance.simulate_mode}")
        if hasattr(self.cli_instance, 'destination_path'):
            print(f"📍 Destination Path: {self.cli_instance.destination_path}")
        
        # Output scope info
        if hasattr(self.cli_instance, 'get_output_scope'):
            scope = self.cli_instance.get_output_scope()
            print(f"🎯 Output Scope: {scope if scope else 'No restrictions'}")
        
        # Conversation history summary
        if hasattr(self.cli_instance.agent_logic.llm_client, 'conversation_history'):
            history = self.cli_instance.agent_logic.llm_client.conversation_history
            print(f"💬 Conversation History: {len(history)} messages")
        
        print("=" * 60)
    
    def export_debug_report(self, output_path: str = None) -> str:
        """
        Export comprehensive debug report to file.
        
        Args:
            output_path: Optional output path, defaults to timestamp-based
            
        Returns:
            Path to exported report
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/tmp/debug_report_{timestamp}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=== COMPREHENSIVE DEBUG REPORT ===\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            
            # Agent information
            f.write("AGENT INFORMATION:\n")
            f.write(f"- ID: {self.cli_instance.agent_logic.get_current_agent()}\n")
            f.write(f"- Embodied: {self.cli_instance.embodied}\n")
            f.write(f"- Working Directory: {self.cli_instance.agent_logic.working_directory}\n")
            
            if hasattr(self.cli_instance.agent_logic, 'environment'):
                f.write(f"- Environment: {self.cli_instance.agent_logic.environment}\n")
            if hasattr(self.cli_instance.agent_logic, 'project'):
                f.write(f"- Project: {self.cli_instance.agent_logic.project}\n")
            
            # Tools and capabilities
            f.write(f"\nAVAILABLE TOOLS:\n")
            for tool in self.cli_instance.get_available_tools():
                f.write(f"- {tool}\n")
            
            # Output scope
            if hasattr(self.cli_instance, 'get_output_scope'):
                scope = self.cli_instance.get_output_scope()
                f.write(f"\nOUTPUT SCOPE:\n")
                if scope:
                    for path in scope:
                        f.write(f"- {path}\n")
                else:
                    f.write("- No restrictions\n")
            
            # Conversation history
            if hasattr(self.cli_instance.agent_logic.llm_client, 'conversation_history'):
                history = self.cli_instance.agent_logic.llm_client.conversation_history
                f.write(f"\nCONVERSATION HISTORY ({len(history)} messages):\n")
                for i, msg in enumerate(history, 1):
                    f.write(f"\n--- Message {i} ---\n")
                    f.write(f"Prompt: {msg.get('prompt', 'N/A')}\n")
                    f.write(f"Response: {msg.get('response', 'N/A')[:1000]}{'...' if len(msg.get('response', '')) > 1000 else ''}\n")
        
        self.logger.info(f"Debug report exported to: {output_path}")
        print(f"📊 Debug report exported to: {output_path}")
        return output_path