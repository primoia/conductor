### Plano de Execução: Estágio 28 - Depreciar Formalmente o `config/workspaces.yaml`

#### Contexto Arquitetônico

O arquivo `config/workspaces.yaml` era a "fonte da verdade" na arquitetura legada para a descoberta de projetos. A nova arquitetura, governada pelo `ConductorService`, centraliza toda a configuração no `config.yaml` raiz e utiliza o backend de armazenamento para a descoberta de agentes. Portanto, o `workspaces.yaml` se tornou obsoleto e sua existência agora representa um débito técnico e uma fonte de confusão.

#### Propósito Estratégico

O objetivo é eliminar a ambiguidade e consolidar a fonte de verdade da configuração do sistema. Ao depreciar e remover o uso do `workspaces.yaml`, garantimos que o `config.yaml` seja o único ponto de configuração que um desenvolvedor precisa conhecer. Isso simplifica o modelo mental do sistema e previne bugs onde configurações legadas poderiam interferir no comportamento da nova arquitetura.

#### Checklist de Execução

- [ ] Realizar uma busca global no código-fonte por quaisquer usos restantes do arquivo `config/workspaces.yaml`.
- [ ] Remover o código que lê e processa este arquivo (provavelmente nos CLIs legados, que já foram refatorados, mas uma verificação final é necessária).
- [ ] Renomear o arquivo para `config/workspaces.yaml.DEPRECATED`.
- [ ] Adicionar um comentário no topo do arquivo renomeado explicando que ele não é mais utilizado e que a configuração de armazenamento deve ser feita no `config.yaml` principal.
- [ ] Garantir que todos os testes (unitários, de integração, golden master) continuem passando após a remoção da lógica de leitura.
