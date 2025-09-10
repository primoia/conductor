# Especificação Técnica e Plano de Execução: 0028.12-garantir-fs-mock-discovery

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção visa garantir que o `FileSystemStateRepository` descubra e carregue corretamente os agentes mockados criados nos testes, resolvendo as falhas nos testes de integração e permitindo a validação da Fase VII.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve modificar os arquivos `src/infrastructure/persistence/state_repository.py` e `tests/e2e/test_full_flow.py`.

**Arquivo 1 (Modificar): `src/infrastructure/persistence/state_repository.py`**

```python
# src/infrastructure/persistence/state_repository.py
# ... (imports existentes)

class FileStateRepository(StateRepository):
    # ... (manter __init__ e save_state)

    def load_state(self, agent_id: str) -> Dict[str, Any]:
        agent_file_path = self.agents_path / f"{agent_id}.json"
        try:
            if agent_file_path.exists():
                with open(agent_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            # Retorna um estado inicial padrão se o arquivo não existir
            # O ConductorService espera uma estrutura com 'definition' para AgentDefinition
            return {"definition": {"name": "", "version": "", "schema_version": "", "description": "", "author": "", "tags": [], "capabilities": [], "allowed_tools": []}}
        except Exception as e:
            logger.error(f"Failed to load agent state from {agent_file_path}: {e}")
            raise StatePersistenceError(
                f"Failed to load agent state from {agent_file_path}: {e}"
            )

    def list_agents(self) -> List[str]:
        """Lista os IDs de todos os agentes disponíveis no backend de armazenamento."""
        agent_ids = []
        # Garantir que o diretório exista antes de iterar
        if self.agents_path.exists() and self.agents_path.is_dir():
            for item in self.agents_path.iterdir():
                if item.is_file() and item.suffix == ".json":
                    agent_ids.append(item.stem)
        return agent_ids

# ... (restante do arquivo)
```

**Arquivo 2 (Modificar): `tests/e2e/test_full_flow.py`**

```python
# tests/e2e/test_full_flow.py
# ... (imports existentes)

@pytest.fixture
def filesystem_service(tmp_path):
    """Fixture para criar um ConductorService com backend de filesystem."""
    # Criar config e workspace de teste
    config_path = tmp_path / "config.yaml"
    workspace_path = tmp_path / ".test_workspace"
    workspace_path.mkdir()
    
    FILESYSTEM_CONFIG["storage"]["path"] = str(workspace_path)
    with open(config_path, "w") as f:
        yaml.dump(FILESYSTEM_CONFIG, f)

    # Criar um agente mock no workspace
    # O FileSystemStateRepository espera arquivos .json diretamente no subdiretório 'agents'
    agent_dir = workspace_path / "agents"
    agent_dir.mkdir(parents=True)
    
    # Conteúdo do agente mock no formato JSON
    agent_content = {
        "definition": {
            "name": "FS Agent", 
            "version": "1.0", 
            "schema_version": "1.0",
            "description": "A test agent for filesystem flow", 
            "author": "test",
            "tags": [],
            "capabilities": [],
            "allowed_tools": []
        },
        "agent_home_path": str(agent_dir.resolve()), # Caminho para o diretório do agente
        "allowed_tools": []
    }
    
    # Salvar como arquivo JSON
    with open(agent_dir / "fs_agent.json", "w") as f:
        json.dump(agent_content, f, indent=2)

    return ConductorService(config_path=str(config_path))

# ... (restante do arquivo)
```

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
