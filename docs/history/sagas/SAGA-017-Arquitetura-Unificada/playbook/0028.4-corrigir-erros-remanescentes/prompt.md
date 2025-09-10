# Especificação Técnica e Plano de Execução: 0028.4-corrigir-erros-remanescentes

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção visa eliminar as últimas falhas na suíte de testes, garantindo que o projeto esteja em um estado totalmente funcional e validado. Isso é crucial para a conclusão da depreciação do `workspaces.yaml` e para a continuidade do desenvolvimento.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve implementar as seguintes correções:

1.  **`tests/test_container.py`**: Remover os testes `test_load_workspaces_config_missing_file` e `test_resolve_agent_paths_common`, pois eles testam métodos que não existem mais.

2.  **`tests/e2e/test_containerized_service.py`**: 
    -   Adicionar um `pytest.mark.skipif` para pular o teste se o Docker não estiver rodando ou se `docker compose` não for encontrado no PATH. Isso evita falhas em ambientes sem Docker.
    -   Adicionar um `print` para a saída do `stderr` do `subprocess.run` para depuração, caso o `docker compose up` falhe.

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
