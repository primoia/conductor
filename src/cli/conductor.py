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
        if hasattr(args, 'project_path') and args.project_path:
            context["project_path"] = args.project_path
        if hasattr(args, 'timeout') and args.timeout:
            context["timeout"] = args.timeout
        
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
    """Valida a configuração atual do Conductor com verificações detalhadas."""
    from src.core.constants import Messages, Paths
    
    print("🔍 Validando configuração do Conductor...")
    print("=" * 60)
    
    validation_errors = []
    validation_warnings = []
    
    try:
        # 1. Validar carregamento da configuração
        print("📋 1. Validando arquivo de configuração...")
        config_service = container.get_configuration_service()
        config = config_service.get_global_config()
        print("   ✅ config.yaml carregado com sucesso")
        
        # 2. Validar configuração de storage
        print("\n💾 2. Validando configuração de storage...")
        print(f"   Tipo: {config.storage.type}")
        print(f"   Caminho: {config.storage.path}")
        
        import os
        
        # Verificar se o diretório base existe
        if not os.path.exists(config.storage.path):
            validation_errors.append(f"Diretório de storage não existe: {config.storage.path}")
            print(f"   ❌ Diretório base não existe: {config.storage.path}")
        else:
            print(f"   ✅ Diretório base existe")
            
            # Verificar permissões de escrita
            if not os.access(config.storage.path, os.W_OK):
                validation_errors.append(f"Sem permissão de escrita em: {config.storage.path}")
                print(f"   ❌ Sem permissão de escrita")
            else:
                print(f"   ✅ Permissões de escrita OK")
        
        # 3. Validar diretório de agentes
        print("\n🤖 3. Validando diretório de agentes...")
        agents_dir = os.path.join(config.storage.path, Paths.AGENTS_DIR)
        
        if not os.path.exists(agents_dir):
            validation_warnings.append(f"Diretório de agentes não existe: {agents_dir}")
            print(f"   ⚠️  Diretório não existe: {agents_dir}")
            print(f"   💡 Será criado automaticamente quando necessário")
        else:
            print(f"   ✅ Diretório existe: {agents_dir}")
            
            # Contar e validar agentes
            agent_dirs = [d for d in os.listdir(agents_dir) if os.path.isdir(os.path.join(agents_dir, d))]
            print(f"   📊 Agentes encontrados: {len(agent_dirs)}")
            
            if agent_dirs:
                print("\n   🔍 Validando estrutura dos agentes...")
                valid_agents = 0
                
                for agent_id in agent_dirs[:5]:  # Validar apenas os primeiros 5 para não ser muito verboso
                    agent_path = os.path.join(agents_dir, agent_id)
                    definition_file = os.path.join(agent_path, Paths.DEFINITION_FILE)
                    
                    if os.path.exists(definition_file):
                        try:
                            # Tentar carregar e validar definition.yaml
                            import yaml
                            with open(definition_file, 'r', encoding='utf-8') as f:
                                definition = yaml.safe_load(f)
                            
                            # Verificar campos obrigatórios
                            required_fields = ['name', 'version', 'description']
                            missing_fields = [field for field in required_fields if field not in definition]
                            
                            if missing_fields:
                                validation_warnings.append(f"Agente {agent_id}: campos obrigatórios ausentes: {missing_fields}")
                                print(f"   ⚠️  {agent_id}: campos ausentes: {missing_fields}")
                            else:
                                valid_agents += 1
                                print(f"   ✅ {agent_id}: estrutura válida")
                                
                        except Exception as e:
                            validation_errors.append(f"Agente {agent_id}: erro ao validar definition.yaml: {e}")
                            print(f"   ❌ {agent_id}: erro na definição: {e}")
                    else:
                        validation_errors.append(f"Agente {agent_id}: definition.yaml não encontrado")
                        print(f"   ❌ {agent_id}: definition.yaml ausente")
                
                if len(agent_dirs) > 5:
                    print(f"   ... (validação completa de {len(agent_dirs) - 5} agentes restantes omitida)")
                
                print(f"   📊 Agentes válidos: {valid_agents}/{len(agent_dirs)}")
        
        # 4. Validar plugins de ferramentas
        print("\n🔧 4. Validando plugins de ferramentas...")
        if config.tool_plugins:
            print(f"   📊 Plugins configurados: {len(config.tool_plugins)}")
            for plugin_dir in config.tool_plugins:
                if os.path.exists(plugin_dir):
                    print(f"   ✅ {plugin_dir}: existe")
                else:
                    validation_warnings.append(f"Diretório de plugin não existe: {plugin_dir}")
                    print(f"   ⚠️  {plugin_dir}: não existe")
        else:
            print("   📊 Nenhum plugin configurado")
        
        # 5. Testar descoberta de agentes
        print("\n🔍 5. Testando descoberta de agentes...")
        try:
            conductor_service = container.get_conductor_service()
            agents = conductor_service.discover_agents()
            print(f"   ✅ Descoberta funcionando: {len(agents)} agentes descobertos")
        except Exception as e:
            validation_errors.append(f"Erro na descoberta de agentes: {e}")
            print(f"   ❌ Erro na descoberta: {e}")
        
        # 6. Resumo final
        print("\n" + "=" * 60)
        print("📊 RESUMO DA VALIDAÇÃO")
        
        if validation_errors:
            print(f"❌ Erros encontrados: {len(validation_errors)}")
            for error in validation_errors:
                print(f"   • {error}")
        
        if validation_warnings:
            print(f"⚠️  Avisos: {len(validation_warnings)}")
            for warning in validation_warnings:
                print(f"   • {warning}")
        
        if not validation_errors and not validation_warnings:
            print("✅ Configuração totalmente válida!")
        elif not validation_errors:
            print("✅ Configuração válida com avisos menores")
        else:
            print("❌ Configuração com problemas que precisam ser corrigidos")
            return 1  # Exit code para indicar erro
        
        print(f"\n💡 Para mais informações sobre um agente específico:")
        print(f"   conductor info --agent <agent_id>")
        
    except Exception as e:
        print(f"❌ Erro crítico na validação: {e}")
        return 1

def info_agent_command(args):
    """Mostra informações detalhadas sobre um agente específico."""
    from src.core.constants import Messages, Paths
    
    print(f"🔍 Informações do agente: {args.agent}")
    print("=" * 60)
    
    try:
        agent_service = container.get_agent_discovery_service()
        
        # Verificar se o agente existe
        if not agent_service.agent_exists(args.agent):
            suggestions = agent_service.get_similar_agent_names(args.agent)
            location = f"{Paths.WORKSPACE_ROOT}/{Paths.AGENTS_DIR}/"
            print(Messages.AGENT_NOT_FOUND.format(agent_id=args.agent, location=location))
            if suggestions:
                print(Messages.SUGGEST_SIMILAR.format(suggestions=', '.join(suggestions)))
            print(Messages.USE_LIST_COMMAND)
            return
        
        # Carregar definição do agente
        agent_definition = agent_service.get_agent_definition(args.agent)
        
        if not agent_definition:
            print(f"❌ Erro ao carregar definição do agente {args.agent}")
            return
        
        # Informações básicas
        print("📋 INFORMAÇÕES BÁSICAS")
        print(f"   ID: {args.agent}")
        print(f"   Nome: {agent_definition.name}")
        print(f"   Versão: {agent_definition.version}")
        print(f"   Autor: {agent_definition.author}")
        print(f"   Descrição: {agent_definition.description}")
        
        # Tags
        if agent_definition.tags:
            print(f"\n🏷️  TAGS")
            for tag in agent_definition.tags:
                print(f"   • {tag}")
        
        # Capacidades
        if agent_definition.capabilities:
            print(f"\n🛠️  CAPACIDADES")
            for capability in agent_definition.capabilities:
                print(f"   • {capability}")
        
        # Ferramentas permitidas
        if agent_definition.allowed_tools:
            print(f"\n🔧 FERRAMENTAS PERMITIDAS")
            for tool in agent_definition.allowed_tools:
                print(f"   • {tool}")
        
        # Verificar arquivos do agente
        storage_service = container.get_storage_service()
        repository = storage_service.get_repository()
        agent_home = repository.get_agent_home_path(args.agent)
        
        print(f"\n📁 ARQUIVOS DO AGENTE")
        print(f"   Localização: {agent_home}")
        
        import os
        files_status = []
        for file_name in [Paths.DEFINITION_FILE, Paths.PERSONA_FILE, Paths.SESSION_FILE, 
                         Paths.KNOWLEDGE_FILE, Paths.HISTORY_FILE, Paths.PLAYBOOK_FILE]:
            file_path = os.path.join(agent_home, file_name)
            status = "✅" if os.path.exists(file_path) else "❌"
            size = ""
            if os.path.exists(file_path):
                try:
                    size_bytes = os.path.getsize(file_path)
                    if size_bytes < 1024:
                        size = f" ({size_bytes}B)"
                    elif size_bytes < 1024 * 1024:
                        size = f" ({size_bytes // 1024}KB)"
                    else:
                        size = f" ({size_bytes // (1024 * 1024)}MB)"
                except:
                    size = ""
            files_status.append(f"   {status} {file_name}{size}")
        
        for status in files_status:
            print(status)
        
        # Estatísticas do histórico
        try:
            history = agent_service.get_conversation_history(args.agent)
            print(f"\n📊 ESTATÍSTICAS")
            print(f"   Conversas no histórico: {len(history)}")
            
            if history:
                # Última interação
                last_interaction = max(history, key=lambda x: x.get('timestamp', ''))
                print(f"   Última interação: {last_interaction.get('timestamp', 'N/A')}")
        except:
            print(f"\n📊 ESTATÍSTICAS")
            print(f"   Conversas no histórico: N/A")
        
        print(f"\n💡 Para executar este agente:")
        print(f"   conductor execute --agent {args.agent} --input '<sua mensagem>'")
        
    except Exception as e:
        print(f"❌ Erro ao obter informações: {e}")

def backup_agents_command(args):
    """Faz backup dos agentes para armazenamento persistente."""
    print("💾 Fazendo backup dos agentes...")
    print("=" * 50)
    
    try:
        import subprocess
        import os
        
        # Executar script de backup
        script_path = os.path.join(os.getcwd(), "scripts", "backup_agents.sh")
        
        if not os.path.exists(script_path):
            print(f"❌ Script de backup não encontrado: {script_path}")
            return
        
        result = subprocess.run([script_path], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Erro no backup: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Erro ao executar backup: {e}")

def restore_agents_command(args):
    """Restaura agentes do armazenamento persistente."""
    print("📥 Restaurando agentes do backup...")
    print("=" * 50)
    
    try:
        import subprocess
        import os
        
        # Executar script de restore
        script_path = os.path.join(os.getcwd(), "scripts", "restore_agents.sh")
        
        if not os.path.exists(script_path):
            print(f"❌ Script de restore não encontrado: {script_path}")
            return
        
        result = subprocess.run([script_path], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            # Limpar cache após restore
            agent_service = container.get_agent_discovery_service()
            agent_service.clear_cache()
            print("🔄 Cache de descoberta limpo")
        else:
            print(f"❌ Erro no restore: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Erro ao executar restore: {e}")

def install_templates_command(args):
    """Instala templates de agentes por categoria ou agente específico."""
    import os
    import shutil
    from pathlib import Path
    
    templates_dir = Path("agent_templates")
    workspace_agents = Path(".conductor_workspace/agents")
    
    if args.list:
        print("📋 Templates Disponíveis:")
        print("=" * 50)
        
        if not templates_dir.exists():
            print("❌ Diretório de templates não encontrado")
            return
        
        for category in templates_dir.iterdir():
            if category.is_dir():
                print(f"\n🏷️  {category.name.replace('_', ' ').title()}:")
                for agent in category.iterdir():
                    if agent.is_dir():
                        # Ler descrição do definition.yaml se existir
                        def_file = agent / "definition.yaml"
                        description = "Sem descrição"
                        if def_file.exists():
                            try:
                                import yaml
                                with open(def_file, 'r') as f:
                                    data = yaml.safe_load(f)
                                    description = data.get('description', 'Sem descrição')
                            except:
                                pass
                        print(f"   • {agent.name}: {description}")
        return
    
    if args.category:
        category_path = templates_dir / args.category
        if not category_path.exists():
            print(f"❌ Categoria '{args.category}' não encontrada")
            print("💡 Use --list para ver categorias disponíveis")
            return
        
        print(f"📦 Instalando categoria: {args.category}")
        print("=" * 50)
        
        installed = 0
        for agent_dir in category_path.iterdir():
            if agent_dir.is_dir():
                target = workspace_agents / agent_dir.name
                if target.exists():
                    print(f"⚠️  {agent_dir.name}: já existe, pulando")
                else:
                    shutil.copytree(agent_dir, target)
                    print(f"✅ {agent_dir.name}: instalado")
                    installed += 1
        
        print(f"\n📊 {installed} agentes instalados da categoria '{args.category}'")
        
        # Limpar cache para descobrir novos agentes
        agent_service = container.get_agent_discovery_service()
        agent_service.clear_cache()
        
    elif args.agent:
        # Procurar agente específico em todas as categorias
        found = False
        for category in templates_dir.iterdir():
            if category.is_dir():
                agent_path = category / args.agent
                if agent_path.exists():
                    target = workspace_agents / args.agent
                    if target.exists():
                        print(f"⚠️  Agente '{args.agent}' já existe")
                    else:
                        shutil.copytree(agent_path, target)
                        print(f"✅ Agente '{args.agent}' instalado da categoria '{category.name}'")
                        
                        # Limpar cache
                        agent_service = container.get_agent_discovery_service()
                        agent_service.clear_cache()
                    found = True
                    break
        
        if not found:
            print(f"❌ Agente '{args.agent}' não encontrado nos templates")
            print("💡 Use --list para ver agentes disponíveis")
    else:
        print("❌ Especifique --category, --agent ou --list")

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