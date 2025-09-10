### Plano de Execução: Estágio 14 - Criar o Teste de "Smoke" do Contêiner

#### Contexto Arquitetônico

Temos uma imagem (`Dockerfile`), uma forma de orquestrá-la (`docker-compose.yml`) e um jeito de verificar sua saúde (`healthcheck`). A peça final da nossa fundação DevOps é um "smoke test" — um teste de ponta a ponta que verifica se o ambiente containerizado, como um todo, sobe corretamente e se o serviço principal está minimamente funcional.

#### Propósito Estratégico

O objetivo é criar a primeira e mais importante barreira de qualidade no nosso pipeline de CI/CD. Um smoke test não verifica a lógica de negócios em detalhes, mas responde a uma pergunta crucial: "A aplicação sequer inicia no ambiente de destino?". Ao ter um teste que sobe o `docker-compose`, espera pelo `healthcheck` passar, e faz uma chamada básica, garantimos que qualquer mudança que quebre a configuração do ambiente ou a inicialização do serviço seja detectada imediatamente, muito antes de chegar a um ambiente de produção.

#### Checklist de Execução

- [x] Criar um novo arquivo de teste em `tests/e2e/test_containerized_service.py`.
- [x] Utilizar uma biblioteca como `pytest-docker` ou escrever um script customizado para gerenciar o `docker-compose up -d` e `docker-compose down`.
- [x] O teste deve esperar que o serviço `conductor-service` se torne "saudável" (healthy).
- [x] Após o serviço estar saudável, o teste deve executar uma chamada simples contra ele. (Como ainda não temos uma API, o teste pode executar um comando dentro do contêiner, por exemplo, `docker exec conductor_service python -c "..."` para instanciar o `ConductorService` e chamar `discover_agents()`).
- [x] O teste deve validar que a chamada não falhou e retornou um resultado esperado (mesmo que seja uma lista vazia de agentes, por enquanto).
