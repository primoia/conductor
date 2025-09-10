### Plano de Execução: Estágio 11 - Criar o `Dockerfile` do Serviço

#### Contexto Arquitetônico

Com o `ConductorService` definido, precisamos de um método padronizado, reprodutível e isolado para executá-lo. Esta tarefa consiste em criar um `Dockerfile` que encapsulará o serviço e todas as suas dependências em uma imagem de contêiner. Utilizaremos uma abordagem de "multi-stage build" para criar uma imagem final que seja enxuta, segura e otimizada para produção, contendo apenas o necessário para a execução do serviço, sem incluir dependências de build ou o código-fonte completo.

#### Propósito Estratégico

O objetivo é tornar o `ConductorService` uma unidade de implantação (deployment unit) portátil e autossuficiente. Um `Dockerfile` bem construído garante que o serviço rode de forma consistente em qualquer ambiente (desenvolvimento local, CI/CD, produção), eliminando a clássica síndrome do "funciona na minha máquina". Este é o primeiro e mais crítico passo para estabelecer uma fundação DevOps sólida para o projeto.

#### Checklist de Execução

- [ ] Na raiz do projeto, criar um novo arquivo chamado `Dockerfile.service`.
- [ ] Definir um primeiro estágio (`builder`) baseado em uma imagem Python oficial (ex: `python:3.10-slim-bullseye`).
- [ ] No estágio `builder`, copiar os arquivos de dependência (`pyproject.toml`, `poetry.lock`) e instalar as dependências usando Poetry.
- [ ] Copiar todo o código-fonte da aplicação para o estágio `builder`.
- [ ] Definir um segundo estágio (`final`) baseado na mesma imagem Python.
- [ ] No estágio `final`, copiar apenas o ambiente virtual com as dependências e o código da pasta `src` do estágio `builder`.
- [ ] Definir um usuário não-root para executar a aplicação.
- [ ] Definir o `CMD` ou `ENTRYPOINT` padrão para iniciar o serviço (mesmo que o serviço ainda não tenha um ponto de entrada executável, podemos definir um placeholder).
