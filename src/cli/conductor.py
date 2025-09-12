#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cli.shared import CLIArgumentParser
from src.container import container
from src.core.domain import TaskDTO

def main():
    """Ponto de entrada unificado para o Conductor CLI."""
    parser = CLIArgumentParser.create_main_parser()
    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)
    
    # Executar a função associada ao subcomando
    args.func(args)

def list_agents_command(args):
    """Lista todos os agentes disponíveis."""
    print("🤖 Agentes disponíveis em .conductor_workspace/agents/:")
    print("=" * 60)
    
    try:
        conductor_service = container.get_conductor_service()
        agents = conductor_service.discover_agents()
        
        if not agents:
            print("❌ Nenhum agente encontrado.")
            print("💡 Verifique se há agentes em .conductor_workspace/agents/")
            return
        
        for i, agent in enumerate(agents, 1):
            print(f"{i:2d}. {agent.agent_id}")
            if hasattr(agent, 'name') and agent.name:
                print(f"     Nome: {agent.name}")
            if hasattr(agent, 'capabilities') and agent.capabilities:
                print(f"     Capacidades: {', '.join(agent.capabilities[:3])}{'...' if len(agent.capabilities) > 3 else ''}")
            if hasattr(agent, 'tags') and agent.tags:
                print(f"     Tags: {', '.join(agent.tags[:3])}{'...' if len(agent.tags) > 3 else ''}")
            print()
        
        print(f"📊 Total: {len(agents)} agentes encontrados")
        print("\n💡 Para executar um agente:")
        print("   conductor execute --agent <agent_id> --input '<mensagem>'")
        
    except Exception as e:
        print(f"❌ Erro ao listar agentes: {e}")
        print("💡 Verifique se o diretório .conductor_workspace/agents/ existe")

def run_admin_command(args):
    """Lógica para executar o fluxo do 'admin'."""
    print("Executando fluxo 'admin'...")
    service = container.conductor_service()
    task = TaskDTO(
        agent_id=args.agent,
        user_input=args.input or "", # Lidar com caso de REPL
        context={
            "meta": True, 
            "new_agent_id": args.new_agent_id
        }
    )
    # Aqui a lógica completa de REPL vs. input único seria chamada
    result = service.execute_task(task)
    print(result.output)

def execute_agent_command(args):
    """Executa um agente com a mensagem fornecida."""
    print(f"🤖 Executando agente: {args.agent}")
    print("=" * 50)
    
    try:
        conductor_service = container.get_conductor_service()
        
        # Verificar se o agente existe primeiro
        agent_service = container.get_agent_discovery_service()
        if not agent_service.agent_exists(args.agent):
            suggestions = agent_service.get_similar_agent_names(args.agent)
            print(f"❌ Agente '{args.agent}' não encontrado em .conductor_workspace/agents/")
            if suggestions:
                print(f"💡 Agentes similares disponíveis: {', '.join(suggestions)}")
            print("📋 Use 'conductor list-agents' para ver todos os agentes disponíveis")
            return
        
        # Construir contexto da tarefa
        context = {}
        if args.environment:
            context["environment"] = args.environment
        if args.project:
            context["project"] = args.project
        
        # Criar e executar tarefa
        task = TaskDTO(
            agent_id=args.agent,
            user_input=args.input,
            context=context
        )
        
        result = conductor_service.execute_task(task)
        
        if result.status == "success":
            print("✅ Execução bem-sucedida:")
            print(result.output)
        else:
            print("❌ Erro na execução:")
            print(result.output)
            
    except Exception as e:
        print(f"❌ Erro fatal: {e}")

def validate_config_command(args):
    """Valida a configuração atual do Conductor."""
    print("🔍 Validando configuração do Conductor...")
    print("=" * 50)
    
    try:
        config_service = container.get_configuration_service()
        config = config_service.get_global_config()
        
        print("✅ Configuração carregada com sucesso:")
        print(f"   Storage Type: {config.storage.type}")
        print(f"   Storage Path: {config.storage.path}")
        print(f"   Tool Plugins: {len(config.tool_plugins)} configurados")
        
        # Verificar se o diretório de agentes existe
        import os
        agents_dir = os.path.join(config.storage.path, "agents")
        if os.path.exists(agents_dir):
            agent_count = len([d for d in os.listdir(agents_dir) if os.path.isdir(os.path.join(agents_dir, d))])
            print(f"   Agentes encontrados: {agent_count}")
        else:
            print(f"   ⚠️  Diretório de agentes não existe: {agents_dir}")
        
        print("\n🎯 Configuração válida!")
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")

def run_agent_command(args):
    """Lógica para executar o fluxo do 'agent' (legacy)."""
    print("Executando fluxo 'agent'...")
    service = container.conductor_service()
    task = TaskDTO(
        agent_id=args.agent,
        user_input=args.input or "",
        context={
            "environment": args.environment,
            "project": args.project
        }
    )
    result = service.execute_task(task)
    print(result.output)

if __name__ == "__main__":
    main()