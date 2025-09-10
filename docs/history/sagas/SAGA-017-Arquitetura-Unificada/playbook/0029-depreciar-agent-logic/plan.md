### Plano de Execução: Estágio 29 - Depreciar Formalmente `src/core/agent_logic.py`

#### Contexto Arquitetônico

Após a "cirurgia" da Fase III, o `AgentLogic` não é mais utilizado por nenhum código de produção. No entanto, ele ainda existe no código-fonte. Antes de removê-lo em definitivo, a prática recomendada de engenharia de software é marcá-lo formalmente como "depreciado".

#### Propósito Estratégico

O objetivo é comunicar de forma clara e explícita a outros desenvolvedores (e a ferramentas de análise estática) que este componente está obsoleto e não deve ser usado em nenhum novo código. A utilização de um `DeprecationWarning` é um mecanismo padrão em Python que ajuda a garantir uma transição suave, prevenindo que o código legado seja acidentalmente reintroduzido enquanto se aguarda sua remoção completa.

#### Checklist de Execução

- [ ] Abrir o arquivo `src/core/agent_logic.py`.
- [ ] Importar o módulo `warnings`.
- [ ] No `__init__` da classe `AgentLogic`, adicionar uma chamada para `warnings.warn` com uma mensagem clara, indicando que a classe está depreciada e que `AgentExecutor` e `ConductorService` devem ser usados em seu lugar.
- [ ] Atualizar o docstring da classe para também incluir um aviso de depreciação.
