# Especificação Técnica e Plano de Execução: 0028.2-corrigir-imports-testes

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção visa restaurar a funcionalidade da suíte de testes legados, corrigindo um `ImportError` causado pela renomeação da interface `IStateRepository`. Isso é essencial para garantir a estabilidade do projeto e permitir a validação contínua das mudanças arquitetônicas.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve modificar os arquivos de teste especificados para corrigir a importação da interface `IStateRepository`.

**Arquivo 1 (Modificar): `tests/test_core.py`**

Localize a linha:
`from src.ports.state_repository import StateRepository`

E altere para:
`from src.ports.state_repository import IStateRepository as StateRepository`

**Arquivo 2 (Modificar): `tests/test_state_management.py`**

Localize a linha:
`from src.ports.state_repository import StateRepository`

E altere para:
`from src.ports.state_repository import IStateRepository as StateRepository`

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
