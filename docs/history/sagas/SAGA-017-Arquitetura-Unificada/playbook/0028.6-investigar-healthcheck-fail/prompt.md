# Especificação Técnica e Plano de Execução: 0028.6-investigar-healthcheck-fail

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção visa resolver a falha do `healthcheck` do serviço `conductor_service`, que está impedindo a validação da suíte de testes. Garantir que o ambiente containerizado esteja funcionando corretamente é fundamental para a continuidade do desenvolvimento e para a garantia de qualidade do projeto.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve investigar a causa da falha do `healthcheck` e implementar as correções necessárias.

1.  **Analisar logs do contêiner `conductor_service`:**
    ```bash
    docker compose up --build -d
    docker logs conductor_service
    ```
    Procure por mensagens de erro ou indicações de que o serviço não está inicializando corretamente.

2.  **Modificar `scripts/docker/healthcheck.py`:**
    -   O script atual sempre retorna sucesso. Ele precisa verificar se o `ConductorService` pode ser importado e instanciado. Isso simulará uma verificação básica de que o ambiente Python dentro do contêiner está funcional.
    -   **Conteúdo do `healthcheck.py`:**
        ```python
        #!/usr/bin/env python3
        import sys
        import os

        # Adicionar o diretório raiz do projeto ao sys.path para que o ConductorService possa ser importado
        # Assumindo que o script está em /home/appuser/app/scripts/docker
        project_root = "/home/appuser/app"
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        try:
            from src.core.conductor_service import ConductorService
            # Tentar instanciar o serviço para verificar se as dependências básicas estão ok
            # Nota: Isso pode falhar se config.yaml não for válido ou dependências externas não estiverem prontas
            # Para um healthcheck mais robusto, um endpoint HTTP seria melhor.
            ConductorService()
            print("Health check OK: ConductorService pode ser importado e instanciado.")
            sys.exit(0)
        except Exception as e:
            print(f"Health check FAILED: {e}")
            sys.exit(1)
        ```

3.  **Modificar `Dockerfile.service`:**
    -   Garantir que o `CMD` no `Dockerfile.service` realmente inicie o serviço de alguma forma, mesmo que seja um placeholder que permita a importação do `ConductorService`.
    -   **Conteúdo do `Dockerfile.service` (apenas a linha `CMD`):**
        ```dockerfile
        # ... (conteúdo existente)
        CMD ["python", "-c", "from src.core.conductor_service import ConductorService; ConductorService(); import time; time.sleep(3600)"]
        ```
        Isso fará com que o contêiner fique ativo por uma hora, permitindo que o `healthcheck` seja executado.

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
