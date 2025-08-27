#!/usr/bin/env python3
"""
Agent CLI - Interactive Agent Embodiment Interface

This script provides a command-line interface for interacting with agents using
the core GenesisAgent class. It handles project agent execution and embodiment.

This script is focused exclusively on project agents that require environment/project context.
For meta-agents that manage the framework itself, use admin.py instead.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Import core functionality
from core import GenesisAgent
from agent_common import start_repl_session


def main():
    """Main function for agent.py CLI."""
    parser = argparse.ArgumentParser(
        description='Agent CLI - Project Agent Executor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/agent.py --environment develop --project nex-web-backend --agent KotlinEntityCreator_Agent --repl
    python scripts/agent.py --environment develop --project nex-web-backend --agent ProblemRefiner_Agent

Note: For meta-agents that manage the framework itself, use admin.py instead:
    python scripts/admin.py --agent AgentCreator_Agent --repl
        """
    )
    
    # Required Arguments
    parser.add_argument('--environment', type=str, required=True,
                        help='Environment name (develop, main, etc.) - Required')
    parser.add_argument('--project', type=str, required=True,
                        help='Project name - Required')
    parser.add_argument('--agent', type=str, required=True,
                        help='Agent ID to embody - Required')
    
    # Optional Arguments
    parser.add_argument('--ai-provider', type=str, default=None, choices=['claude', 'gemini'], 
                        help='AI provider override (uses dual provider system by default)')
    parser.add_argument('--repl', action='store_true', 
                        help='Start interactive REPL')
    parser.add_argument('--input', type=str, default=None,
                        help='Input message to send to agent (non-interactive mode)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode (shows logs in console)')
    parser.add_argument('--timeout', type=int, default=120,
                        help='Timeout in seconds for Claude CLI operations (default: 120)')
    
    args = parser.parse_args()
    
    # Setup basic logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    # Initialize Genesis Agent
    try:
        print(f"🚀 Iniciando Agent CLI")
        print(f"   Environment: {args.environment}")
        print(f"   Project: {args.project}")
        print(f"   Agent: {args.agent}")
        if args.debug:
            print(f"   Debug mode: enabled")
            print(f"   Logs: logs/genesis_{datetime.now().strftime('%Y%m%d')}.log")
        
        logger.info(f"Starting Agent CLI for {args.environment}/{args.project}/{args.agent}")
        
        agent = GenesisAgent(
            environment=args.environment,
            project=args.project,
            agent_id=args.agent,
            ai_provider=args.ai_provider,
            timeout=args.timeout
        )
        
        logger.info("GenesisAgent initialized successfully")
        
        # Embody agent
        print(f"🤖 Embodying agent: {args.agent}")
        logger.info(f"Attempting to embody agent: {args.agent}")
        
        if agent.embody_agent_v2(args.agent):
            print(f"✅ Successfully embodied {args.agent} in {args.environment}/{args.project}")
            print(f"📂 Working directory: {agent.working_directory}")
            if hasattr(agent, 'output_scope') and agent.output_scope:
                print(f"🔒 Output scope: {agent.output_scope}")
            else:
                print(f"🔓 No output restrictions")
            
            logger.info(f"Successfully embodied agent: {args.agent}")
        else:
            print(f"❌ Failed to embody {args.agent}")
            logger.error(f"Failed to embody agent: {args.agent}")
            exit(1)

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        logger.error(f"Agent CLI initialization failed: {e}")
        exit(1)
    
    # Start REPL if requested
    if args.repl:
        logger.info("Starting REPL session")
        start_repl_session(agent, "agent")
        logger.info("REPL session completed")
    
    # Process input if provided (non-interactive mode)
    elif args.input and agent.embodied:
        logger.info(f"Processing input message: {args.input[:100]}...")
        print(f"\n🤖 Processing input for {args.agent}:")
        print(f"📝 Input: {args.input}")
        print("-" * 60)
        
        try:
            # Determine if this is a generation task
            generation_commands = ['gerar documento', 'preview', 'consolidar', 'criar artefato', 'salvar documento', 'documento', 'documentacao', 'gere']
            is_generation_task = any(cmd in args.input.lower() for cmd in generation_commands)
            
            # Always enhance input with automatic persona instructions
            enhanced_input = f"""IMPORTANTE: Leia atentamente o persona.md e agent.yaml do agente e siga EXATAMENTE as diretrizes definidas nesses arquivos.

{args.input}

Lembre-se: Você DEVE seguir a estrutura e formato especificados no persona, não crie formatos alternativos."""
            logger.info("Enhanced input with automatic persona instructions")
            
            if is_generation_task:
                print(f"🏗️  Using generation provider for artifact creation...")
                logger.info("Using generation provider for artifact creation")
                response = agent.generate_artifact(enhanced_input)
            else:
                print(f"💬 Using chat provider for conversation...")
                logger.info("Using chat provider for conversation")
                response = agent.chat(enhanced_input)
            
            print("\n📄 Response:")
            print("=" * 60)
            print(response)
            print("=" * 60)
            
            # Save state after processing
            if hasattr(agent, 'save_agent_state_v2'):
                agent.save_agent_state_v2()
                logger.info("Agent state saved after processing input")
            
        except Exception as e:
            print(f"\n❌ Error processing input: {e}")
            logger.error(f"Error processing input: {e}")
    
    # If not REPL mode and no input, just show ready message
    elif not args.repl and agent.embodied:
        print("\n💡 Tip: Use --repl for interactive mode or --input for single message")
        print("🤖 Agent ready for programmatic use")
        logger.info("Agent ready for programmatic use")
    
    print("\n👋 Agent CLI session completed")
    logger.info("Agent CLI session completed")


if __name__ == "__main__":
    main()