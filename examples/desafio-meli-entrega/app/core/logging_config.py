import json
import logging
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Formatador customizado que produz logs em formato JSON estruturado.
    
    Este formatador cria logs estruturados que podem ser facilmente
    processados por sistemas de observabilidade e análise de logs.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o registro de log como JSON.
        
        Args:
            record: Registro de log a ser formatado
            
        Returns:
            String JSON com os dados estruturados do log
        """
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Adiciona informacoes de excecao se presentes
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def configure_logging() -> None:
    """
    Configura o sistema de logging da aplicacao com formato JSON estruturado.
    
    Configura um logger que escreve para stdout no formato JSON,
    facilitando integração com sistemas de observabilidade.
    """
    # Remove handlers existentes para evitar duplicacao
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Cria handler para stdout com formatador JSON
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    # Configura o logger raiz
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    # Define o nivel para o logger do uvicorn para reduzir verbosidade
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
