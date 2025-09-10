#!/bin/bash
# Este script deve ser executado em um commit ANTES da refatoração da Fase III.
# Ele gera os arquivos .golden que servem como gabarito.

echo "Gerando Golden Master para admin.py..."
poetry run python src/cli/admin.py --agent SomeAgent --input "Teste Admin" > tests/golden_master/admin_output.golden

echo "Gerando Golden Master para agent.py..."
poetry run python src/cli/agent.py --env dev --proj test --agent OtherAgent --input "Teste Agent" > tests/golden_master/agent_output.golden

echo "Geração concluída."