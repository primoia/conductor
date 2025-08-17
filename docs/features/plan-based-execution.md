# Execução Baseada em Planos

Para automação e tarefas complexas de CI/CD, o framework utiliza o **Conductor Engine**, um executor não-interativo que segue um plano de implementação.

**Como funciona:**
1.  **Plano YAML**: Você define uma sequência de tarefas em um arquivo `.yaml`.
2.  **Executor**: O `run_conductor.py` lê este arquivo.
3.  **Orquestração**: O Conductor invoca os agentes necessários na ordem definida, passando os outputs de uma etapa como inputs para a próxima.

Isso permite a automação de cadeias de tarefas, como: `Analisar Requisito` -> `Gerar Código` -> `Criar Testes` -> `Documentar`.
