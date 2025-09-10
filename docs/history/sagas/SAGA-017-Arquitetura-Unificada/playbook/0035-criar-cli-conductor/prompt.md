# Especificação Técnica e Plano de Execução: 0035-criar-cli-conductor

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação. Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa cria a interface de comando unificada e definitiva para o sistema. Um único CLI (`conductor`) melhora a experiência do usuário, simplifica a documentação e estabelece a base para todos os futuros comandos e interações com a plataforma.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** O novo CLI **DEVE** ser criado em `src/cli/conductor.py`.
- **Retrocompatibilidade:** O novo CLI **DEVE** suportar os mesmos argumentos e funcionalidades dos CLIs `admin.py` e `agent.py` através de subparsers.
- **Uso de Componentes Compartilhados:** O script **DEVE** reutilizar os componentes de parsing de argumentos já definidos em `src/cli/shared/` para evitar duplicação de código.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo. O conteúdo **DEVE** ser exatamente como especificado abaixo, utilizando os parsers já existentes.

**Arquivo 1 (Novo): `src/cli/conductor.py`**
```python
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
```
*Nota: A implementação acima é simplificada. A lógica real precisaria ser adaptada para reutilizar o `REPLManager` e o fluxo completo dos scripts `admin.py` e `agent.py` refatorados, mas agora invocados a partir daqui.*

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `src/cli/conductor.py` for criado, definindo o parser principal e os subparsers `admin` e `agent`, e for capaz de invocar a lógica de serviço correspondente.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
