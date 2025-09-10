### Plano de Execução: Estágio 38 - Criar os Artefatos de Definição do `Maestro_Agent`

#### Contexto Arquitetônico

Com a fundação da nova arquitetura estabelecida, agora podemos começar a definir os agentes de sistema que operarão sobre ela. O primeiro e mais importante é o `Maestro_Agent`, o supervisor de projetos que orquestra a execução de playbooks. Esta tarefa consiste em criar os arquivos de artefato iniciais (`definition.yaml`, `persona.md`) para o `Maestro_Agent`.

#### Propósito Estratégico

O objetivo é dar "vida" ao conceito de Maestro que discutimos. Ao criar seus artefatos de definição, nós o tornamos um cidadão de primeira classe no ecossistema Conductor. Esses artefatos servirão como a "fonte da verdade" para o comportamento do Maestro e permitirão que o `ConductorService` o descubra e, eventualmente, o execute, pavimentando o caminho para a automação de alto nível.

#### Checklist de Execução

- [ ] Criar um novo diretório para os agentes de sistema, ex: `.conductor_workspace/agents/Maestro_Agent/`.
- [ ] Dentro do novo diretório, criar o arquivo `definition.yaml`.
- [ ] Preencher o `definition.yaml` com a definição do agente (nome, versão, descrição, etc.).
- [ ] Criar o arquivo `persona.md`.
- [ ] Preencher o `persona.md` com a persona do Maestro, baseando-se no que já temos em `project-management/persona/maestro_persona.md`, mas adaptando-o para ser a instrução direta para o LLM.
