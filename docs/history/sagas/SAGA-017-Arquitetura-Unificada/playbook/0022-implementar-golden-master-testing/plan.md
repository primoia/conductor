### Plano de Execução: Estágio 22 - Implementar o "Golden Master Testing"

#### Contexto Arquitetônico

A "cirurgia" da Fase III substituiu o motor do carro, mas manteve o chassi. Agora, precisamos de uma prova objetiva de que o carro ainda se comporta da mesma maneira do ponto de vista do motorista. O "Golden Master Testing" é uma técnica onde capturamos a saída de um sistema legado (o "golden master") e a usamos como um gabarito para validar a nova implementação.

#### Propósito Estratégico

O objetivo é garantir a **retrocompatibilidade comportamental** e prevenir regressões sutis. Enquanto os testes de integração validam que o novo sistema funciona, este teste valida que ele produz *exatamente o mesmo resultado* que o sistema antigo para um conjunto de entradas fixas. Isso nos dá a mais alta confiança de que a refatoração foi um sucesso e não alterou o comportamento esperado pelos usuários.

#### Checklist de Execução

- [ ] Criar um diretório de teste, ex: `tests/golden_master/`.
- [ ] Criar um subdiretório com uma versão do código *antes* da refatoração da Fase III.
- [ ] Criar um script `generate_golden_master.sh` que executa uma série de comandos (`admin.py` e `agent.py`) contra o código antigo e salva a saída de cada comando em arquivos `.golden`.
- [ ] Criar um script de teste `test_golden_master.py`.
- [ ] O teste deve executar os mesmos comandos contra o código *novo* (refatorado).
- [ ] O teste deve então comparar a saída do código novo com o conteúdo dos arquivos `.golden` correspondentes.
- [ ] O teste falha se houver qualquer diferença, por menor que seja.
