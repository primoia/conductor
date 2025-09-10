# tests/e2e/test_containerized_service.py
import subprocess
import time
import pytest
import shutil

# Este teste é complexo e depende de um ambiente externo (Docker).
# A implementação abaixo é uma representação simplificada usando subprocess.
# Uma implementação mais robusta usaria pytest-docker.

def docker_available():
    """Check if Docker and docker compose are available."""
    try:
        # Check if docker is available
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        # Check if docker compose is available
        subprocess.run(["docker", "compose", "--version"], check=True, capture_output=True)
        # Check if Docker daemon is running
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

@pytest.fixture(scope="module")
def docker_services():
    """Fixture para gerenciar o ambiente docker-compose."""
    try:
        print("Subindo o ambiente Docker...")
        # Usar -d para detached mode
        result = subprocess.run(["docker", "compose", "up", "--build", "-d"], check=True, capture_output=True, text=True)
        if result.stderr:
            print(f"Docker compose stderr: {result.stderr}")

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
        subprocess.run(["docker", "compose", "down"], check=True)

@pytest.mark.skipif(not docker_available(), reason="Docker not available or not running")
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