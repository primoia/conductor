#!/usr/bin/env python3
import sys
from pathlib import Path
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.cli.shared import CLIArgumentParser, REPLManager
from src.container import container
from src.core.domain import TaskDTO
from src.core.observability import configure_logging


class ConductorCLI:
    """
    Unified CLI interface for all conductor operations
    with comprehensive agent management and task execution capabilities.
    """

    def __init__(
        self,
        agent_id: str,
        environment: str = None,
        project: str = None,
        meta: bool = False,
        new_agent_id: str = None,
        simulate: bool = False,
        timeout: int = 120,
        debug_mode: bool = False,
    ):
        """Initialize Conductor CLI with unified parameters."""
        self.agent_id = agent_id
        self.environment = environment
        self.project = project
        self.meta = meta
        self.new_agent_id = new_agent_id
        self.simulate_mode = simulate
        self.timeout = timeout
        self.debug_mode = debug_mode
        
        # Initialize logging
        self.logger = configure_logging(debug_mode, f"conductor_{agent_id}", agent_id)
        
        # Get services from container
        self.conductor_service = container.get_conductor_service()
        self.agent_service = container.get_agent_discovery_service()
        
        print(f"✅ ConductorCLI inicializado para agente: {agent_id}")

    @property
    def embodied(self) -> bool:
        """Check if the target agent exists in the ecosystem."""
        return self.agent_service.agent_exists(self.agent_id)

    def chat(self, message: str, debug_save_input: bool = False) -> str:
        """Send a message to the agent through ConductorService."""
        if not self.embodied:
            from src.core.constants import Messages, Paths
            suggestions = self.agent_service.get_similar_agent_names(self.agent_id)
            location = f"{Paths.WORKSPACE_ROOT}/{Paths.AGENTS_DIR}/"
            error_msg = Messages.AGENT_NOT_FOUND.format(agent_id=self.agent_id, location=location)
            if suggestions:
                error_msg += f"\n{Messages.SUGGEST_SIMILAR.format(suggestions=', '.join(suggestions))}"
            error_msg += f"\n{Messages.USE_LIST_COMMAND}"
            return error_msg

        try:
            # Handle debug mode - save input without calling provider
            if debug_save_input:
                enhanced_message = self.agent_service.build_meta_agent_context(
                    message, self.meta, self.new_agent_id
                )
                # For now, just return debug info
                return f"✅ DEBUG MODE: Input captured. Enhanced message length: {len(enhanced_message)} chars"

            # Handle simulation mode
            if self.simulate_mode:
                return f"🎭 SIMULATION: Would send '{message[:50]}...' to {self.agent_id}"

            # Build task context
            task_context = {
                "meta": self.meta,
                "new_agent_id": self.new_agent_id,
                "debug_save_input": debug_save_input,
                "simulate_mode": self.simulate_mode,
                "timeout": self.timeout
            }
            
            # Add project context if available
            if self.environment:
                task_context["environment"] = self.environment
            if self.project:
                task_context["project"] = self.project

            # Create and execute task
            task = TaskDTO(
                agent_id=self.agent_id,
                user_input=message,
                context=task_context
            )

            # Execute through conductor service
            result = self.conductor_service.execute_task(task)

            # Process result
            if result.status == "success":
                return result.output
            else:
                return f"❌ Erro na execução da tarefa: {result.output}"

        except Exception as e:
            self.logger.error(f"Erro no chat do ConductorCLI: {e}")
            return f"❌ Erro fatal no ConductorCLI: {e}"

    def get_available_tools(self) -> list:
        """Get available tools from agent definition."""
        try:
            agent_definition = self.agent_service.get_agent_definition(self.agent_id)
            return agent_definition.allowed_tools if agent_definition else []
        except Exception as e:
            self.logger.error(f"Error getting available tools: {e}")
            return []

    def get_conversation_history(self) -> list:
        """Get conversation history through AgentService."""
        try:
            return self.agent_service.get_conversation_history(self.agent_id)
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []

    def clear_conversation_history(self) -> bool:
        """Clear the agent's conversation history through AgentService."""
        try:
            success = self.agent_service.clear_conversation_history(self.agent_id)
            if success:
                self.logger.info(f"Cleared conversation history for agent {self.agent_id}")
            else:
                self.logger.warning(f"Could not clear conversation history for agent {self.agent_id}")
            return success
        except Exception as e:
            self.logger.error(f"Error clearing conversation history: {e}")
            return False

    def save_agent_state(self):
        """Save agent state using AgentService."""
        return self.agent_service.save_agent_state(self.agent_id)

    def get_output_scope(self) -> list:
        """Get output scope restrictions from agent definition."""
        return self.agent_service.get_agent_output_scope(self.agent_id)

    def get_full_prompt(self, sample_message: str = "Mensagem de exemplo") -> str:
        """Get the complete prompt that would be sent to the AI provider."""
        return self.agent_service.get_full_prompt(
            agent_id=self.agent_id, 
            sample_message=sample_message, 
            meta=self.meta, 
            new_agent_id=self.new_agent_id,
            current_message=None,
            save_to_file=False
        )


def main():
    """Ponto de entrada unificado para o Conductor CLI."""
    parser = CLIArgumentParser.create_main_parser()
    args = parser.parse_args()

    # Handle new unified interface
    if args.list:
        list_agents_command(args)
    elif args.info:
        info_agent_command_new(args)
    elif args.validate:
        validate_config_command(args)
    elif args.install:
        install_templates_command_new(args)
    elif args.backup:
        backup_agents_command(args)
    elif args.restore:
        restore_agents_command(args)
    elif args.migrate_to:
        migrate_agents_command(args)
    elif args.agent:
        # Main agent interaction logic
        handle_agent_interaction(args)
    elif hasattr(args, 'func') and args.func:
        # Legacy subcommand
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)

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
        
        output_mode = getattr(args, 'output', 'text')
        if output_mode == 'json':
            payload = {
                "status": result.status,
                "output": result.output,
                "metadata": result.metadata,
                "updated_session": result.updated_session,
                "updated_knowledge": result.updated_knowledge,
                "history_entry": result.history_entry,
            }
            print(json.dumps(payload, ensure_ascii=False))
        else:
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

def migrate_agents_command(args):
    """Migrar agentes entre backends usando o motor de sincronização."""
    import subprocess
    import os
    from src.core.services.configuration_service import ConfigurationService
    
    try:
        # Determinar backend de origem
        if args.migrate_from:
            source = args.migrate_from
        else:
            # Usar configuração atual como padrão
            config_service = ConfigurationService()
            source = config_service.get_storage_config().type
        
        destination = args.migrate_to
        
        print(f"🔄 Migrando agentes: {source} → {destination}")
        print("=" * 50)
        
        # Preparar argumentos para o sync_engine
        sync_script = os.path.join(os.getcwd(), "scripts", "helpers", "sync_engine.py")
        
        if not os.path.exists(sync_script):
            print(f"❌ Script de sincronização não encontrado: {sync_script}")
            return
        
        cmd = [
            "python3", sync_script,
            "--source", source,
            "--destination", destination
        ]
        
        # Adicionar flags opcionais
        if args.no_config_update:
            cmd.append("--no-config-update")
        
        if args.path:
            cmd.extend(["--path", args.path])
        
        # Executar migração
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n🎉 Migração concluída com sucesso!")
            
            # Limpar cache após migração se houve mudança de backend
            if not args.no_config_update:
                agent_service = container.get_agent_discovery_service()
                agent_service.clear_cache()
                print("🔄 Cache de descoberta limpo")
        else:
            print(f"❌ Erro na migração (código: {result.returncode})")
            
    except Exception as e:
        print(f"❌ Erro ao executar migração: {e}")

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

def repl_command(args):
    """Start unified REPL session with different modes."""
    print(f"🚀 Iniciando sessão REPL unificada")
    print(f"   Agente: {args.agent}")
    print(f"   Modo: {args.mode}")
    
    if args.environment:
        print(f"   Environment: {args.environment}")
    if args.project:
        print(f"   Project: {args.project}")
    if args.meta:
        print(f"   Tipo: meta-agent")
    if args.simulate:
        print(f"   🎭 Modo simulação ativado")
    
    # Initialize unified CLI
    cli = ConductorCLI(
        agent_id=args.agent,
        environment=args.environment,
        project=args.project,
        meta=args.meta,
        new_agent_id=args.new_agent_id,
        simulate=args.simulate,
        timeout=args.timeout,
        debug_mode=(args.mode == 'dev')
    )
    
    if not cli.embodied:
        print(f"❌ Agente não encontrado: {args.agent}")
        return
    
    # Configure REPL based on mode
    repl_manager = REPLManager(args.agent, cli)
    
    # Add mode-specific commands
    if args.mode in ['advanced', 'dev']:
        repl_manager.add_custom_command(
            "debug", lambda: _show_debug_info(cli)
        )
        repl_manager.add_custom_command(
            "prompt", lambda: _show_full_prompt(cli)
        )
        
    if args.mode == 'dev':
        repl_manager.add_custom_command(
            "simulate", lambda: _toggle_simulation(cli)
        )
        repl_manager.add_custom_command(
            "export-debug", lambda: _export_debug_report(cli)
        )
    
    # Show mode-specific help
    mode_help = _get_mode_help(args.mode)
    
    # Start REPL session
    repl_manager.start_session(mode_help)

def chat_command(args):
    """Send a message with context preservation (like REPL but single message)."""
    print(f"💬 Chat com {args.agent}")
    
    # Clear history if requested
    if args.clear_history:
        cli = ConductorCLI(agent_id=args.agent)
        if cli.clear_conversation_history():
            print("🗑️ Histórico limpo")
        else:
            print("⚠️ Não foi possível limpar o histórico")
    
    # Initialize CLI
    cli = ConductorCLI(
        agent_id=args.agent,
        environment=args.environment,
        project=args.project,
        meta=args.meta,
        new_agent_id=args.new_agent_id
    )
    
    if not cli.embodied:
        print(f"❌ Agente não encontrado: {args.agent}")
        return
    
    # Send message
    print(f"📝 Enviando: {args.input}")
    print("-" * 50)
    
    response = cli.chat(args.input)
    
    print("🤖 Resposta:")
    print("=" * 50)
    print(response)
    print("=" * 50)
    
    # Show history if requested
    if args.show_history:
        history = cli.get_conversation_history()
        print(f"\n📚 Histórico ({len(history)} mensagens):")
        for i, msg in enumerate(history[-3:], 1):  # Show last 3
            user_msg = msg.get('user_input', 'N/A')
            ai_msg = msg.get('ai_response', 'N/A')
            print(f"  {i}. 👤: {user_msg[:50]}...")
            print(f"     🤖: {ai_msg[:50]}...")

# Helper functions for REPL modes
def _get_mode_help(mode: str) -> str:
    """Get help text for specific REPL mode."""
    if mode == 'basic':
        return "💡 Modo básico: Digite suas mensagens normalmente"
    elif mode == 'advanced':
        return "🔍 Modo avançado: Use 'debug' e 'prompt' para informações técnicas"
    elif mode == 'dev':
        return "🛠️ Modo desenvolvedor: Comandos completos de debug e desenvolvimento"
    return ""

def _show_debug_info(cli):
    """Show debug information."""
    print("\n🔍 === DEBUG INFO ===")
    print(f"Agent ID: {cli.agent_id}")
    print(f"Embodied: {cli.embodied}")
    print(f"Meta mode: {cli.meta}")
    print(f"Simulation: {cli.simulate_mode}")
    print(f"Tools: {cli.get_available_tools()}")
    print("=" * 30)

def _show_full_prompt(cli):
    """Show full prompt that would be sent to AI."""
    print("\n📝 === PROMPT COMPLETO ===")
    prompt = cli.get_full_prompt()
    print(prompt)
    print(f"\n📊 Tamanho: {len(prompt)} caracteres")
    print("=" * 40)

def _toggle_simulation(cli):
    """Toggle simulation mode."""
    cli.simulate_mode = not cli.simulate_mode
    status = "ATIVADO" if cli.simulate_mode else "DESATIVADO"
    print(f"\n🎭 Modo simulação: {status}")

def _export_debug_report(cli):
    """Export debug report (placeholder)."""
    print("\n📊 === RELATÓRIO DE DEBUG ===")
    print("Funcionalidade em desenvolvimento...")
    print("=" * 40)

def handle_agent_interaction(args):
    """Handle the main agent interaction logic with new unified interface."""
    # Validate arguments
    if not args.input and not args.interactive:
        print("❌ Erro: Especifique --input ou --interactive")
        print("💡 Exemplos:")
        print("   conductor --agent MyAgent --input 'sua mensagem'")
        print("   conductor --agent MyAgent --chat --interactive")
        return

    if args.interactive and not args.chat:
        print("❌ Erro: --interactive requer --chat")
        print("💡 Use: conductor --agent MyAgent --chat --interactive")
        return

    # Determine execution mode
    include_history = args.chat
    save_to_history = args.chat
    
    # Show execution mode
    if args.simulate:
        mode_desc = "🎭 Modo simulação"
    elif include_history:
        mode_desc = "💬 Modo contextual (com histórico)"
    else:
        mode_desc = "⚡ Modo isolado (sem histórico)"
    
    print(f"🤖 Executando {args.agent}")
    print(f"📋 {mode_desc}")
    
    if args.project:
        print(f"🏗️ Projeto: {args.project}")
    if args.environment:
        print(f"🌐 Ambiente: {args.environment}")
    if args.meta:
        print(f"🔧 Meta-agent ativo")
    
    print("=" * 50)

    try:
        # Clear history if requested
        if args.clear:
            cli = ConductorCLI(agent_id=args.agent)
            if cli.clear_conversation_history():
                print("🗑️ Histórico limpo")
            else:
                print("⚠️ Não foi possível limpar o histórico")

        # Initialize CLI
        cli = ConductorCLI(
            agent_id=args.agent,
            environment=args.environment,
            project=args.project,
            meta=args.meta,
            new_agent_id=args.new_agent_id,
            simulate=args.simulate,
            timeout=args.timeout,
            debug_mode=False
        )

        if not cli.embodied:
            agent_service = container.get_agent_discovery_service()
            suggestions = agent_service.get_similar_agent_names(args.agent)
            print(f"❌ Agente '{args.agent}' não encontrado")
            if suggestions:
                print(f"💡 Agentes similares: {', '.join(suggestions)}")
            print("📋 Use 'conductor --list' para ver todos os agentes")
            return

        # Show history info if in contextual mode
        if include_history:
            history = cli.get_conversation_history()
            print(f"📚 Histórico: {len(history)} interações anteriores")

        # Execute initial message if provided
        if args.input:
            print(f"📝 Input: {args.input}")
            print("-" * 50)

            # Create task with history flags
            task_context = {
                "include_history": include_history,
                "save_to_history": save_to_history,
                "meta": args.meta,
                "new_agent_id": args.new_agent_id,
                "simulate_mode": args.simulate,
                "timeout": args.timeout
            }
            
            if args.environment:
                task_context["environment"] = args.environment
            if args.project:
                task_context["project"] = args.project

            task = TaskDTO(
                agent_id=args.agent,
                user_input=args.input,
                context=task_context
            )

            result = cli.conductor_service.execute_task(task)

            output_mode = getattr(args, 'output', 'text')
            if output_mode == 'json':
                payload = {
                    "status": result.status,
                    "output": result.output,
                    "metadata": result.metadata,
                    "updated_session": result.updated_session,
                    "updated_knowledge": result.updated_knowledge,
                    "history_entry": result.history_entry,
                }
                print(json.dumps(payload, ensure_ascii=False))
            else:
                print("🤖 Resposta:")
                print("=" * 50)
                if result.status == "success":
                    print(result.output)
                else:
                    print(f"❌ Erro: {result.output}")
                print("=" * 50)

            # Show execution stats
            if args.simulate:
                print("🎭 Simulação concluída (sem chamada real à IA)")
            elif include_history:
                print("✅ Resposta adicionada ao histórico")
            else:
                print("⚡ Execução isolada concluída")

        # Enter interactive mode if requested
        if args.interactive:
            print("\n🎮 Entrando no modo interativo...")
            print("💡 Digite 'exit' para sair")
            
            # Use existing REPL manager
            repl_manager = REPLManager(args.agent, cli)
            
            # Add debug commands based on context
            if args.meta or args.simulate:
                repl_manager.add_custom_command("debug", lambda: _show_debug_info(cli))
                repl_manager.add_custom_command("prompt", lambda: _show_full_prompt(cli))
            
            if args.simulate:
                repl_manager.add_custom_command("simulate", lambda: _toggle_simulation(cli))
            
            mode_help = "🎮 Modo interativo ativo"
            if args.simulate:
                mode_help += " (simulação)"
            
            repl_manager.start_session(mode_help)

    except Exception as e:
        print(f"❌ Erro fatal: {e}")

def info_agent_command_new(args):
    """Show detailed information about an agent (new interface)."""
    # Reuse existing logic but with new argument structure
    class InfoArgs:
        def __init__(self, agent_id):
            self.agent = agent_id
    
    info_args = InfoArgs(args.info)
    info_agent_command(info_args)

def install_templates_command_new(args):
    """Install agent templates (new interface)."""
    if args.install == "list":
        # Show available templates
        print("📋 Templates Disponíveis:")
        print("=" * 50)
        
        from pathlib import Path
        templates_dir = Path("agent_templates")
        
        if not templates_dir.exists():
            print("❌ Diretório de templates não encontrado")
            return
        
        for category in templates_dir.iterdir():
            if category.is_dir():
                print(f"\n🏷️ {category.name.replace('_', ' ').title()}:")
                for agent in category.iterdir():
                    if agent.is_dir():
                        # Read description from definition.yaml if exists
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
        
        print(f"\n💡 Para instalar:")
        print(f"   conductor --install <categoria>")
        print(f"   conductor --install <agent_name>")
        return
    
    # Install specific category or agent
    class InstallArgs:
        def __init__(self, install_target):
            # Try to determine if it's a category or specific agent
            from pathlib import Path
            templates_dir = Path("agent_templates")
            
            # Check if it's a category
            if (templates_dir / install_target).exists():
                self.category = install_target
                self.agent = None
                self.list = False
            else:
                # Assume it's a specific agent
                self.category = None
                self.agent = install_target
                self.list = False
    
    install_args = InstallArgs(args.install)
    install_templates_command(install_args)

if __name__ == "__main__":
    main()