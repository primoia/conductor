# src/infrastructure/filesystem_storage.py

import json
import yaml
from pathlib import Path
from typing import List

from src.core.domain import (
    AgentDefinition, AgentPersona, AgentPlaybook, AgentKnowledge, HistoryEntry, AgentSession,
    PlaybookBestPractice, PlaybookAntiPattern, KnowledgeItem
)

class FileSystemStorage:
    """
    Implementa a persistência de artefatos de agente usando o sistema de arquivos local.
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path
        # Garante que o diretório base do agente exista.
        self.base_path.mkdir(parents=True, exist_ok=True)

    def load_definition(self) -> AgentDefinition:
        """Carrega a definição do agente de definition.yaml."""
        definition_path = self.base_path / "definition.yaml"
        if not definition_path.exists():
            raise FileNotFoundError(f"Definition file not found: {definition_path}")
        
        with open(definition_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return AgentDefinition(
            name=data['name'],
            version=data['version'],
            schema_version=data['schema_version'],
            description=data['description'],
            author=data['author'],
            tags=data.get('tags', []),
            capabilities=data.get('capabilities', []),
            allowed_tools=data.get('allowed_tools', [])
        )

    def save_definition(self, definition: AgentDefinition):
        """Salva a definição do agente em definition.yaml."""
        definition_path = self.base_path / "definition.yaml"
        
        data = {
            'name': definition.name,
            'version': definition.version,
            'schema_version': definition.schema_version,
            'description': definition.description,
            'author': definition.author,
            'tags': definition.tags,
            'capabilities': definition.capabilities,
            'allowed_tools': definition.allowed_tools
        }
        
        with open(definition_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

    def load_persona(self) -> AgentPersona:
        """Carrega a persona do agente de persona.md."""
        persona_path = self.base_path / "persona.md"
        if not persona_path.exists():
            raise FileNotFoundError(f"Persona file not found: {persona_path}")
        
        with open(persona_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return AgentPersona(content=content)

    def save_persona(self, persona: AgentPersona):
        """Salva a persona do agente em persona.md."""
        persona_path = self.base_path / "persona.md"
        
        with open(persona_path, 'w', encoding='utf-8') as f:
            f.write(persona.content)

    def load_playbook(self) -> AgentPlaybook:
        """Carrega o playbook do agente de playbook.yaml."""
        playbook_path = self.base_path / "playbook.yaml"
        if not playbook_path.exists():
            raise FileNotFoundError(f"Playbook file not found: {playbook_path}")
        
        with open(playbook_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        best_practices = []
        if 'best_practices' in data:
            for bp_data in data['best_practices']:
                best_practices.append(PlaybookBestPractice(
                    id=bp_data['id'],
                    title=bp_data['title'],
                    description=bp_data['description']
                ))
        
        anti_patterns = []
        if 'anti_patterns' in data:
            for ap_data in data['anti_patterns']:
                anti_patterns.append(PlaybookAntiPattern(
                    id=ap_data['id'],
                    title=ap_data['title'],
                    description=ap_data['description']
                ))
        
        return AgentPlaybook(
            best_practices=best_practices,
            anti_patterns=anti_patterns
        )

    def save_playbook(self, playbook: AgentPlaybook):
        """Salva o playbook do agente em playbook.yaml."""
        playbook_path = self.base_path / "playbook.yaml"
        
        data = {}
        
        if playbook.best_practices:
            data['best_practices'] = [
                {
                    'id': bp.id,
                    'title': bp.title,
                    'description': bp.description
                }
                for bp in playbook.best_practices
            ]
        
        if playbook.anti_patterns:
            data['anti_patterns'] = [
                {
                    'id': ap.id,
                    'title': ap.title,
                    'description': ap.description
                }
                for ap in playbook.anti_patterns
            ]
        
        with open(playbook_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

    def load_knowledge(self) -> AgentKnowledge:
        """Carrega o conhecimento do agente de knowledge.json."""
        knowledge_path = self.base_path / "knowledge.json"
        if not knowledge_path.exists():
            raise FileNotFoundError(f"Knowledge file not found: {knowledge_path}")
        
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        artifacts = {}
        if 'artifacts' in data:
            for path, item_data in data['artifacts'].items():
                artifacts[path] = KnowledgeItem(
                    summary=item_data['summary'],
                    purpose=item_data['purpose'],
                    last_modified_by_task=item_data['last_modified_by_task']
                )
        
        return AgentKnowledge(artifacts=artifacts)

    def save_knowledge(self, knowledge: AgentKnowledge):
        """Salva o conhecimento do agente em knowledge.json."""
        knowledge_path = self.base_path / "knowledge.json"
        
        data = {
            'artifacts': {
                path: {
                    'summary': item.summary,
                    'purpose': item.purpose,
                    'last_modified_by_task': item.last_modified_by_task
                }
                for path, item in knowledge.artifacts.items()
            }
        }
        
        with open(knowledge_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_history(self) -> List[HistoryEntry]:
        """Carrega o histórico de um agente a partir de history.log (JSON Lines)."""
        history_path = self.base_path / "history.log"
        if not history_path.exists():
            return []
        
        history_entries = []
        with open(history_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    history_entries.append(HistoryEntry(
                        _id=data['_id'],
                        agent_id=data['agent_id'],
                        task_id=data['task_id'],
                        status=data['status'],
                        summary=data['summary'],
                        git_commit_hash=data['git_commit_hash']
                    ))
        
        return history_entries

    def append_to_history(self, entry: HistoryEntry):
        """Adiciona uma nova entrada ao final de history.log (JSON Lines)."""
        history_path = self.base_path / "history.log"
        
        data = {
            '_id': entry._id,
            'agent_id': entry.agent_id,
            'task_id': entry.task_id,
            'status': entry.status,
            'summary': entry.summary,
            'git_commit_hash': entry.git_commit_hash
        }
        
        with open(history_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    def load_session(self) -> AgentSession:
        """Carrega a sessão de session.json."""
        session_path = self.base_path / "session.json"
        if not session_path.exists():
            raise FileNotFoundError(f"Session file not found: {session_path}")
        
        with open(session_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return AgentSession(
            current_task_id=data['current_task_id'],
            state=data.get('state', {})
        )

    def save_session(self, session: AgentSession):
        """Salva a sessão em session.json."""
        session_path = self.base_path / "session.json"
        
        data = {
            'current_task_id': session.current_task_id,
            'state': session.state
        }
        
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)