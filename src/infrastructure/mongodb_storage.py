# src/infrastructure/mongodb_storage.py

import json
from typing import List, Dict
from pymongo import MongoClient
from datetime import datetime

from src.core.domain import (
    AgentDefinition, AgentPersona, AgentPlaybook, AgentKnowledge, HistoryEntry, AgentSession,
    PlaybookBestPractice, PlaybookAntiPattern, KnowledgeItem
)

class MongoDbStorage:
    """
    Implementa a persistência de artefatos de agente usando MongoDB.
    """

    def __init__(self, connection_string: str, db_name: str = "conductor", agent_name: str = None):
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.agents_collection = self.db["agents"]
        self.history_collection = self.db["history"]
        self.sessions_collection = self.db["sessions"]
        self.agent_name = agent_name
        
        # Criar índice TTL na coleção de sessões, se não existir
        self.sessions_collection.create_index("createdAt", expireAfterSeconds=86400)
        
        # Criar índices para otimização
        self.agents_collection.create_index("name")
        self.history_collection.create_index("agent_id")
        self.sessions_collection.create_index("agent_id")

    def load_definition(self) -> AgentDefinition:
        """Carrega a definição de um agente a partir do MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to load definition")
            
        doc = self.agents_collection.find_one({"name": self.agent_name})
        if not doc or "definition" not in doc:
            raise FileNotFoundError(f"Definition not found for agent: {self.agent_name}")
        
        def_data = doc["definition"]
        return AgentDefinition(
            name=def_data['name'],
            version=def_data['version'],
            schema_version=def_data['schema_version'],
            description=def_data['description'],
            author=def_data['author'],
            tags=def_data.get('tags', []),
            capabilities=def_data.get('capabilities', []),
            allowed_tools=def_data.get('allowed_tools', [])
        )

    def save_definition(self, definition: AgentDefinition):
        """Salva (ou atualiza) a definição de um agente no MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to save definition")
            
        def_data = {
            'name': definition.name,
            'version': definition.version,
            'schema_version': definition.schema_version,
            'description': definition.description,
            'author': definition.author,
            'tags': definition.tags,
            'capabilities': definition.capabilities,
            'allowed_tools': definition.allowed_tools
        }
        
        self.agents_collection.update_one(
            {"name": self.agent_name},
            {"$set": {"definition": def_data}},
            upsert=True
        )

    def load_persona(self) -> AgentPersona:
        """Carrega a persona do agente a partir do MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to load persona")
            
        doc = self.agents_collection.find_one({"name": self.agent_name})
        if not doc or "persona" not in doc:
            raise FileNotFoundError(f"Persona not found for agent: {self.agent_name}")
        
        return AgentPersona(content=doc["persona"]["content"])

    def save_persona(self, persona: AgentPersona):
        """Salva a persona do agente no MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to save persona")
            
        persona_data = {"content": persona.content}
        
        self.agents_collection.update_one(
            {"name": self.agent_name},
            {"$set": {"persona": persona_data}},
            upsert=True
        )

    def load_playbook(self) -> AgentPlaybook:
        """Carrega o playbook do agente a partir do MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to load playbook")
            
        doc = self.agents_collection.find_one({"name": self.agent_name})
        if not doc or "playbook" not in doc:
            raise FileNotFoundError(f"Playbook not found for agent: {self.agent_name}")
        
        playbook_data = doc["playbook"]
        
        best_practices = []
        if 'best_practices' in playbook_data:
            for bp_data in playbook_data['best_practices']:
                best_practices.append(PlaybookBestPractice(
                    id=bp_data['id'],
                    title=bp_data['title'],
                    description=bp_data['description']
                ))
        
        anti_patterns = []
        if 'anti_patterns' in playbook_data:
            for ap_data in playbook_data['anti_patterns']:
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
        """Salva o playbook do agente no MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to save playbook")
            
        playbook_data = {}
        
        if playbook.best_practices:
            playbook_data['best_practices'] = [
                {
                    'id': bp.id,
                    'title': bp.title,
                    'description': bp.description
                }
                for bp in playbook.best_practices
            ]
        
        if playbook.anti_patterns:
            playbook_data['anti_patterns'] = [
                {
                    'id': ap.id,
                    'title': ap.title,
                    'description': ap.description
                }
                for ap in playbook.anti_patterns
            ]
        
        self.agents_collection.update_one(
            {"name": self.agent_name},
            {"$set": {"playbook": playbook_data}},
            upsert=True
        )

    def load_knowledge(self) -> AgentKnowledge:
        """Carrega o conhecimento do agente a partir do MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to load knowledge")
            
        doc = self.agents_collection.find_one({"name": self.agent_name})
        if not doc or "knowledge" not in doc:
            raise FileNotFoundError(f"Knowledge not found for agent: {self.agent_name}")
        
        knowledge_data = doc["knowledge"]
        artifacts = {}
        if 'artifacts' in knowledge_data:
            for path, item_data in knowledge_data['artifacts'].items():
                artifacts[path] = KnowledgeItem(
                    summary=item_data['summary'],
                    purpose=item_data['purpose'],
                    last_modified_by_task=item_data['last_modified_by_task']
                )
        
        return AgentKnowledge(artifacts=artifacts)

    def save_knowledge(self, knowledge: AgentKnowledge):
        """Salva o conhecimento do agente no MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to save knowledge")
            
        knowledge_data = {
            'artifacts': {
                path: {
                    'summary': item.summary,
                    'purpose': item.purpose,
                    'last_modified_by_task': item.last_modified_by_task
                }
                for path, item in knowledge.artifacts.items()
            }
        }
        
        self.agents_collection.update_one(
            {"name": self.agent_name},
            {"$set": {"knowledge": knowledge_data}},
            upsert=True
        )

    def load_history(self) -> List[HistoryEntry]:
        """Carrega o histórico de um agente a partir do MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to load history")
            
        cursor = self.history_collection.find({"agent_id": self.agent_name}).sort("_id", 1)
        history_entries = []
        
        for doc in cursor:
            history_entries.append(HistoryEntry(
                _id=doc['_id'],
                agent_id=doc['agent_id'],
                task_id=doc['task_id'],
                status=doc['status'],
                summary=doc['summary'],
                git_commit_hash=doc['git_commit_hash']
            ))
        
        return history_entries

    def append_to_history(self, entry: HistoryEntry):
        """Adiciona uma nova entrada ao histórico no MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to append to history")
            
        doc = {
            '_id': entry._id,
            'agent_id': entry.agent_id,
            'task_id': entry.task_id,
            'status': entry.status,
            'summary': entry.summary,
            'git_commit_hash': entry.git_commit_hash,
            'createdAt': datetime.utcnow()
        }
        
        self.history_collection.insert_one(doc)

    def load_session(self) -> AgentSession:
        """Carrega a sessão a partir do MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to load session")
            
        doc = self.sessions_collection.find_one({"agent_id": self.agent_name})
        if not doc:
            raise FileNotFoundError(f"Session not found for agent: {self.agent_name}")
        
        return AgentSession(
            current_task_id=doc['current_task_id'],
            state=doc.get('state', {})
        )

    def save_session(self, session: AgentSession):
        """Salva a sessão no MongoDB."""
        if not self.agent_name:
            raise ValueError("Agent name must be set to save session")
            
        doc = {
            'agent_id': self.agent_name,
            'current_task_id': session.current_task_id,
            'state': session.state,
            'createdAt': datetime.utcnow()
        }
        
        self.sessions_collection.replace_one(
            {"agent_id": self.agent_name},
            doc,
            upsert=True
        )