#!/usr/bin/env python3
import sys
import os

# Adicionar o diretório raiz do projeto ao sys.path para que o ConductorService possa ser importado
# Assumindo que o script está em /home/appuser/app/scripts/docker
project_root = "/home/appuser/app"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Healthcheck básico: verifica estrutura de arquivos e Python
    project_root = "/home/appuser/app"

    # Verificar se estrutura de arquivos existe
    required_paths = [
        f"{project_root}/config.yaml",
        f"{project_root}/src",
        f"{project_root}/src/core"
    ]

    for path in required_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required path not found: {path}")

    # Teste básico de Python
    import json
    test_data = {"test": True}
    json.dumps(test_data)

    print("Health check OK: Container structure and Python working.")
    sys.exit(0)
except Exception as e:
    print(f"Health check FAILED: {e}")
    sys.exit(1)