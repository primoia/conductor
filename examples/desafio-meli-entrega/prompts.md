# Prompts Chave do Projeto

Este arquivo documenta os prompts e as conversas que guiaram as decisões de arquitetura e implementação deste projeto, conforme solicitado pelo briefing do desafio.

---

### 1. Definição da Stack e Arquitetura Inicial

**Prompt:**
> "Esse é o objetivo do teste do Meli, penso que posso usar o koltin ou python. Como é uma API profissional precisamos fazer ser muito boa, que tal comecar a estruturar um plano? que acha de fazer uma um API de koltin com swaguer, ou python? A IA manja mais de python e eu manjo mais de kotlin. pensei em criar uma API em koltin e um projeto teste e2e em python? mas vc é meu planejador, o que sugere?"

**Resultado:**
Esta conversa levou à decisão fundamental de usar **Python com FastAPI** devido à sua velocidade de desenvolvimento, documentação automática com Swagger UI, e um ecossistema de testes unificado com `pytest`. Também estabeleceu a primeira versão da nossa arquitetura de camadas (API, Serviços, Repositório) e o plano de ação inicial.

---

### 2. Estabelecimento do Processo de "Sagas"

**Prompt:**
> "Nao gostaria de pensar em APIs e nem produto ainda, que acha montarmos um plano agora documentado e formal para a concepsao do no projeto, talvez projetar até um hello world no container [...], que tal um estrutura de pastas auto incrementais, 001-project, 002-algo.. dentro do docs como se fosse sagas?"

**Resultado:**
Este prompt foi crucial para definir nosso **processo de desenvolvimento incremental**. A ideia das "Sagas de Arquitetura" nasceu aqui, estabelecendo o fluxo de trabalho onde o Arquiteto (Gemini) planeja e documenta formalmente cada marco, e o Implementador (Claude) executa com base nesse blueprint.

---

### 3. Introdução da Observabilidade e Logging Estruturado

**Prompt:**
> "certo, quero impressionar mas nao complicar demais, o que sugere? o que seria facil e portavel? newrealic papertrails ou coisa simples, penseo com cuidado"

**Resultado:**
Esta pergunta elevou o nível do projeto. A discussão levou à decisão de não acoplar a aplicação a nenhuma ferramenta específica, mas sim adotar a melhor prática de **logging estruturado (JSON) para `stdout`**. Isso tornou nossa aplicação "pronta para produção" e demonstrou um entendimento de arquiteturas "cloud-native", onde a aplicação é agnóstica em relação ao ambiente de execução.

---
