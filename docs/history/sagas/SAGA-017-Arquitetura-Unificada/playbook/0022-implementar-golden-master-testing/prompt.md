# Especificação Técnica e Plano de Execução: 0022-implementar-golden-master-testing

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa fornece a mais alta garantia de que a refatoração não introduziu regressões comportamentais. Ao comparar a saída do novo sistema com um "gabarito" gerado pelo sistema antigo, garantimos a retrocompatibilidade e a consistência da experiência do usuário, que é um requisito crítico da cirurgia de transplante.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** Os scripts e gabaritos **DEVEM** ser localizados em um novo diretório `tests/golden_master/`.
- **Automatização:** O processo de geração do gabarito e de execução da comparação **DEVE** ser automatizado através de scripts para garantir a reprodutibilidade.
- **Comparação Exata:** A comparação **DEVE** ser exata. Qualquer diferença, incluindo espaços em branco ou ordem de saída, deve fazer o teste falhar.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar três novos arquivos. O conteúdo **DEVE** representar a estrutura e a lógica do teste.

**Arquivo 1 (Novo): `tests/golden_master/generate_master.sh`**
```bash
#!/bin/bash
# Este script deve ser executado em um commit ANTES da refatoração da Fase III.
# Ele gera os arquivos .golden que servem como gabarito.

echo "Gerando Golden Master para admin.py..."
poetry run python src/cli/admin.py --agent SomeAgent --input "Teste Admin" > tests/golden_master/admin_output.golden

echo "Gerando Golden Master para agent.py..."
poetry run python src/cli/agent.py --env dev --proj test --agent OtherAgent --input "Teste Agent" > tests/golden_master/agent_output.golden

echo "Geração concluída."
```

**Arquivo 2 (Novo): `tests/golden_master/test_golden_master.py`**
```python
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
```

**Arquivo 3 (Novo): `tests/golden_master/README.md`**
```markdown
# Golden Master Testing

Este diretório contém os testes para garantir a retrocompatibilidade comportamental dos CLIs após a refatoração da SAGA-017.

## Como Funciona

1.  **`generate_master.sh`**: Este script deve ser executado em um commit **anterior** à refatoração da Fase III. Ele executa os CLIs legados e salva sua saída nos arquivos `.golden`.
2.  **`test_golden_master.py`**: Este teste `pytest` executa os **mesmos** comandos no código-fonte **atual** (pós-refatoração) e compara a saída com o conteúdo dos arquivos `.golden`.

O teste falhará se houver qualquer diferença, garantindo que a "cirurgia" não alterou o comportamento externo.
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando os três arquivos (`generate_master.sh`, `test_golden_master.py`, `README.md`) forem criados no diretório `tests/golden_master/` exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
