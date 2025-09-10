# tests/golden_master/test_golden_master.py
import subprocess
import pytest
from pathlib import Path

# Obter o diretório do golden master
GOLDEN_MASTER_DIR = Path(__file__).parent
LEGACY_COMMANDS = [
    {
        "name": "admin_cli",
        "command": ["poetry", "run", "python", "src/cli/admin.py", "--agent", "SomeAgent", "--input", "Teste Admin"],
        "golden_file": GOLDEN_MASTER_DIR / "admin_output.golden"
    },
    {
        "name": "agent_cli",
        "command": ["poetry", "run", "python", "src/cli/agent.py", "--env", "dev", "--proj", "test", "--agent", "OtherAgent", "--input", "Teste Agent"],
        "golden_file": GOLDEN_MASTER_DIR / "agent_output.golden"
    }
]

@pytest.mark.parametrize("test_case", LEGACY_COMMANDS)
def test_cli_behavior_remains_unchanged(test_case):
    """
    Executa um comando no código refatorado e compara sua saída com o gabarito .golden.
    """
    # Presume que os arquivos .golden já foram gerados
    if not test_case["golden_file"].exists():
        pytest.skip(f"Arquivo Golden Master não encontrado: {test_case['golden_file']}")

    # Executar o comando no código atual (pós-refatoração)
    result = subprocess.run(test_case["command"], capture_output=True, text=True, check=True)
    current_output = result.stdout

    # Ler o gabarito
    golden_output = test_case["golden_file"].read_text()

    # Comparar
    assert current_output == golden_output