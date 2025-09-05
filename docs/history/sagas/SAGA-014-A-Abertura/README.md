# SAGA-014: A Abertura - Preparação para Open Source

## Objetivo

Esta saga detalha o plano estratégico para transformar o projeto "Conductor" de um sistema interno para um projeto Open Source de alta qualidade, pronto para receber contribuições da comunidade. O objetivo é garantir que o projeto seja seguro, bem documentado, organizado e acessível a novos usuários e desenvolvedores.

---

## Fases do Projeto

### Fase 1: Limpeza e Organização do Repositório

O objetivo desta fase é remover arquivos desnecessários, organizar a estrutura e padronizar o código para facilitar a navegação e a compreensão.

*   **Tarefa 1.1: Sanear `.gitignore`**
    *   **Descrição:** Revisar e adicionar entradas ao `.gitignore` para garantir que arquivos de IDE (`.idea/`, `.vscode/`), caches (`__pycache__/`, `.pytest_cache/`), arquivos de ambiente (`.env*`) e outros artefatos locais não sejam versionados.

*   **Tarefa 1.2: Remover Arquivos Temporários e Backups**
    *   **Descrição:** Excluir permanentemente do repositório diretórios como `backups/`, `scripts_backup_.../` e quaisquer outros arquivos que não fazem parte do código-fonte principal.

*   **Tarefa 1.3: Reorganizar Estrutura de Testes**
    *   **Descrição:** Mover todos os scripts de teste que estão no diretório raiz (ex: `test_admin_loop_fix.py`) para dentro do diretório `tests/`, organizando-os em subdiretórios se necessário (ex: `tests/cli/`).

*   **Tarefa 1.4: Padronizar Idioma para Inglês**
    *   **Descrição:** Realizar uma varredura no código-fonte, comentários e documentação para traduzir todo o conteúdo para o inglês. Isso inclui nomes de variáveis, comentários e textos em arquivos `.md`.

*   **Tarefa 1.5: Formalizar Projeto de Exemplo**
    *   **Descrição:** Mover o projeto `desafio-meli` do diretório `templates/` para `examples/` para refletir melhor seu papel como um caso de uso prático. Esta tarefa também servirá como base para, futuramente, adicionar um `README.md` dedicado explicando como o projeto funciona como um showcase para os agentes do Conductor.

### Fase 2: Auditoria de Segurança e Dependências

Esta fase é crítica para garantir que nenhum dado sensível seja exposto e que o projeto seja construído sobre uma base de dependências sólida.

*   **Tarefa 2.1: Varredura e Remoção de Segredos**
    *   **Descrição:** Executar uma busca exaustiva por chaves de API, senhas, tokens, e-mails pessoais, nomes de hosts internos e qualquer outra informação sensível. Substituir por variáveis de ambiente ou placeholders documentados.

*   **Tarefa 2.2: Auditoria de Dependências**
    *   **Descrição:** Revisar `pyproject.toml` para verificar cada dependência. Garantir que todas são necessárias, que suas licenças são compatíveis com a nossa licença Open Source e que não existem dependências de pacotes privados.

### Fase 3: Fundações da Comunidade e Licenciamento

Aqui, criamos os documentos essenciais que definem as "regras do jogo" para a comunidade.

*   **Tarefa 3.1: Criar Arquivo `LICENSE`**
    *   **Descrição:** Adicionar um arquivo `LICENSE` na raiz do projeto. A licença escolhida é a **MIT**.

*   **Tarefa 3.2: Criar Arquivo `CONTRIBUTING.md`**
    *   **Descrição:** Criar um guia detalhado para contribuidores, explicando como configurar o ambiente de desenvolvimento, os padrões de código, como criar uma branch, o fluxo de Pull Request e como rodar os testes.

*   **Tarefa 3.3: Criar Arquivo `CODE_OF_CONDUCT.md`**
    *   **Descrição:** Adotar e adicionar um código de conduta (baseado no Contributor Covenant) para fomentar uma comunidade positiva e inclusiva.

*   **Tarefa 3.4: Criar Templates de Issues e PRs no GitHub**
    *   **Descrição:** Criar templates para reporte de bugs e sugestão de funcionalidades na pasta `.github/ISSUE_TEMPLATE/`. Criar também um template para Pull Requests em `.github/PULL_REQUEST_TEMPLATE.md`.

### Fase 4: Documentação Pública

Esta fase foca em reescrever e criar a documentação com um público externo em mente.

*   **Tarefa 4.1: Reescrita Completa do `README.md`**
    *   **Descrição:** Substituir o `README.md` atual por uma versão completa e profissional, contendo:
        *   Logo (se houver) e badges (build, licença).
        *   Pitch do projeto: O que é e qual problema resolve.
        *   Lista de funcionalidades principais.
        *   Guia de Instalação e "Getting Started".
        *   Exemplos de uso básicos.
        *   Links para a documentação completa e o guia de contribuição.

*   **Tarefa 4.2: Revisar e Adaptar Documentação Existente**
    *   **Descrição:** Revisar todos os arquivos em `docs/`. Adaptar o conteúdo para um público externo, removendo jargões internos. Mover documentos puramente históricos (como as Sagas) para uma subpasta `docs/history/` para não sobrecarregar novos usuários.

*   **Tarefa 4.3: Documentar Arquivos de Configuração**
    *   **Descrição:** Criar um guia em `docs/guides/configuration.md` que explique o propósito e os parâmetros de cada arquivo de configuração em `config/` e seus subdiretórios.

### Fase 5: Polimento Final e Revisão

A última etapa antes do lançamento, focada em garantir a máxima qualidade e consistência.

*   **Tarefa 5.1: Formatação e Linting do Código**
    *   **Descrição:** Executar um formatador de código (ex: `black`) e um linter (ex: `ruff`) em toda a base de código para garantir um estilo consistente.

*   **Tarefa 5.2: Revisão Final do Repositório**
    *   **Descrição:** Realizar uma revisão manual completa do repositório, simulando a experiência de um novo contribuidor que acabou de clonar o projeto. Verificar se a instalação funciona, se os testes rodam e se a documentação é clara.

---

## Conclusão

Ao final desta saga, o projeto "Conductor" estará estruturado como um projeto Open Source exemplar, pronto para ser publicado e para crescer com a ajuda da comunidade.
