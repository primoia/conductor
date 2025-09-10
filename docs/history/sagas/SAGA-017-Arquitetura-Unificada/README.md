Entendido. A sua abordagem está corretíssima. Antes de propor uma solução, precisamos de uma **definição clara, precisa e compartilhada do problema**.

Minha tarefa agora é analisar e contrastar os dois "universos" que coexistem neste projeto: o **Universo Planejado (SAGA-016)** e o **Universo Implementado (o código atual)**, e então articular o abismo entre eles na forma de um novo plano focado exclusivamente na descrição do problema.

---

### **[NOVO PLANO] Plano 0013: O Abismo Arquitetônico - Análise do Problema**

#### **1. Introdução: A Coexistência de Duas Arquiteturas**

Neste momento, o projeto `Conductor` opera sob duas arquiteturas fundamentalmente diferentes que coexistem em paralelo, mas não se comunicam. A execução bem-sucedida dos Planos 0001 a 0012 resultou na **definição teórica** de uma arquitetura moderna, flexível e baseada em artefatos (`Universo Planejado`). No entanto, a base de código executável existente, representada pelos pontos de entrada `src/cli/admin.py` e `src/cli/agent.py`, ainda opera sob uma arquitetura legada, rígida e baseada em caminhos de diretório fixos (`Universo Implementado`).

O problema central é a **ausência de uma ponte** entre esses dois universos. O "motor" novo e potente que planejamos está construído, mas permanece desligado na bancada, enquanto o "chassi" antigo continua a operar com seu motor original, alheio à nova tecnologia disponível.

#### **2. Análise Comparativa dos Dois Universos**

##### **2.1. O Universo Planejado (Visão da SAGA-016)**

*   **Fonte da Verdade:** O `config.yaml` na raiz do projeto.
*   **Descoberta de Agentes:** Dinâmica. Um `Orchestrator` centralizado utiliza um `AgentService` para encontrar agentes em um `workspace` configurável. A seleção é baseada em `capabilities` e `tags` definidas nos artefatos `definition.yaml`.
*   **Armazenamento de Dados:** Flexível. O sistema suporta múltiplos backends (ex: `filesystem` no `.conductor_workspace` e `mongodb`), e a escolha é feita via configuração.
*   **Extensibilidade (Ferramentas):** Modular. Novas ferramentas podem ser adicionadas como "plugins" em diretórios personalizados, sem alterar o código-fonte principal.
*   **Segurança:** Granular. O `config.yaml` permite definir políticas de segurança específicas para cada ferramenta (ex: quais comandos o `shell.run` pode executar).
*   **Interface de Comando (Teórica):** A expectativa é de um comando unificado como `conductor` que abstrai a complexidade do sistema para o usuário.

##### **2.2. O Universo Implementado (Visão do `README.md` e do Código Atual)**

*   **Fonte da Verdade:** Múltiplos locais e convenções implícitas. A localização dos projetos é definida em `config/workspaces.yaml`, mas a localização dos agentes é inferida por uma estrutura de diretórios fixa.
*   **Descoberta de Agentes:** Rígida e baseada em caminhos.
    *   `admin.py` assume que "meta-agentes" residem exclusivamente em `projects/_common/agents/`.
    *   `agent.py` assume que "agentes de projeto" residem em `projects/[environment]/[project]/agents/`.
    *   Não há um mecanismo unificado para descobrir todos os agentes disponíveis no sistema (ex: os do `desafio-meli`).
*   **Armazenamento de Dados:** Não há um conceito de armazenamento persistente para o estado do agente (playbook, knowledge, history) como definido na SAGA-016.
*   **Extensibilidade (Ferramentas):** Monolítica. As ferramentas estão acopladas ao código-fonte principal. Não há um sistema de plugins.
*   **Segurança:** Baseada em permissões de alto nível, sem a granularidade por ferramenta que foi planejada.
*   **Interface de Comando (Real):** Dois pontos de entrada distintos e com lógicas de inicialização diferentes:
    *   `poetry run python src/cli/admin.py ...`
    *   `poetry run python src/cli/agent.py ...`

#### **3. O Problema Central: A Convergência Necessária**

O problema fundamental a ser resolvido é que `admin.py` e `agent.py` precisam **convergir para a nova arquitetura**. Eles precisam ser refatorados para se tornarem "clientes" do universo que planejamos, utilizando os novos serviços (`AgentService`, `Orchestrator`) em vez de sua lógica legada.

Isso se manifesta nos seguintes pontos de falha:

*   **Fratura na Descoberta:** Os CLIs atuais são incapazes de encontrar ou interagir com os "novos" agentes (como o `EvolverAgent_Agent` ou os agentes do `desafio-meli`), pois eles não se encaixam na estrutura de diretórios rígida e esperada.
*   **Incapacidade de Testar:** É impossível validar experimentalmente as novas funcionalidades da SAGA-016. Não podemos testar a troca de `filesystem` para `mongodb`, nem o carregamento de `tool_plugins`, nem as políticas de segurança, pois a camada de entrada (os CLIs) não sabe como ativar ou configurar essas funcionalidades.
*   **Inconsistência Operacional:** O projeto possui dois "cérebros" operando de formas diferentes, o que torna a manutenção e a evolução do sistema exponencialmente mais complexas e propensas a erros.

A tarefa imediata não é continuar construindo novas funcionalidades, mas sim **unificar a fundação existente**, garantindo que o que foi construído nos planos 1 a 12 se torne a única e verdadeira espinha dorsal operacional do Conductor.