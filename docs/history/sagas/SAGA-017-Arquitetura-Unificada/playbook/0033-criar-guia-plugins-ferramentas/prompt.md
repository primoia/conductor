# Especificação Técnica e Plano de Execução: 0033-criar-guia-plugins-ferramentas

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação. Você é um escritor técnico criando um guia para desenvolvedores.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa cria a documentação essencial que capacita os usuários a estender o framework. Um guia claro sobre a criação de plugins é o que transforma uma funcionalidade de "código" em uma capacidade real do "produto", incentivando a adoção e a contribuição da comunidade.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** O guia **DEVE** ser criado em `docs/guides/creating_tool_plugins.md`.
- **Exemplo Completo:** O guia **DEVE** conter um exemplo completo e funcional, desde a criação do arquivo Python até a configuração do `config.yaml`.
- **Aviso de Segurança:** O guia **DEVE** incluir uma seção proeminente sobre as implicações de segurança de carregar código de fontes não confiáveis.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `docs/guides/creating_tool_plugins.md`**
```markdown
# Guia: Criando Plugins de Ferramentas

A arquitetura do Conductor é projetada para ser extensível. Você pode adicionar suas próprias ferramentas customizadas (plugins) sem modificar o código-fonte principal.

## 1. O Conceito

O Conductor possui dois tipos de ferramentas:
-   **Core Tools:** Ferramentas essenciais que vêm com o sistema.
-   **Tool Plugins:** Ferramentas que você cria e registra em um diretório customizado.

## 2. Criando seu Plugin

### Passo 1: Crie um Diretório para o Plugin
Crie um novo diretório em qualquer lugar dentro do seu projeto. Por exemplo:
`custom_tools/`

### Passo 2: Crie o Módulo da Ferramenta
Dentro do seu novo diretório, crie um arquivo Python. O nome do arquivo será o nome do módulo.
`custom_tools/my_api_tools.py`

### Passo 3: Escreva e Exporte suas Ferramentas
Dentro do seu arquivo, escreva suas ferramentas como funções Python. Em seguida, adicione os nomes das funções a uma lista especial chamada `PLUGIN_TOOLS`.

```python
# custom_tools/my_api_tools.py
import requests

def get_weather(city: str) -> str:
    """Busca o clima atual para uma cidade."""
    # (Implementação da chamada de API)
    return f"O clima em {city} é ensolarado."

# A convenção é exportar as ferramentas em uma lista
PLUGIN_TOOLS = [get_weather]
```

## 3. Registrando seu Plugin

O passo final é dizer ao Conductor onde encontrar seu novo plugin. Abra o `config.yaml` e adicione o caminho para o seu diretório de plugin na lista `tool_plugins`.

```yaml
# config.yaml
storage:
  type: filesystem
  path: .conductor_workspace

tool_plugins:
  - custom_tools/
  - other_plugins/another_set_of_tools/
```

Na próxima vez que o Conductor iniciar, ele irá escanear o diretório `custom_tools/`, importar o módulo `my_api_tools`, e a ferramenta `get_weather` estará disponível para qualquer agente que tenha a permissão para usá-la em seu `agent.yaml`.

## 4. Considerações de Segurança

**AVISO IMPORTANTE:** A funcionalidade de plugins carrega e executa código Python dinamicamente.

-   **Confiança:** **NUNCA** adicione um caminho de plugin de uma fonte que você não confia completamente. Fazer isso pode levar à execução de código malicioso.
-   **Escopo:** Como medida de segurança, o Conductor só carregará plugins de diretórios que estejam dentro da pasta do projeto.
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `docs/guides/creating_tool_plugins.md` for criado com o conteúdo exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
