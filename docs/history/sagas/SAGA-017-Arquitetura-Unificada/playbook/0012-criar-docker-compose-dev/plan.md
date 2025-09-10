### Plano de Execução: Estágio 12 - Criar o `docker-compose.yml` de Desenvolvimento

#### Contexto Arquitetônico

Temos um `Dockerfile` para construir a imagem do nosso serviço. Agora, precisamos de uma forma fácil e declarativa de rodar esta imagem junto com suas dependências de desenvolvimento, como o MongoDB. Esta tarefa consiste em criar um arquivo `docker-compose.yml` que define o ambiente de desenvolvimento completo, orquestrando o `ConductorService` e o banco de dados.

#### Propósito Estratégico

O objetivo é simplificar radicalmente o "onboarding" de desenvolvedores e a execução de testes de integração. Com um único comando (`docker-compose up`), qualquer desenvolvedor poderá ter o ambiente completo da nova arquitetura rodando localmente, com o serviço e o banco de dados já conectados e prontos para uso. Isso garante um ambiente de desenvolvimento consistente para toda a equipe e serve como a base para os testes de integração automatizados que virão a seguir.

#### Checklist de Execução

- [ ] Na raiz do projeto, criar um novo arquivo chamado `docker-compose.yml`.
- [ ] Definir a versão do compose (ex: `3.8`).
- [ ] Definir um serviço para o `conductor-service`, especificando que ele deve ser construído a partir do `Dockerfile.service`.
- [ ] Mapear um volume para a pasta `src` para permitir o "hot-reloading" do código durante o desenvolvimento.
- [ ] Definir um serviço para o `mongodb`, usando uma imagem oficial do MongoDB (ex: `mongo:5.0`).
- [ ] Configurar uma rede customizada para que os serviços possam se comunicar pelo nome (`conductor-service`, `mongodb`).
- [ ] Passar as variáveis de ambiente necessárias, como a string de conexão do MongoDB, para o `conductor-service`.
