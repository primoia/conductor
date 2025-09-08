# Glossário da Nova Arquitetura

Aqui está um glossário detalhado da função de cada arquivo e conceito em nosso plano final.

## Estrutura de Arquivos e Diretórios

*   `_agent_templates/`
    *   **Função:** Diretório versionado em Git que contém as "plantas baixas" dos agentes. É a fonte da verdade para as definições base de cada agente que acompanha o Conductor. Cada subdiretório representa um agente e contém sua `definition.yaml`, `persona.md` e `playbook.yaml` iniciais.

*   `.conductor_workspace/`
    *   **Função:** Diretório de trabalho local, não versionado (deve estar no `.gitignore`). É o backend de armazenamento padrão (`filesystem`). Contém as instâncias "vivas" dos agentes, com suas memórias, sessões e playbooks modificados. Garante uma experiência de "dependência zero" para novos usuários.

*   `config.yaml`
    *   **Função:** Arquivo de configuração principal do Conductor, localizado na raiz do projeto. É aqui que o usuário define qual `storage_backend` usar (`filesystem` ou `mongodb`) e onde registra os `tool_plugins` customizados.

*   `.../agents/<AgentName>/definition.yaml`
    *   **Função:** A identidade de uma instância de agente. Contém metadados estruturados como nome, versão, `tags` e, crucialmente, a lista de `allowed_tools`. É usado pelo Orquestrador para filtragem rápida.

*   `.../agents/<AgentName>/persona.md`
    *   **Função:** O "manual de comportamento" do agente. É um documento em Markdown que descreve o estilo, o tom e as diretrizes operacionais que o LLM deve seguir.

*   `.../agents/<AgentName>/playbook.yaml`
    *   **Função:** O "manual de conhecimento" incremental do agente. Contém as seções `best_practices` e `anti_patterns` em formato YAML estruturado, que são atualizadas para refletir as "lições aprendidas", guiando o agente para tomar decisões melhores no futuro.

*   `.../agents/<AgentName>/knowledge.json`
    *   **Função:** A memória semântica do agente. É um arquivo JSON estruturado que armazena o conhecimento do agente sobre os artefatos que ele gerencia, incluindo resumos, propósitos e metadados de arquivos.

*   `.../agents/<AgentName>/history.log`
    *   **Função:** A memória episódica do agente. É um arquivo no formato JSON Lines que armazena um log imutável de todas as tarefas executadas, seus parâmetros, resultados e commits Git associados.

*   `.../agents/<AgentName>/session.json`
    *   **Função:** A memória de curto prazo do agente. É um arquivo JSON que armazena o estado volátil da tarefa atualmente em execução. É descartado ou arquivado após a conclusão da tarefa.

## Conceitos e Parâmetros Chave

*   **Template de Agente (Agent Template)**
    *   **Definição:** A "planta baixa" de um agente, localizada em `_agent_templates/`. É uma definição estática e versionada.

*   **Instância de Agente (Agent Instance)**
    *   **Definição:** Um agente "vivo" e completo, com estado, que reside no backend de armazenamento. É criado a partir de um Template e evolui com o uso.

*   **Backend de Armazenamento (Storage Backend)**
    *   **Definição:** A camada de persistência configurável (`filesystem` ou `mongodb`) onde as Instâncias de Agente são armazenadas.

*   **Ferramentas do Core (Core Tools)**
    *   **Definição:** O conjunto de ferramentas essenciais e universais que vêm incluídas no framework Conductor.

*   **Ferramentas Customizadas (Custom Tools / Plugins)**
    *   **Definição:** Ferramentas desenvolvidas pelo usuário e carregadas no Conductor através da configuração `tool_plugins` no `config.yaml`. Permitem estender as capacidades do Conductor de forma segura e modular.
