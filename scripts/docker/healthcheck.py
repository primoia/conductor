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