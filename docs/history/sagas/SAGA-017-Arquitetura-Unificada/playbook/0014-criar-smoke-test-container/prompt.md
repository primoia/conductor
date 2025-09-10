# Especificação Técnica e Plano de Execução: 0014-criar-smoke-test-container

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa cria a primeira rede de segurança para nosso pipeline de integração contínua. Um smoke test automatizado que valida o ambiente containerizado como um todo garante que mudanças que quebrem a configuração de base ou a inicialização do serviço sejam detectadas instantaneamente, prevenindo falhas catastróficas em estágios posteriores do deployment.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** O teste **DEVE** ser criado em `tests/e2e/test_containerized_service.py`.
- **Framework:** O teste **DEVE** ser escrito usando `pytest`.
- **Interação:** Como ainda não há uma API, a interação com o serviço dentro do contêiner **DEVE** ser feita via `docker exec`.
- **Independência:** O teste **DEVE** gerenciar o ciclo de vida do ambiente (`docker-compose up` e `down`), garantindo que ele não deixe processos órfãos.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo e modificar um existente para adicionar uma dependência de teste. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Modificar): `pyproject.toml`**
```toml
# ... (seção [tool.poetry.dependencies] existente) ...

[tool.poetry.group.dev.dependencies]
# ... (outras dependências de dev existentes) ...
pytest-docker = "^2.0.1"
```

**Arquivo 2 (Novo): `tests/e2e/test_containerized_service.py`**
```python
# tests/e2e/test_containerized_service.py
import subprocess
import time
import pytest

# Este teste é complexo e depende de um ambiente externo (Docker).
# A implementação abaixo é uma representação simplificada usando subprocess.
# Uma implementação mais robusta usaria pytest-docker.

@pytest.fixture(scope="module")
def docker_services():
    """Fixture para gerenciar o ambiente docker-compose."""
    try:
        print("Subindo o ambiente Docker...")
        # Usar -d para detached mode
        subprocess.run(["docker-compose", "up", "--build", "-d"], check=True)

        # Esperar o healthcheck passar
        print("Aguardando o serviço se tornar saudável...")
        for _ in range(30): # Timeout de 60 segundos
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Health.Status}}", "conductor_service"],
                capture_output=True, text=True
            )
            if result.stdout.strip() == "healthy":
                print("Serviço está saudável!")
                break
            time.sleep(2)
        else:
            pytest.fail("Timeout: Serviço não se tornou saudável a tempo.")
        
        yield
    finally:
        print("Derrubando o ambiente Docker...")
        subprocess.run(["docker-compose", "down"], check=True)

def test_service_smoke_run(docker_services):
    """
    Executa um comando simples dentro do contêiner para verificar
    se o ConductorService pode ser instanciado e uma função chamada.
    """
    print("Executando o smoke test...")
    # Comando para instanciar o serviço e chamar um método
    command_to_run = (
        "from src.core.conductor_service import ConductorService; "
        "service = ConductorService(); "
        "agents = service.discover_agents(); "
        "print(f'Agentes encontrados: {len(agents)}')"
    )
    
    result = subprocess.run(
        ["docker", "exec", "conductor_service", "python", "-c", command_to_run],
        capture_output=True,
        text=True,
        check=True
    )
    
    print(f"Saída do contêiner: {result.stdout}")
    assert "Agentes encontrados" in result.stdout
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `pyproject.toml` for modificado e o `test_containerized_service.py` for criado exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
