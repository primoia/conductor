# SAGA-007: Refatoração da Documentação de Avaliação

**Status:** Concluída

## Descrição

Esta saga representa a execução de uma refatoração na documentação do projeto para adotar um modelo mais robusto e escalável, separando a documentação canônica da documentação histórica.

## Principais Ações

1.  **Promoção de Conteúdo:** O conteúdo do "Procedimento Operacional Padrão de Avaliação", que residia na `SAGA-004`, foi movido e promovido para um guia permanente.
    -   **Nova Localização Canônica:** [`/docs/guides/AGENT_EVALUATION_PROCESS.md`](../../docs/guides/AGENT_EVALUATION_PROCESS.md)

2.  **Correção de Informação:** O novo guia foi atualizado para refletir o estado real do script `admin.py`, documentando seu modo não-interativo e os problemas conhecidos.

3.  **Arquivamento:** A `SAGA-004-A-Avaliacao` foi movida para o diretório `_archive/`, pois foi totalmente substituída por esta saga e pelo novo guia permanente.
