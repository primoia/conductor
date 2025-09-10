# Benchmarking de Performance

Este diretório contém scripts para medir a performance dos CLIs do Conductor.

## Como Usar

1.  **Crie um Agente Mock:** Certifique-se de que um agente simples (ex: `BenchmarkAgent`) exista para que o comando possa ser executado.
2.  **Execute na Versão Antiga:** Faça o checkout para um commit anterior à Fase III e execute:
    ```bash
    python benchmarks/run_benchmark.py
    ```
    Salve os resultados.
3.  **Execute na Versão Nova:** Volte para o commit mais recente e execute o script novamente.
4.  **Compare:** Compare a média dos tempos de execução. O critério de aceitação é que o tempo da versão nova não seja mais do que 10-15% superior ao da versão antiga.

## Resultados (Exemplo)

*   **Versão Legada (Commit X):**
    *   Média: 0.8521 segundos
*   **Versão Refatorada (Commit Y):**
    *   Média: 0.8995 segundos
*   **Conclusão:** Regressão de ~5.5%. **ACEITO**.