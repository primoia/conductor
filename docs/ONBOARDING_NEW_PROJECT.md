# Guia de Onboarding: Integrando um Novo Projeto ao Framework Maestro

**Versão:** 1.0

**Público-alvo:** Desenvolvedores e Arquitetos

## 1. Introdução

Este guia descreve o processo passo a passo para registrar e configurar um novo projeto de software para ser gerenciado pelo ecossistema de agentes do Framework Maestro. O objetivo é permitir que o `genesis_agent.py` e o `conductor` possam operar de forma segura e contextualizada no seu projeto.

## 2. Pré-requisitos

- O Framework Maestro deve estar clonado e configurado na sua máquina local.
- O projeto que você deseja integrar deve ter um repositório Git e estar acessível no seu sistema de arquivos.

## 3. Passo a Passo

### Passo 1: Criar a Estrutura de Diretórios do Projeto

O Maestro organiza os agentes por ambiente e por projeto. O primeiro passo é criar a hierarquia de pastas que representará seu projeto dentro do framework.

Suponha que seu projeto se chame **`my-new-app`** e você queira começar a trabalhar no ambiente **`develop`**.

1.  Navegue até a pasta `projects/` na raiz do Maestro.
2.  Crie a seguinte estrutura de diretórios:

    ```bash
    # Exemplo de comando a partir da raiz do Maestro
    mkdir -p projects/develop/my-new-app/agents
    ```

*   **Explicação:**
    *   `projects/develop/`: Representa o ambiente de desenvolvimento.
    *   `my-new-app/`: É o diretório específico do seu projeto.
    *   `agents/`: É a pasta que conterá todos os Agentes Especialistas customizados para este projeto e ambiente.

### Passo 2: Criar seu Primeiro Agente Especialista

A melhor maneira de validar a configuração é criando um primeiro agente para o seu projeto. Usaremos o `AgentCreator_Agent` para isso.

1.  Execute o Gênesis no modo de incorporação do `AgentCreator_Agent`:

    ```bash
    python scripts/genesis_agent.py --embody AgentCreator_Agent --repl
    ```

2.  No diálogo com o "Arquiteto Meta", forneça as informações do seu novo agente, especificando o ambiente e o projeto quando solicitado:
    *   **Ambiente:** `develop`
    *   **Projeto:** `my-new-app`
    *   **ID do Agente:** (ex: `MyFirstAgent`)
    *   ...e siga o restante do diálogo de design.

3.  Ao final, o `AgentCreator_Agent` irá criar a estrutura completa do seu novo agente dentro de `projects/develop/my-new-app/agents/MyFirstAgent/`.

### Passo 3: Executar o Agente no Contexto do Projeto

Com seu novo agente criado, você pode agora interagir com ele no contexto do seu projeto.

1.  Para iniciar uma sessão de chat, use o Gênesis, passando o **ID do seu novo agente** e, crucialmente, o **caminho raiz do seu projeto**.

    ```bash
    # Supondo que o caminho para seu projeto seja /path/to/my-new-app
    python scripts/genesis_agent.py --embody MyFirstAgent --project-root /path/to/my-new-app --repl
    ```

2.  Dentro desta sessão, o `MyFirstAgent` terá a capacidade de ler e escrever arquivos (`read_file`, `write_file`) de forma segura dentro de `/path/to/my-new-app`.

## 4. Conclusão

Seu projeto está agora onboarded! Você pode criar quantos agentes especialistas forem necessários para o seu projeto dentro da pasta `agents` correspondente. O motor Gênesis saberá como carregá-los e executá-los no contexto correto, garantindo que as operações de cada agente fiquem contidas no diretório do projeto especificado via `--project-root`.
