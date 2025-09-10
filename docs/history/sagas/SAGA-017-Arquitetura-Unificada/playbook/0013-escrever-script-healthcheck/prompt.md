# Especificação Técnica e Plano de Execução: 0013-escrever-script-healthcheck

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa introduz a capacidade de autocura e monitoramento ao nosso serviço containerizado. Um `healthcheck` robusto é fundamental para a automação de CI/CD e para a estabilidade de ambientes de produção, permitindo que orquestradores de contêineres gerenciem o ciclo de vida do serviço de forma inteligente.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** O script de health check **DEVE** ser criado em `scripts/docker/healthcheck.py`.
- **Independência:** O script **DEVE** ter o mínimo de dependências possível, idealmente usando apenas a biblioteca padrão do Python para garantir sua leveza.
- **Integração:** A `healthcheck` **DEVE** ser integrada ao `docker-compose.yml` na definição do serviço `conductor-service`.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo e modificar um existente. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `scripts/docker/healthcheck.py`**
```python
#!/usr/bin/env python3
import sys
import http.client

# Este script é um placeholder. Ele irá verificar um endpoint /health
# quando a camada de API for implementada. Por enquanto, ele sempre
# retorna sucesso para permitir que o build do contêiner funcione.

def check_health():
    """
    Verifica a saúde do serviço Conductor.
    No futuro, fará uma requisição HTTP para http://localhost:8000/health.
    """
    # Exemplo de como seria a verificação real:
    # try:
    #     conn = http.client.HTTPConnection("localhost", 8000, timeout=2)
    #     conn.request("GET", "/health")
    #     response = conn.getresponse()
    #     if response.status == 200:
    #         print("Health check OK")
    #         sys.exit(0)
    #     else:
    #         print(f"Health check falhou com status: {response.status}")
    #         sys.exit(1)
    # except Exception as e:
    #     print(f"Health check falhou com erro: {e}")
    #     sys.exit(1)
    # finally:
    #     conn.close()

    print("Health check simulado: OK")
    sys.exit(0)

if __name__ == "__main__":
    check_health()
```

**Arquivo 2 (Modificar): `docker-compose.yml`**
```yaml
version: '3.8'

services:
  conductor-service:
    build:
      context: .
      dockerfile: Dockerfile.service
    container_name: conductor_service
    ports:
      - "8000:8000"
    volumes:
      - ./src:/home/appuser/app/src
      - ./scripts/docker:/home/appuser/app/scripts/docker # Mapear o script
    environment:
      - MONGODB_CONNECTION_STRING=mongodb://mongodb:27017/conductor
    networks:
      - conductor_net
    depends_on:
      - mongodb
    healthcheck:
      test: ["CMD", "python", "scripts/docker/healthcheck.py"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  mongodb:
    image: mongo:5.0
    container_name: mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - conductor_net

networks:
  conductor_net:
    driver: bridge

volumes:
  mongodb_data:
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `healthcheck.py` for criado e o `docker-compose.yml` for modificado exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
