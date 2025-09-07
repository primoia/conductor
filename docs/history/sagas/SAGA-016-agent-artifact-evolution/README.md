# SAGA-016: A Nova Arquitetura de Agentes: Definição, Persistência e Extensibilidade

**Status:** Defined

## 1. O Problema: As Limitações da Arquitetura Inicial

A arquitetura inicial de agentes do Conductor, embora funcional, apresentava uma série de desafios arquitetônicos e práticos que limitavam sua escalabilidade, segurança e facilidade de uso. Esta SAGA visa resolver esses problemas de forma definitiva.

Os problemas identificados foram:

1.  **Acoplamento de Definição e Estado:** O uso de um único `state.json` misturava a definição de longo prazo de um agente (sua persona, capacidades) com seu estado de execução de curto prazo (a tarefa atual). Isso tornava a análise e a manutenção difíceis.

2.  **Conflito entre Versionamento e Privacidade:** Armazenar os artefatos dos agentes diretamente no sistema de arquivos, dentro de um repositório Git, criava um conflito insolúvel:
    *   Se os artefatos fossem versionados, o estado dinâmico (memória, playbooks atualizados) contendo informações de projetos privados do usuário seria acidentalmente commitado, criando um grave risco de segurança.
    *   Se os artefatos fossem adicionados ao `.gitignore`, o estado valioso do agente (sua "memória" e "aprendizados") seria perdido e não persistido, derrotando o propósito de um agente que aprende.

3.  **Alta Barreira de Entrada (Onboarding):** A exigência de configurar dependências externas, como um banco de dados (MongoDB), apenas para executar o projeto pela primeira vez, criava uma barreira de entrada significativa para novos usuários e contribuidores do projeto open-source.

4.  **Risco de Inchaço do Framework (Bloat):** A falta de um mecanismo claro para extensibilidade significava que novas funcionalidades, tanto na forma de agentes quanto de ferramentas, teriam que ser adicionadas ao core do projeto, levando a um framework inchado, difícil de manter e com funcionalidades que serviam apenas a um subconjunto de usuários.

## 2. A Arquitetura Proposta: Princípios Fundamentais

Para resolver esses problemas, a nova arquitetura se baseia em quatro princípios fundamentais que promovem separação de interesses, flexibilidade e segurança.

*   **Princípio 1: Separação Clara entre Definição e Estado:** A identidade e o comportamento de um agente (sua *definição*) são tratados de forma separada de sua experiência e contexto de execução (seu *estado*).

*   **Princípio 2: Backend de Persistência Flexível:** O sistema não impõe um método de armazenamento. Ele abstrai a camada de persistência, oferecendo um padrão de "dependência zero" para fácil onboarding e uma opção avançada para escalabilidade.

*   **Princípio 3: Sistema de Ferramentas Extensível (Plugins):** O framework não deve conter todas as ferramentas possíveis. Ele deve fornecer um core essencial e um mecanismo robusto para que os usuários carreguem seus próprios conjuntos de ferramentas customizadas.

*   **Princípio 4: Agentes Não Executam Código, Eles Usam Ferramentas (Tools):** Este é um princípio de segurança e design inegociável. A lógica de um agente reside em sua capacidade de decidir e orquestrar, não em executar código arbitrário. Toda a execução de ações (operações de arquivo, chamadas de API, etc.) é delegada a `Tools` que são seguras, versionadas, testadas e explicitamente permitidas. Isso impede vulnerabilidades de RCE (Remote Code Execution) e mantém uma fronteira clara entre o "cérebro" (agente) e os "músculos" (ferramentas).

## 3. Componentes da Arquitetura

Estes são os componentes detalhados que implementam os princípios acima.

### 3.1. Artefatos do Agente

Cada agente é composto por um conjunto de artefatos, cada um com um propósito claro e um formato adequado.

| Artefato | Formato | Propósito e Justificativa |
| :--- | :--- | :--- |
| **`definition`** | YAML/JSON | **Para a Máquina.** Contém metadados estruturados (`name`, `version`, `tags`, `capabilities`). Usado pelo Orquestrador para **filtragem rápida e programática** de agentes. |
| **`persona`** | Markdown | **Para o Humano e para o LLM.** Documento de texto que define o comportamento e a especialidade do agente. É editado por humanos e lido pelo LLM para **decisão semântica**. |
| **`playbook`** | Markdown | **Para o Humano e para o LLM.** Contém as "lições aprendidas" de forma estruturada. Humanos o editam para adicionar orientação. O LLM o lê para se guiar. A estrutura interna é dividida em `## Best Practices` e `## Anti-Patterns`, com cada entrada possuindo um `ID` único, `Title` e `Description`. Para mais detalhes, veja o [Guia de Referência de Artefatos](./AGENT_ARTIFACTS_REFERENCE.md). |
| **`memory`** | JSON | **Para a Máquina.** É um log de dados estruturados de longo prazo. Permite consultas programáticas sobre o histórico de execuções do agente. Para mais detalhes, veja o [Guia de Referência de Artefatos](./AGENT_ARTIFACTS_REFERENCE.md). |
| **`session`** | JSON | **Para a Máquina.** É um objeto de estado volátil de curto prazo. Permite que o sistema modifique o contexto da tarefa atual de forma atômica e confiável. Para mais detalhes, veja o [Guia de Referência de Artefatos](./AGENT_ARTIFACTS_REFERENCE.md). |

**Exemplo de `playbook.md` Estruturado:**
```markdown
## Best Practices

---
**ID:** BP001
**Title:** Seja Conciso e Direto
**Description:** Responda à pergunta do usuário da forma mais direta possível, evitando preâmbulos desnecessários.

---
**ID:** BP002
**Title:** Ofereça Exemplos Práticos
**Description:** Sempre que explicar um conceito técnico, forneça um pequeno bloco de código ou um exemplo de comando para ilustrar o ponto.

## Anti-Patterns

---
**ID:** AP001
**Title:** Evite Respostas Excessivamente Longas
**Description:** Se uma explicação requer mais de três parágrafos, considere dividi-la em partes ou perguntar ao usuário se ele deseja detalhes adicionais.
---
```

### 3.2. Templates de Agente (A Fonte da Verdade)

*   O repositório Git do Conductor conterá um diretório `_agent_templates/`.
*   Este diretório armazena as "plantas baixas" ou "versões de fábrica" dos agentes essenciais e exemplos. Cada subdiretório contém os artefatos de definição: `agent.yaml`, `persona.md`, e `playbook.md` inicial.
*   **Propósito:** Permitir o versionamento e o code review das definições base dos agentes, garantindo um ponto de partida estável e confiável.

### 3.3. Instâncias de Agente (Os Agentes "Vivos")

*   Um agente em execução, com seu estado completo, é uma **"Instância"**.
*   As instâncias vivem inteiramente no backend de armazenamento configurado (seja no sistema de arquivos local ou no MongoDB).
*   Uma instância é um objeto único que encapsula todos os artefatos de um agente: sua definição, persona, playbook, memória e sessão.

**Exemplo de Instância de Agente no MongoDB:**
```json
// collection: "agents"
{
  "_id": "KotlinEntityCreator",
  "template_version": "2.1.0",
  "definition": { "name": "...", "tags": ["kotlin"] },
  "persona": "Eu sou um especialista em Kotlin...",
  "playbook": {
    "best_practices": "- Sempre use `val`...",
    "anti_patterns": "- Nunca use `FetchType.EAGER`..."
  },
  "memory": [ { "taskId": "...", "summary": "..." } ],
  "session": { "current_task": null }
}
```

### 3.4. O Backend Flexível de Armazenamento

Este é o componente que resolve o problema do onboarding e da escalabilidade. O usuário pode escolher o backend através de um arquivo `config.yaml`.

*   **Modo Padrão: `storage_backend: filesystem`**
    *   **Funcionamento:** O sistema cria e opera dentro de um diretório `.conductor_workspace/` na raiz do projeto, que é automaticamente ignorado pelo Git. Na primeira execução, ele copia os `_agent_templates/` para dentro deste workspace.
    *   **Vantagem:** **Onboarding com dependência zero.** O usuário pode clonar o repositório e executar o projeto imediatamente, sem precisar configurar bancos de dados ou outras dependências.

*   **Modo Avançado: `storage_backend: mongodb`**
    *   **Funcionamento:** O sistema se conecta a uma instância do MongoDB especificada pelo usuário. Todas as operações de leitura e escrita das instâncias de agente ocorrem no banco de dados.
    *   **Vantagem:** **Escalabilidade e Centralização.** Ideal para equipes, ambientes de produção e cenários que exigem que múltiplos processos do Conductor compartilhem o mesmo estado de agentes.

### 3.5. O Sistema de Ferramentas Híbrido (Plugins)

Este componente resolve o problema do inchaço do framework.

*   **Core Tools:** O Conductor vem com um conjunto essencial de ferramentas universais (`file.read`, `shell.run`, etc.), que são parte do código principal.
*   **Custom Tools (Plugins):** O usuário pode desenvolver suas próprias ferramentas em diretórios separados e registrá-los no `config.yaml`:
    ```yaml
    # config.yaml
    tool_plugins:
      - /path/to/my_company_sap_tools/
      - /path/to/my_personal_scripts/
    ```
*   O sistema carrega essas ferramentas customizadas na inicialização. Uma vez carregadas, elas são tratadas de forma idêntica às Core Tools, incluindo o sistema de permissões no `agent.yaml`.

## 4. Fluxos de Trabalho na Nova Arquitetura

### 4.1. Arquitetura e Fluxo do Orquestrador

O Orquestrador é o componente central que impulsiona a execução autônoma de planos. Ele opera como uma máquina de estados que, para cada tarefa em um plano, seleciona e ativa o agente mais adequado. Sua lógica interna segue um fluxo robusto para garantir eficiência e inteligência.

**Entrada:** Um plano de execução (ex: `implementation_plan.yaml`), que contém uma lista de tarefas, suas descrições e dependências.

**O Fluxo de Execução para Cada Tarefa:**

1.  **Análise da Tarefa:** O Orquestrador lê a próxima tarefa do plano, extraindo sua descrição, nome e requisitos (ex: `"Configurar logging estruturado na aplicação"`).

2.  **Fase 1: Filtragem Rápida de Candidatos:**
    *   O Orquestrador consulta o backend de armazenamento para obter os artefatos `definition` de todos os agentes disponíveis.
    *   Ele realiza uma filtragem programática e de baixo custo, selecionando agentes cujo `tags` ou `capabilities` correspondem às palavras-chave e requisitos da tarefa. Isso gera uma lista curta de candidatos potenciais.

3.  **Fase 2: Decisão Semântica com LLM:**
    *   Se a filtragem resultar em múltiplos candidatos, o Orquestrador constrói um prompt para si mesmo.
    *   Este prompt contém a descrição da tarefa e a `persona` de cada agente candidato.
    *   Ele então faz uma chamada a um LLM com a pergunta: `"Qual destes especialistas é o mais qualificado para esta tarefa específica? Justifique."`. A resposta do LLM determina a seleção final.

4.  **Fase 3: Fallback de Criação de Agente:**
    *   Se a Fase 1 não retornar candidatos, ou se a Fase 2 resultar em uma baixa pontuação de confiança, o Orquestrador ativa um fluxo de fallback.
    *   Ele invoca o `AgentCreator_Agent` com a descrição da tarefa original, instruindo-o a criar um novo agente especialista.
    *   **Nota:** O plano de execução pode configurar se este passo requer aprovação humana antes de prosseguir com o agente recém-criado.

5.  **Execução e Monitoramento:**
    *   Com um agente selecionado (ou recém-criado), o Orquestrador o ativa, passando o contexto e as entradas necessárias para a tarefa.
    *   Ele monitora a execução, coleta os artefatos de saída e atualiza o `history` e o `knowledge` do agente no backend de armazenamento após a conclusão bem-sucedida.

6.  **Manuseio de Erros:** Se uma tarefa falhar, o Orquestrador, dependendo da configuração do plano (`stop_on_error`), pode pausar a execução, registrar o erro e aguardar a intervenção humana.

### 4.2. Fluxo de "Afinamento" de um Agente (Meta-Workflow)

Este fluxo permite a melhoria contínua dos agentes:

1.  Um humano inicia uma sessão com um "meta-agente" (ex: `AgentTuner_Agent`).
2.  Este agente possui `Tools` para ler e escrever os artefatos de outros agentes (ex: `get_agent_artifact`, `update_agent_artifact`).
3.  O humano pode pedir para ver a `persona` ou o `playbook` de um agente alvo, sugerir alterações, e o `AgentTuner_Agent` as aplica, salvando-as permanentemente no backend de armazenamento.

## 5. Visão de Evolução Futura

Esta arquitetura abre portas para evoluções futuras:

*   **Busca Semântica de Memória:** Integrar um **Banco de Dados Vetorial** para permitir que os agentes encontrem memórias de tarefas passadas que sejam *semanticamente similares* às atuais, melhorando o aprendizado por contexto.
*   **Ferramenta de Administração de Agentes (Agent Admin Tool):** Construir uma CLI ou UI dedicada para implementar o "Meta-Workflow" de afinamento, facilitando o gerenciamento do ciclo de vida dos agentes.

## 6. Resumo da Solução

A nova arquitetura resolve os problemas iniciais de forma abrangente:

*   **Privacidade e Versionamento:** Resolvidos pela separação de `Templates` (em Git) e `Instâncias` (em um backend separado e não versionado).
*   **Onboarding:** Resolvido pelo backend `filesystem` padrão, que não exige dependências externas.
*   **Inchaço do Framework:** Resolvido pelo sistema de `tool_plugins`, que permite extensibilidade ilimitada sem poluir o core.
*   **Manutenção e Clareza:** Resolvidos pela separação de artefatos com formatos específicos para cada propósito (`definition`, `persona`, `playbook`, `memory`, `session`).