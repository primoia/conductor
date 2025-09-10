### Plano de Execução: Estágio 13 - Escrever Script de Health Check

#### Contexto Arquitetônico

Com nosso ambiente dockerizado definido, precisamos de uma forma automatizada de verificar se o `ConductorService` dentro do contêiner está não apenas rodando, mas também funcional e pronto para aceitar trabalho. Esta tarefa consiste em criar um script de `healthcheck` que pode ser usado pelo Docker para determinar a saúde do serviço.

#### Propósito Estratégico

O objetivo é aumentar a robustez e a resiliência do nosso ambiente. Um `healthcheck` permite que o Docker (ou orquestradores como Kubernetes) gerencie o ciclo de vida do nosso contêiner de forma inteligente. Ele pode reiniciar o contêiner se o serviço travar ou parar de responder. Para o desenvolvimento e CI, ele nos permite esperar até que o serviço esteja totalmente pronto antes de começar a rodar os testes de integração, evitando falhas por "race conditions".

#### Checklist de Execução

- [ ] Criar um diretório `scripts/docker/`.
- [ ] Dentro do novo diretório, criar um arquivo `healthcheck.py`.
- [ ] O script deve tentar se conectar a um futuro endpoint de API `/health` no serviço. Por enquanto, ele pode simular essa verificação.
- [ ] O script deve sair com `exit code 0` se o serviço for considerado saudável.
- [ ] O script deve sair com `exit code 1` se o serviço não estiver saudável.
- [ ] Modificar o `docker-compose.yml` para adicionar uma seção `healthcheck` ao serviço `conductor-service`.
- [ ] A `healthcheck` do Docker Compose deve usar o script `healthcheck.py` para verificar o estado do serviço.
