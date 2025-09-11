# src/infrastructure/storage/filesystem_repository.py
import os
import json
import yaml
from src.ports.state_repository import IStateRepository
from typing import Dict, Any, List

class FileSystemStateRepository(IStateRepository):
    """Implementação de repositório de estado baseada em sistema de arquivos."""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or ".conductor_workspace"

    def _get_agent_dir(self, agent_id: str) -> str:
        """Retorna o diretório do agente, criando-o se necessário."""
        agent_dir = os.path.join(self.base_path, "agents", agent_id)
        os.makedirs(agent_dir, exist_ok=True)
        return agent_dir

    def load_definition(self, agent_id: str) -> Dict:
        """Carrega a definição do agente (definition.yaml)."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            definition_file = os.path.join(agent_dir, "definition.yaml")
            if os.path.exists(definition_file):
                with open(definition_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            return {}
        except Exception:
            return {}

    def load_persona(self, agent_id: str) -> str:
        """Carrega a persona do agente (persona.md)."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            persona_file = os.path.join(agent_dir, "persona.md")
            if os.path.exists(persona_file):
                with open(persona_file, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception:
            return ""

    def save_session(self, agent_id: str, session_data: Dict) -> bool:
        """Salva os dados da sessão (session.json)."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            session_file = os.path.join(agent_dir, "session.json")
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def load_session(self, agent_id: str) -> Dict:
        """Carrega os dados da sessão (session.json)."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            session_file = os.path.join(agent_dir, "session.json")
            if os.path.exists(session_file):
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f) or {}
            return {}
        except Exception:
            return {}

    def save_knowledge(self, agent_id: str, knowledge_data: Dict) -> bool:
        """Salva os dados de conhecimento (knowledge.json)."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            knowledge_file = os.path.join(agent_dir, "knowledge.json")
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def load_knowledge(self, agent_id: str) -> Dict:
        """Carrega os dados de conhecimento (knowledge.json)."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            knowledge_file = os.path.join(agent_dir, "knowledge.json")
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    return json.load(f) or {}
            return {}
        except Exception:
            return {}

    def save_playbook(self, agent_id: str, playbook_data: Dict) -> bool:
        """Salva os dados do playbook (playbook.yaml)."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            playbook_file = os.path.join(agent_dir, "playbook.yaml")
            with open(playbook_file, 'w', encoding='utf-8') as f:
                yaml.dump(playbook_data, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception:
            return False

    def load_playbook(self, agent_id: str) -> Dict:
        """Carrega os dados do playbook (playbook.yaml)."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            playbook_file = os.path.join(agent_dir, "playbook.yaml")
            if os.path.exists(playbook_file):
                with open(playbook_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            return {}
        except Exception:
            return {}

    def append_to_history(self, agent_id: str, history_entry: Dict) -> bool:
        """Adiciona uma entrada ao histórico (history.log) no formato JSON Lines."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            history_file = os.path.join(agent_dir, "history.log")
            with open(history_file, 'a', encoding='utf-8') as f:
                json.dump(history_entry, f, ensure_ascii=False)
                f.write('\n')
            return True
        except Exception:
            return False

    def load_history(self, agent_id: str) -> List[Dict]:
        """Carrega o histórico completo (history.log)."""
        try:
            agent_dir = self._get_agent_dir(agent_id)
            history_file = os.path.join(agent_dir, "history.log")
            if os.path.exists(history_file):
                history = []
                with open(history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                history.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                return history
            return []
        except Exception:
            return []

    def list_agents(self) -> List[str]:
        """
        Lista todos os agentes disponíveis escaneando o diretório agents/.
        """
        try:
            agents_dir = os.path.join(self.base_path, "agents")
            if not os.path.exists(agents_dir):
                return []
            
            # Retornar apenas diretórios (cada um representa um agente)
            agents = []
            for item in os.listdir(agents_dir):
                item_path = os.path.join(agents_dir, item)
                if os.path.isdir(item_path):
                    agents.append(item)
            
            return sorted(agents)
        except Exception:
            return []