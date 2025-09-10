### Plano de Execução: Estágio 28.7 - Corrigir `config.yaml`

#### Contexto Arquitetônico

A investigação do Passo 28.6 revelou que a falha do `healthcheck` e a incapacidade do `ConductorService` de inicializar são causadas por erros de validação de configuração no `config.yaml`. Especificamente, os campos `storage` e `tool_plugins` estão ausentes ou incorretos, o que impede a instanciação do `ConductorService`.

#### Propósito Estratégico

O objetivo é fornecer uma configuração `config.yaml` válida que permita a inicialização bem-sucedida do `ConductorService` e, consequentemente, a passagem do `healthcheck` nos testes containerizados. Isso é fundamental para restaurar a estabilidade da suíte de testes e permitir a validação completa do Passo 28.

#### Checklist de Execução

- [x] Modificar o arquivo `config.yaml` na raiz do projeto.
- [x] Adicionar uma seção `storage` válida, por exemplo, com `type: filesystem` e um `path` para o workspace.
- [x] Adicionar uma seção `tool_plugins` como uma lista vazia ou com caminhos válidos.
- [x] Executar `docker compose up --build -d` para verificar se o ambiente sobe sem erros.
- [x] Executar `poetry run pytest` para confirmar que o `test_service_smoke_run` passa após a correção.
