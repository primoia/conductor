# src/infrastructure/utils.py

import os
import time
from pathlib import Path

def cleanup_orphan_sessions(workspace_path: str, max_age_hours: int = 24):
    """
    Varre o workspace e remove arquivos session.json órfãos mais antigos que max_age_hours.
    """
    workspace = Path(workspace_path)
    max_age_seconds = max_age_hours * 3600
    now = time.time()

    if not workspace.is_dir():
        return

    print(f"Executando limpeza de sessões órfãs em '{workspace}'...")
    for session_file in workspace.glob("**/session.json"):
        try:
            file_age = now - session_file.stat().st_mtime
            if file_age > max_age_seconds:
                print(f"Removendo sessão órfã: {session_file}")
                session_file.unlink()
        except OSError as e:
            print(f"Erro ao processar o arquivo {session_file}: {e}")