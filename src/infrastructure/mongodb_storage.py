# src/infrastructure/mongodb_storage.py

from typing import List

from src.core.domain import (
    AgentDefinition, AgentPersona, AgentPlaybook, AgentKnowledge, HistoryEntry, AgentSession,
    PlaybookBestPractice, PlaybookAntiPattern, KnowledgeItem
)
from src.ports.agent_storage import IAgentStorage
from src.infrastructure.storage.mongo_repository import MongoStateRepository

class MongoDbStorage(IAgentStorage):
    """
    Implementa a camada de alto nível para artefatos de agente no MongoDB.
    Trabalha com objetos de domínio e delega a persistência para MongoStateRepository.
    """

    def __init__(self, connection_string: str, db_name: str = "conductor"):
        self.repository = MongoStateRepository(connection_string, db_name)

    def load_definition(self, agent_id: str) -> AgentDefinition:
        """Carrega a definição do agente."""
        data = self.repository.load_definition(agent_id)
        if not data:
            raise FileNotFoundError(f"Definition not found for agent: {agent_id}")

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

    def save_definition(self, agent_id: str, definition: AgentDefinition):
        """Salva a definição do agente."""
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

        success = self.repository.save_definition(agent_id, data)
        if not success:
            raise RuntimeError(f"Failed to save definition for agent: {agent_id}")

    def load_persona(self, agent_id: str) -> AgentPersona:
        """Carrega a persona do agente."""
        content = self.repository.load_persona(agent_id)
        if not content:
            raise FileNotFoundError(f"Persona not found for agent: {agent_id}")

        return AgentPersona(content=content)

    def save_persona(self, agent_id: str, persona: AgentPersona):
        """Salva a persona do agente."""
        success = self.repository.save_persona(agent_id, persona.content)
        if not success:
            raise RuntimeError(f"Failed to save persona for agent: {agent_id}")

    def load_playbook(self, agent_id: str) -> AgentPlaybook:
        """Carrega o playbook do agente."""
        data = self.repository.load_playbook(agent_id)
        if not data:
            raise FileNotFoundError(f"Playbook not found for agent: {agent_id}")

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

    def save_playbook(self, agent_id: str, playbook: AgentPlaybook):
        """Salva o playbook do agente."""
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

        success = self.repository.save_playbook(agent_id, data)
        if not success:
            raise RuntimeError(f"Failed to save playbook for agent: {agent_id}")

    def load_knowledge(self, agent_id: str) -> AgentKnowledge:
        """Carrega o conhecimento do agente."""
        data = self.repository.load_knowledge(agent_id)
        if not data:
            raise FileNotFoundError(f"Knowledge not found for agent: {agent_id}")

        artifacts = {}
        if 'artifacts' in data:
            for path, item_data in data['artifacts'].items():
                artifacts[path] = KnowledgeItem(
                    summary=item_data['summary'],
                    purpose=item_data['purpose'],
                    last_modified_by_task=item_data['last_modified_by_task']
                )

        return AgentKnowledge(artifacts=artifacts)

    def save_knowledge(self, agent_id: str, knowledge: AgentKnowledge):
        """Salva o conhecimento do agente."""
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

        success = self.repository.save_knowledge(agent_id, data)
        if not success:
            raise RuntimeError(f"Failed to save knowledge for agent: {agent_id}")

    def load_history(self, agent_id: str) -> List[HistoryEntry]:
        """Carrega o histórico do agente."""
        history_data = self.repository.load_history(agent_id)

        history_entries = []
        for data in history_data:
            history_entries.append(HistoryEntry(
                _id=data.get('_id'),
                agent_id=data['agent_id'],
                task_id=data['task_id'],
                status=data['status'],
                summary=data['summary'],
                git_commit_hash=data['git_commit_hash']
            ))

        return history_entries

    def append_to_history(self, agent_id: str, entry: HistoryEntry):
        """Adiciona uma entrada ao histórico do agente."""
        data = {
            '_id': entry._id,
            'agent_id': entry.agent_id,
            'task_id': entry.task_id,
            'status': entry.status,
            'summary': entry.summary,
            'git_commit_hash': entry.git_commit_hash
        }

        success = self.repository.append_to_history(agent_id, data)
        if not success:
            raise RuntimeError(f"Failed to append to history for agent: {agent_id}")

    def load_session(self, agent_id: str) -> AgentSession:
        """Carrega a sessão do agente."""
        data = self.repository.load_session(agent_id)
        if not data:
            raise FileNotFoundError(f"Session not found for agent: {agent_id}")

        return AgentSession(
            current_task_id=data['current_task_id'],
            state=data.get('state', {})
        )

    def save_session(self, agent_id: str, session: AgentSession):
        """Salva a sessão do agente."""
        data = {
            'current_task_id': session.current_task_id,
            'state': session.state
        }

        success = self.repository.save_session(agent_id, data)
        if not success:
            raise RuntimeError(f"Failed to save session for agent: {agent_id}")

    def list_agents(self) -> List[str]:
        """Lista todos os agentes disponíveis."""
        return self.repository.list_agents()