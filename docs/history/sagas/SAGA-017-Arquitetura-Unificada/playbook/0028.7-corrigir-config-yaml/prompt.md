# Especificação Técnica e Plano de Execução: 0028.7-corrigir-config-yaml

#### 1. OBJETIVO ESTRATÉGICO (O "PORQUÊ")

Esta tarefa de correção visa fornecer uma configuração `config.yaml` válida para o `ConductorService`, permitindo sua inicialização bem-sucedida e a passagem dos testes containerizados. Isso é crucial para desbloquear a validação do Passo 28 e garantir a estabilidade do ambiente.

#### 2. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")

Você deve modificar o arquivo `config.yaml` na raiz do projeto para incluir a configuração mínima necessária para o `ConductorService`.

**Arquivo 1 (Modificar): `config.yaml`**

O conteúdo do `config.yaml` deve ser atualizado para:

```yaml
storage:
  type: filesystem
  path: .conductor_workspace
tool_plugins: []
```

#### 3. SINAL DE CONCLUSÃO

Responda com: `TASK_COMPLETE`
