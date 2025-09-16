# 📋 Task: Integration with Primoia Log-Watcher

**Project**: conductor  
**Technology**: Python  
**Priority**: High  
**Estimate**: 2-3 days  

## 🎯 Objective

Integrate the `conductor` service with the **Primoia Log-Watcher** (the central observability hub of the Primoia ecosystem) to centralize logs and improve the observability of the orchestration and automation system.

## 📊 Expected Benefits

- ✅ **Centralized Observability** - Orchestration logs in one place
- ✅ **Intelligent Analysis** - AI to detect problems in workflows
- ✅ **Noise Reduction** - Automatic grouping of similar logs
- ✅ **Proactive Diagnostics** - Alerts before they affect automations
- ✅ **Unified Metrics** - Consolidated view of workflow health
- ✅ **Execution Tracking** - Monitoring of pipelines and automations

## 🏗️ Current Architecture

```
┌─────────────────────────┐
│  conductor              │
│  (Python)               │
│                         │
│  - Orchestrator         │
│  - Scripts              │
│  - Templates            │
│  - Projects             │
│  - Local logs           │
└─────────────────────────┘
```

## 🎯 Target Architecture

```
┌─────────────────────────┐    Logs    ┌─────────────────────┐
│  conductor              │ ──────────► │  Primoia Log-Watcher│
│  (Python)               │            │  (Central Hub)      │
│                         │            │                     │
│  - Orchestrator         │            │  - AI Analysis      │
│  - Scripts              │            │  - Grouping         │
│  - Templates            │            │  - Alerts           │
│  - Projects             │            │  - Dashboard        │
│  - PrimoiaLogClient     │            │  - Workflow Tracking│
└─────────────────────────┘            └─────────────────────┘
```

## 📋 Implementation Tasks

### Phase 1: Base Configuration (1 day)

#### 1.1 Dependency Configuration
- [ ] Add dependencies to `requirements.txt` (if it exists) or create it
  ```txt
  httpx==0.25.2
  python-dotenv==1.0.0
  structlog==23.2.0
  ```

#### 1.2 Property Configuration
- [ ] Create file `config/logging_config.py`
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

#### 1.3 Environment Variables
- [ ] Create file `.env.example`
  ```env
  PRIMOIA_LOG_URL=http://primoia-log-watcher:8000
  PRIMOIA_LOG_API_KEY=conductor-key-2024
  APP_VERSION=1.0.0
  HOSTNAME=conductor-001
  ```

### Phase 2: Client Implementation (1 day)

#### 2.1 Create PrimoiaLogClient
- [ ] Create class `utils/primoia_log_client.py`
- [ ] Implement method `send_log(level: str, message: str, context: dict = None)`
- [ ] Configure httpx with timeout and retry
- [ ] Implement fallback to local logs in case of failure

#### 2.2 Logger Configuration
- [ ] Create `utils/logger.py` with PrimoiaLogClient integration
- [ ] Configure structlog for structured logs
- [ ] Implement logging middleware for scripts

### Phase 3: Integration into Main Modules (0.5 day)

#### 3.1 Orchestrator Logs
- [ ] **orchestrator/**: Workflow execution logs
- [ ] **scripts/**: Script execution logs
- [ ] **templates/**: Template generation logs

#### 3.2 Projects Logs
- [ ] **projects/**: Project operation logs
- [ ] **stories/**: Story management logs
- [ ] **demo/**: Demo logs

### Phase 4: Performance and Monitoring Logs (0.5 day)

#### 4.1 Performance Logs
- [ ] Workflow execution time logs
- [ ] Resource usage logs (CPU, memory)
- [ ] Cache hit/miss logs

#### 4.2 Monitoring Logs
- [ ] Health check logs
- [ ] System metrics logs
- [ ] Alert and notification logs

## 🔧 Technical Implementation

### File Structure

```
conductor/
├── config/
│   └── logging_config.py          # Logging configuration
├── utils/
│   ├── primoia_log_client.py      # Client for Primoia Log-Watcher
│   └── logger.py                  # Integrated logger
├── orchestrator/
│   └── [existing files]           # (modified)
├── scripts/
│   └── [existing files]           # (modified)
├── templates/
│   └── [existing files]           # (modified)
├── projects/
│   └── [existing files]           # (modified)
└── .env.example                   # Example environment variables
```

### Implementation Example

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
        """Sends a log to the Primoia Log-Watcher"""
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
            # Fallback to local log
            print(f"Error sending log to Primoia: {e}")
            print(f"Log data: {json.dumps(log_data, indent=2)}")
    
    async def send_batch_logs(self, logs: List[Dict[str, Any]]) -> None:
        """Sends multiple logs in a batch"""
        if not self.config.enabled:
            return
        
        try:
            response = await self.client.post(
                f"{self.config.base_url}/api/v1/ingestion/logs/batch",
                json={"logs": logs}
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Error sending batch logs to Primoia: {e}")
    
    async def close(self):
        """Closes the HTTP client"""
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
        
        # Configure structlog
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
        """Processor to send logs to Primoia"""
        asyncio.create_task(
            self.primoia_client.send_log(
                level=method_name.upper(),
                message=event_dict.get("event", ""),
                context=event_dict
            )
        )
        return event_dict
    
    def get_logger(self, name: str = None):
        """Returns a configured logger"""
        return structlog.get_logger(name)
    
    async def close(self):
        """Closes the logger and client"""
        await self.primoia_client.close()

# Global instance
config = PrimoiaLogConfig()
logger_instance = PrimoiaLogger(config)

def get_logger(name: str = None):
    """Helper function to get a logger"""
    return logger_instance.get_logger(name)
```

#### Example usage in scripts
```python
# scripts/example_script.py
from utils.logger import get_logger

logger = get_logger(__name__)

async def main():
    logger.info("Starting script execution", 
                script_name="example_script",
                version="1.0.0")
    
    try:
        # Execute script logic
        logger.info("Executing main logic")
        
        # Simulate operation
        await asyncio.sleep(1)
        
        logger.info("Script executed successfully",
                   execution_time=1.0,
                   status="completed")
    
    except Exception as e:
        logger.error("Error in script execution",
                    error=str(e),
                    error_type=type(e).__name__,
                    status="failed")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

## 🧪 Tests

### Unit Tests
- [ ] Tests for `PrimoiaLogClient`
- [ ] Tests for `PrimoiaLogger`
- [ ] Configuration tests

### Integration Tests
- [ ] Test sending logs to Primoia Log-Watcher
- [ ] Test fallback in case of failure
- [ ] Performance test (should not impact execution)

### Scenario Tests
- [ ] Workflow execution logs
- [ ] Error and exception logs
- [ ] Orchestration operation logs
- [ ] Performance logs

## 📊 Success Metrics

### Functional
- [ ] 100% of workflow executions logged
- [ ] 100% of orchestration operations logged
- [ ] 0% log loss in case of Primoia Log-Watcher failure

### Performance
- [ ] Impact < 50ms on workflow execution time
- [ ] Additional memory usage < 100MB
- [ ] Functional fallback in case of unavailability

### Observability
- [ ] Structured and standardized logs
- [ ] Rich context for workflow analysis
- [ ] Integration with Primoia Log-Watcher metrics

## 🔐 Security

### Configuration
- [ ] API key in environment variables
- [ ] Do not expose sensitive information in logs
- [ ] Input validation to prevent injection

### Sensitive Data
- [ ] Do not log passwords or tokens
- [ ] Mask personal data (email, phone)
- [ ] Log only project IDs, not complete data

## 🚀 Deploy

### Development
- [ ] Configure Primoia Log-Watcher locally
- [ ] Test full integration
- [ ] Validate logs in the dashboard

### Production
- [ ] Configure Primoia Log-Watcher URL in production
- [ ] Configure production API key
- [ ] Monitor log sending metrics

## 📚 Documentation

### For Developers
- [ ] Document how to use the `PrimoiaLogger`
- [ ] Document available configurations
- [ ] Document troubleshooting

### For Operations
- [ ] Document log monitoring
- [ ] Document alert configuration
- [ ] Document emergency procedures

## 🎯 Acceptance Criteria

### Functional
- [ ] All workflows log execution and results
- [ ] Critical orchestration operations are logged
- [ ] Logs include sufficient context for analysis
- [ ] Fallback works in case of failure

### Technical
- [ ] Code follows Python project standards
- [ ] Tests cover main scenarios
- [ ] Performance is not significantly impacted
- [ ] Configuration is flexible and secure

### Operational
- [ ] Logs appear in Primoia Log-Watcher
- [ ] Metrics are collected correctly
- [ ] Alerts work as expected
- [ ] Documentation is complete

## 📅 Schedule

| Phase | Duration | Deliverables |
|------|---------|-------------|
| Phase 1 | 1 day | Base configuration, dependencies |
| Phase 2 | 1 day | PrimoiaLogClient implemented |
| Phase 3 | 0.5 day | Integration into main modules |
| Phase 4 | 0.5 day | Performance and monitoring logs |
| **Total** | **3 days** | **Full integration** |

## 🔗 References

- [Primoia Log-Watcher Integration Guide](../../primoia-log-watcher/INTEGRATION_GUIDE.md)
- [Integration Examples](../../primoia-log-watcher/examples/integration-examples.md)
- [Primoia Log-Watcher API Documentation](http://localhost:8000/docs)
- [httpx Documentation](https://www.python-httpx.org/)
- [structlog Documentation](https://www.structlog.org/)

---

**Status**: 📋 **Planned**  
**Assignee**: [To be defined]  
**Start Date**: [To be defined]  
**End Date**: [To be defined]