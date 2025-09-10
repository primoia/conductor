### Plano de Execução: Estágio 28.6 - Investigar e Corrigir Falha do `healthcheck`

#### Contexto Arquitetônico

A validação do Passo 28 continua bloqueada por uma falha no `tests/e2e/test_containerized_service.py::test_service_smoke_run`. O erro `Failed: Timeout: Serviço não se tornou saudável a tempo.` indica que o `conductor_service` não está passando no `healthcheck` dentro do tempo limite, ou o serviço não está realmente saudável.

#### Propósito Estratégico

O objetivo é diagnosticar e resolver a causa raiz da falha do `healthcheck` para restaurar a funcionalidade dos testes containerizados. Isso é crucial para que a validação do Passo 28 possa ser concluída com sucesso e para garantir que o ambiente Docker esteja funcionando conforme o esperado.

#### Checklist de Execução

- [ ] **Investigar o `healthcheck`:**
    -   Executar `docker compose up --build -d` manualmente.
    -   Monitorar o status do `healthcheck` com `docker ps` e `docker inspect <container_id>`. 
    -   Verificar os logs do contêiner `conductor_service` (`docker logs conductor_service`) para ver o que o script `healthcheck.py` está imprimindo e se há erros na inicialização do serviço.
- [ ] **Analisar `healthcheck.py`:**
    -   Revisar o script `scripts/docker/healthcheck.py`. Atualmente, ele sempre retorna sucesso. Isso pode ser um problema se o serviço não estiver realmente pronto.
    -   O `ConductorService` ainda não tem um endpoint `/health`. O `healthcheck.py` precisa ser ajustado para verificar algo que indique que o serviço está *realmente* pronto, ou o `ConductorService` precisa expor um endpoint simples.
- [ ] **Corrigir a causa raiz:**
    -   Se o problema for o `healthcheck.py` sempre retornando sucesso, mas o serviço não estar pronto, o `healthcheck.py` precisa ser mais inteligente (ex: tentar importar `ConductorService` e instanciá-lo, ou esperar por uma mensagem específica nos logs).
    -   Se o problema for o serviço não iniciar, corrigir o `Dockerfile.service` ou o `CMD` no `docker-compose.yml`.
- [ ] **Executar `poetry run pytest`:**
    -   Confirmar que o `test_service_smoke_run` passa após as correções.
