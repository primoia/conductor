import logging


class ContextFilter(logging.Filter):
    """Injeta informações de contexto, como o agent_id, nos registros de log."""

    def __init__(self, agent_id: str = "system"):
        super().__init__()
        self.agent_id = agent_id

    def filter(self, record):
        record.agent_id = self.agent_id
        return True
