# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0012-L

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo deste plano é garantir a **Higiene e a Robustez** do ambiente de trabalho do Conductor no modo `filesystem`. Processos podem ser interrompidos de forma anormal, deixando para trás arquivos de sessão (`session.json`) que se tornam "lixo digital". Este plano implementa um "serviço de limpeza" automático que remove esses arquivos órfãos durante a inicialização, prevenindo comportamentos inesperados e garantindo que cada nova execução do Conductor comece em um estado limpo e previsível.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITO NÃO FUNCIONAL)**
- **Execução Condicional:** A rotina de limpeza **DEVE** ser executada apenas quando o backend de armazenamento configurado for `filesystem`. Ela não deve ser executada para o backend `mongodb`, que já lida com a expiração de sessões através de TTL.
- **Execução na Inicialização:** A função de limpeza **DEVE** ser chamada no início do processo de inicialização da aplicação (ex: no `cli/admin.py`), antes que qualquer outra operação seja realizada.
- **Segurança:** A função **DEVE** apagar apenas arquivos com o nome exato `session.json` e que atendam ao critério de tempo, para evitar a exclusão acidental de outros arquivos.
- **Localização:** A função de limpeza **DEVE** residir em um módulo de utilitários de infraestrutura, como `src/infrastructure/utils.py`.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**

**1. Criar o arquivo `src/infrastructure/utils.py` (ou adicionar a um existente):**
```python
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

```

**2. Integrar a chamada de limpeza na inicialização da aplicação:**
```python
# Em src/cli/admin.py (ou no ponto de entrada principal)

from src.config import ConfigManager
from src.infrastructure.utils import cleanup_orphan_sessions

def main():
    # ... (carregamento da configuração)
    config = ConfigManager.load_config()
    storage_config = config.get('storage_backend', {})

    if storage_config.get('type') == 'filesystem':
        workspace_path = storage_config.get('workspace_path')
        if workspace_path:
            cleanup_orphan_sessions(workspace_path)

    # ... (resto da lógica da aplicação)

if __name__ == "__main__":
    main()

```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
- A função `cleanup_orphan_sessions` foi implementada corretamente em um arquivo de utilitários de infraestrutura.
- A função é chamada condicionalmente na inicialização da aplicação, apenas para o backend `filesystem`.
- A função remove com sucesso os arquivos `session.json` que são mais antigos que o limite de tempo definido.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
