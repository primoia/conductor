### Plano de Execução: Estágio 23 - Realizar Benchmarking de Performance

#### Contexto Arquitetônico

A nova arquitetura com o `ConductorService` introduz camadas de abstração para aumentar a flexibilidade e a manutenibilidade. No entanto, abstrações podem, por vezes, introduzir uma sobrecarga (overhead) de performance. Esta tarefa consiste em criar e executar um benchmark simples para comparar a performance da nova arquitetura com a antiga.

#### Propósito Estratégico

O objetivo é garantir que os ganhos arquitetônicos não vieram a um custo inaceitável de performance. Ao medir o tempo de inicialização ("cold start") e o tempo de resposta de uma tarefa simples, podemos quantificar qualquer impacto de performance. Isso nos permite tomar decisões informadas e garante que a experiência do usuário não foi degradada, além de estabelecer uma base de performance para futuras otimizações.

#### Checklist de Execução

- [x] Criar um novo diretório `benchmarks/`.
- [x] Criar um script `benchmark_cli.py`.
- [x] O script deve usar o módulo `time` ou `timeit`.
- [x] O script deve ter uma função para executar um comando CLI (como o `test_golden_master.py`) e medir o tempo total de execução.
- [x] Executar o script em um commit *antes* da refatoração para obter a linha de base de performance do sistema legado.
- [x] Executar o script no código *novo* (pós-refatoração).
- [x] Comparar os resultados e documentá-los em um `benchmarks/README.md`.
- [x] O critério de aceitação é que a regressão de performance não seja superior a 10-15%.
