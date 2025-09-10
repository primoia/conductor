# Especificação Técnica e Plano de Execução: 0028.1-refatorar-container

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção remove as dependências restantes do `config/workspaces.yaml` no `src/container.py`, permitindo que a depreciação formal do arquivo prossiga e consolidando o `config.yaml` como a única fonte de verdade da configuração.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve modificar o arquivo `src/container.py` para remover toda a lógica relacionada ao `workspaces.yaml`.

**Arquivo 1 (Modificar): `src/container.py`**

1.  **Remova** o método `load_workspaces_config` por completo.
2.  **Remova** o método `resolve_agent_paths` por completo, pois sua lógica de descoberta de caminhos legada não é mais compatível com a nova arquitetura baseada em `ConductorService`.
3.  **Inspecione** a classe `DIContainer` para remover quaisquer outros atributos ou chamadas relacionadas a `workspaces`.

Após a modificação, o `container.py` não deve mais conter nenhuma referência a `workspaces.yaml`.

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
