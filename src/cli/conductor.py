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

def run_agent_command(args):
    """Lógica para executar o fluxo do 'agent'."""
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