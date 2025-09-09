# Plano: 0010-J - Orquestração: Lógica de Seleção de Agentes

## Contexto

Com a fundação e os meta-agentes definidos, precisamos de um orquestrador inteligente para selecioná-los. Este plano foca em implementar a lógica de seleção de agentes descrita no plano mestre: **Análise -> Filtragem Rápida -> Decisão Semântica**.

O objetivo é criar uma classe `Orchestrator` que, dada uma tarefa, consegue encontrar o agente mais adequado no workspace.

## Checklist de Verificação

- [ ] Criar um novo arquivo `src/core/orchestrator.py`.
- [ ] Em `orchestrator.py`, criar a classe `Orchestrator`.
- [ ] O `Orchestrator` deve receber o `AgentService` e talvez o `AgentCreator_Agent` (para o fallback) em seu construtor.
- [ ] Implementar um método `find_best_agent_for_task(task_description: str) -> AgentDefinition`.
- [ ] O método `find_best_agent_for_task` deve:
    1. Analisar a `task_description` para extrair capacidades ou tags chave (ex: "monitoramento", "refatorar").
    2. Usar o `AgentService` (ou diretamente o repositório) para listar todas as `AgentDefinition` disponíveis no workspace.
    3. **Filtragem Rápida:** Filtrar a lista de agentes, mantendo apenas aqueles cujas `tags` ou `capabilities` no `definition.yaml` correspondem às extraídas da tarefa.
    4. **Decisão Semântica:** Para os agentes restantes, ler suas `persona.md` e usar um prompt para o LLM decidir qual persona é a mais adequada para a tarefa.
    5. Retornar a `AgentDefinition` do agente escolhido.
- [ ] Adicionar um mecanismo de fallback: se nenhum agente for encontrado, o orquestrador deve ser capaz de invocar o `AgentCreator_Agent` para criar um novo. (Isso pode ser simplificado na primeira versão).
