### Plano de Execução: Estágio 28 - Depreciar Formalmente o `config/workspaces.yaml`

#### Contexto Arquitetônico

O arquivo `config/workspaces.yaml` era a "fonte da verdade" na arquitetura legada para a descoberta de projetos. A nova arquitetura, governada pelo `ConductorService`, centraliza toda a configuração no `config.yaml` raiz e utiliza o backend de armazenamento para a descoberta de agentes. Portanto, o `workspaces.yaml` se tornou obsoleto e sua existência agora representa um débito técnico e uma fonte de confusão.

#### Propósito Estratégico

O objetivo é eliminar a ambiguidade e consolidar a fonte de verdade da configuração do sistema. Ao depreciar e remover o uso do `workspaces.yaml`, garantimos que o `config.yaml` seja o único ponto de configuração que um desenvolvedor precisa conhecer. Isso simplifica o modelo mental do sistema e previne bugs onde configurações legadas poderiam interferir no comportamento da nova arquitetura.

#### Checklist de Execução

- [x] **Passo 1: Busca por Usos (Verificação)**
    - [x] Executar `grep -r "workspaces.yaml" .` para confirmar que não há usos em código-fonte ativo.
- [x] **Passo 2: Renomear o Arquivo**
    - [x] Executar `mv config/workspaces.yaml config/workspaces.yaml.DEPRECATED`.
- [x] **Passo 3: Adicionar o Aviso de Depreciação**
    - [x] Modificar `config/workspaces.yaml.DEPRECATED` para incluir o aviso.
- [x] **Passo 4: Validar a Estabilidade**
    - [x] Executar `poetry run pytest` para confirmar que a suíte de testes completa passa com sucesso.
