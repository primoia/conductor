# 📋 Tarefa: Integração com Primoia Log-Watcher

**Projeto**: conductor  
**Tecnologia**: Python  
**Prioridade**: Alta  
**Estimativa**: 2-3 dias  

## 🎯 Objetivo

Integrar o serviço `conductor` com o **Primoia Log-Watcher** (hub central de observabilidade do ecossistema Primoia) para centralizar logs e melhorar a observabilidade do sistema de orquestração e automação.

## 📊 Benefícios Esperados

- ✅ **Observabilidade Centralizada** - Logs de orquestração em um só lugar
- ✅ **Análise Inteligente** - IA para detectar problemas em workflows
- ✅ **Redução de Ruído** - Agrupamento automático de logs similares
- ✅ **Diagnóstico Proativo** - Alertas antes que afetem automações
- ✅ **Métricas Unificadas** - Visão consolidada da saúde dos workflows
- ✅ **Rastreamento de Execução** - Monitoramento de pipelines e automações

## 🏗️ Arquitetura Atual

```
┌─────────────────────────┐
│  conductor              │
│  (Python)               │
│                         │
│  - Orchestrator         │
│  - Scripts              │
│  - Templates            │
│  - Projects             │
│  - Logs locais          │
└─────────────────────────┘
```

## 🎯 Arquitetura Alvo

```
┌─────────────────────────┐    Logs    ┌─────────────────────┐
│  conductor              │ ──────────► │  Primoia Log-Watcher│
│  (Python)               │            │  (Hub Central)      │
│                         │            │                     │
│  - Orchestrator         │            │  - Análise IA       │
│  - Scripts              │            │  - Agrupamento      │
│  - Templates            │            │  - Alertas          │
│  - Projects             │            │  - Dashboard        │
│  - PrimoiaLogClient     │            │  - Workflow Tracking│
└─────────────────────────┘            └─────────────────────┘
```

## 📋 Tarefas de Implementação

### Fase 1: Configuração Base (1 dia)

#### 1.1 Configuração de Dependências
- [ ] Adicionar dependências no `requirements.txt` (se existir) ou criar
  ```txt
  httpx==0.25.2
  python-dotenv==1.0.0
  structlog==23.2.0
  ```

#### 1.2 Configuração de Propriedades
- [ ] Criar arquivo `config/logging_config.py`
  ```python
  import os
  from dataclasses import dataclass
  from typing import Optional
  from dotenv import load_dotenv
  load_dotenv()
  
  @dataclass
  class PrimoiaLogConfig:
      enabled: bool = True
      api_key: str = os.getenv("PRIMOIA_LOG_API_KEY", "conductor-key-2024")
      base_url: str = os.getenv("PRIMOIA_LOG_URL", "http://localhost:8000")
      service_name: str = "conductor"
      service_type: str = "orchestration"
      service_version: str = os.getenv("APP_VERSION", "1.0.0")
      service_instance_id: str = os.getenv("HOSTNAME", "conductor-001")
  ```

#### 1.3 Variáveis de Ambiente
- [ ] Criar arquivo `.env.example`
  ```env
  PRIMOIA_LOG_URL=http://primoia-log-watcher:8000
  PRIMOIA_LOG_API_KEY=conductor-key-2024
  APP_VERSION=1.0.0
  HOSTNAME=conductor-001
  ```

### Fase 2: Implementação do Cliente (1 dia)

#### 2.1 Criar PrimoiaLogClient
- [ ] Criar classe `utils/primoia_log_client.py`
- [ ] Implementar método `send_log(level: str, message: str, context: dict = None)`
- [ ] Configurar httpx com timeout e retry
- [ ] Implementar fallback para logs locais em caso de falha

#### 2.2 Configuração do Logger
- [ ] Criar `utils/logger.py` com integração ao PrimoiaLogClient
- [ ] Configurar structlog para logs estruturados
- [ ] Implementar middleware de logging para scripts

### Fase 3: Integração nos Módulos Principais (0.5 dia)

#### 3.1 Logs de Orchestrator
- [ ] **orchestrator/**: Logs de execução de workflows
- [ ] **scripts/**: Logs de execução de scripts
- [ ] **templates/**: Logs de geração de templates

#### 3.2 Logs de Projects
- [ ] **projects/**: Logs de operações em projetos
- [ ] **stories/**: Logs de gerenciamento de histórias
- [ ] **demo/**: Logs de demonstrações

### Fase 4: Logs de Performance e Monitoramento (0.5 dia)

#### 4.1 Logs de Performance
- [ ] Logs de tempo de execução de workflows
- [ ] Logs de uso de recursos (CPU, memória)
- [ ] Logs de cache hits/misses

#### 4.2 Logs de Monitoramento
- [ ] Logs de health checks
- [ ] Logs de métricas de sistema
- [ ] Logs de alertas e notificações

## 🔧 Implementação Técnica

### Estrutura de Arquivos

```
conductor/
├── config/
│   └── logging_config.py          # Configuração de logging
├── utils/
│   ├── primoia_log_client.py      # Cliente para Primoia Log-Watcher
│   └── logger.py                  # Logger integrado
├── orchestrator/
│   └── [arquivos existentes]      # (modificados)
├── scripts/
│   └── [arquivos existentes]      # (modificados)
├── templates/
│   └── [arquivos existentes]      # (modificados)
├── projects/
│   └── [arquivos existentes]      # (modificados)
└── .env.example                   # Exemplo de variáveis de ambiente
```

### Exemplo de Implementação

#### primoia_log_client.py
```python
import httpx
import json
import socket
from datetime import datetime
from typing import Dict, Any, Optional, List
from config.logging_config import PrimoiaLogConfig

class PrimoiaLogClient:
    def __init__(self, config: PrimoiaLogConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def send_log(
        self, 
        level: str, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Envia log para o Primoia Log-Watcher"""
        if not self.config.enabled:
            return
        
        log_data = {
            "service_name": self.config.service_name,
            "service_type": self.config.service_type,
            "service_version": self.config.service_version,
            "service_instance_id": self.config.service_instance_id,
            "level": level,
            "message": message,
            "environment": os.getenv("ENVIRONMENT", "dev"),
            "timestamp": datetime.utcnow().isoformat(),
            "host": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname())
        }
        
        if context:
            log_data.update(context)
        
        try:
            response = await self.client.post(
                f"{self.config.base_url}/api/v1/ingestion/logs/single",
                json=log_data
            )
            response.raise_for_status()
        except Exception as e:
            # Fallback para log local
            print(f"Erro ao enviar log para Primoia: {e}")
            print(f"Log data: {json.dumps(log_data, indent=2)}")
    
    async def send_batch_logs(self, logs: List[Dict[str, Any]]) -> None:
        """Envia múltiplos logs em lote"""
        if not self.config.enabled:
            return
        
        try:
            response = await self.client.post(
                f"{self.config.base_url}/api/v1/ingestion/logs/batch",
                json={"logs": logs}
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Erro ao enviar logs em lote para Primoia: {e}")
    
    async def close(self):
        """Fecha o cliente HTTP"""
        await self.client.aclose()
```

#### logger.py
```python
import structlog
import asyncio
from typing import Dict, Any
from utils.primoia_log_client import PrimoiaLogClient
from config.logging_config import PrimoiaLogConfig

class PrimoiaLogger:
    def __init__(self, config: PrimoiaLogConfig):
        self.config = config
        self.primoia_client = PrimoiaLogClient(config)
        
        # Configurar structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                self._primoia_processor,
                structlog.dev.ConsoleRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    def _primoia_processor(self, logger, method_name, event_dict):
        """Processador para enviar logs para Primoia"""
        asyncio.create_task(
            self.primoia_client.send_log(
                level=method_name.upper(),
                message=event_dict.get("event", ""),
                context=event_dict
            )
        )
        return event_dict
    
    def get_logger(self, name: str = None):
        """Retorna logger configurado"""
        return structlog.get_logger(name)
    
    async def close(self):
        """Fecha o logger e cliente"""
        await self.primoia_client.close()

# Instância global
config = PrimoiaLogConfig()
logger_instance = PrimoiaLogger(config)

def get_logger(name: str = None):
    """Função helper para obter logger"""
    return logger_instance.get_logger(name)
```

#### Exemplo de uso em scripts
```python
# scripts/example_script.py
from utils.logger import get_logger

logger = get_logger(__name__)

async def main():
    logger.info("Iniciando execução do script", 
                script_name="example_script",
                version="1.0.0")
    
    try:
        # Executar lógica do script
        logger.info("Executando lógica principal")
        
        # Simular operação
        await asyncio.sleep(1)
        
        logger.info("Script executado com sucesso",
                   execution_time=1.0,
                   status="completed")
    
    except Exception as e:
        logger.error("Erro na execução do script",
                    error=str(e),
                    error_type=type(e).__name__,
                    status="failed")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Testes

### Testes Unitários
- [ ] Testes do `PrimoiaLogClient`
- [ ] Testes do `PrimoiaLogger`
- [ ] Testes de configuração

### Testes de Integração
- [ ] Teste de envio de logs para Primoia Log-Watcher
- [ ] Teste de fallback em caso de falha
- [ ] Teste de performance (não deve impactar execução)

### Testes de Cenários
- [ ] Logs de execução de workflows
- [ ] Logs de erros e exceções
- [ ] Logs de operações de orquestração
- [ ] Logs de performance

## 📊 Métricas de Sucesso

### Funcionais
- [ ] 100% das execuções de workflows logadas
- [ ] 100% das operações de orquestração logadas
- [ ] 0% de perda de logs em caso de falha do Primoia Log-Watcher

### Performance
- [ ] Impacto < 50ms no tempo de execução dos workflows
- [ ] Uso de memória adicional < 100MB
- [ ] Fallback funcional em caso de indisponibilidade

### Observabilidade
- [ ] Logs estruturados e padronizados
- [ ] Contexto rico para análise de workflows
- [ ] Integração com métricas do Primoia Log-Watcher

## 🔐 Segurança

### Configuração
- [ ] API key em variáveis de ambiente
- [ ] Não expor informações sensíveis nos logs
- [ ] Validação de entrada para evitar injection

### Dados Sensíveis
- [ ] Não logar senhas ou tokens
- [ ] Mascarar dados pessoais (email, telefone)
- [ ] Logar apenas IDs de projetos, não dados completos

## 🚀 Deploy

### Desenvolvimento
- [ ] Configurar Primoia Log-Watcher local
- [ ] Testar integração completa
- [ ] Validar logs no dashboard

### Produção
- [ ] Configurar URL do Primoia Log-Watcher em produção
- [ ] Configurar API key de produção
- [ ] Monitorar métricas de envio de logs

## 📚 Documentação

### Para Desenvolvedores
- [ ] Documentar como usar o `PrimoiaLogger`
- [ ] Documentar configurações disponíveis
- [ ] Documentar troubleshooting

### Para Operações
- [ ] Documentar monitoramento de logs
- [ ] Documentar configuração de alertas
- [ ] Documentar procedimentos de emergência

## 🎯 Critérios de Aceitação

### Funcionais
- [ ] Todos os workflows logam execução e resultado
- [ ] Operações de orquestração críticas são logadas
- [ ] Logs incluem contexto suficiente para análise
- [ ] Fallback funciona em caso de falha

### Técnicos
- [ ] Código segue padrões do projeto Python
- [ ] Testes cobrem cenários principais
- [ ] Performance não é impactada significativamente
- [ ] Configuração é flexível e segura

### Operacionais
- [ ] Logs aparecem no Primoia Log-Watcher
- [ ] Métricas são coletadas corretamente
- [ ] Alertas funcionam conforme esperado
- [ ] Documentação está completa

## 📅 Cronograma

| Fase | Duração | Entregáveis |
|------|---------|-------------|
| Fase 1 | 1 dia | Configuração base, dependências |
| Fase 2 | 1 dia | PrimoiaLogClient implementado |
| Fase 3 | 0.5 dia | Integração nos módulos principais |
| Fase 4 | 0.5 dia | Logs de performance e monitoramento |
| **Total** | **3 dias** | **Integração completa** |

## 🔗 Referências

- [Guia de Integração Primoia Log-Watcher](../../primoia-log-watcher/INTEGRATION_GUIDE.md)
- [Exemplos de Integração](../../primoia-log-watcher/examples/integration-examples.md)
- [Documentação da API Primoia Log-Watcher](http://localhost:8000/docs)
- [Documentação do httpx](https://www.python-httpx.org/)
- [Documentação do structlog](https://www.structlog.org/)

---

**Status**: 📋 **Planejado**  
**Responsável**: [A definir]  
**Data de Início**: [A definir]  
**Data de Conclusão**: [A definir]
