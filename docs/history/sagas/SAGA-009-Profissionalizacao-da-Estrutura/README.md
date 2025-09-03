# SAGA 009: A Profissionalização da Estrutura do Projeto

**Autor:** Primo (Gemini)
**Status:** Planejado

## 1. Missão

Esta saga marca a transição do projeto `conductor` de um conjunto de scripts funcionais para uma aplicação Python com uma estrutura de código profissional, coesa e escalável. A desorganização do diretório `scripts/` será resolvida, e uma nova estrutura inspirada em padrões de mercado (conforme validado no projeto de referência `desafio-meli-entrega`) será implementada.

## 2. Justificativa

Com a evolução do `conductor`, a complexidade cresceu. A separação de responsabilidades (CLI, core, avaliação, etc.) não está refletida na estrutura de arquivos, dificultando a manutenção, a testabilidade e a entrada de novos contribuidores.

Esta refatoração irá:
*   **Aumentar a Coesão:** Agrupar módulos por funcionalidade.
*   **Reduzir o Acoplamento:** Desacoplar a interface da linha de comando da lógica de negócio principal.
*   **Melhorar a Manutenibilidade:** Facilitar a localização e modificação de código.
*   **Alinhar com Padrões:** Adotar uma estrutura de projeto Python reconhecida e profissional.

## 3. Plano de Execução

O plano detalhado para esta refatoração está documentado no seguinte artefato, que servirá como blueprint para a IA implementadora:

➡️ **[Plano de Refatoração Detalhado](./REFACTOR_PLAN.md)**
