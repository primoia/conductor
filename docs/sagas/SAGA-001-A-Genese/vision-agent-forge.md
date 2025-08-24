# Visão Arquitetural: A Forja de Agentes (Agent Forge)

Este documento descreve a visão para a interface humana do ecossistema Conductor. A "Forja de Agentes" é concebida como um software de gerenciamento, potencialmente um projeto separado, que serve como o portal principal para o Arquiteto Humano interagir, comandar e evoluir a força de trabalho de agentes de IA.

## O Problema: A Complexidade da Gestão de Agentes

Um sistema com centenas de agentes autônomos, cada um com seu próprio estado, histórico e persona, é poderoso, mas corre o risco de se tornar impossível de gerenciar através de arquivos de configuração e linhas de comando. A criação de um novo agente é um ato de design de alta importância, não um mero script.

## A Solução: Gamificação como Interface

A Forja de Agentes resolve este problema aplicando uma metáfora de **RPG (Role-Playing Game)** ao ciclo de vida dos agentes. Este paradigma transforma a complexidade em conceitos intuitivos e engajadores.

*   **Agentes como Personagens:** Em vez de configurações, os agentes são "personagens" com Classes, Atributos, Habilidades e Níveis.
*   **Criação como uma Jornada:** A criação de um agente é um "wizard" interativo, um diálogo com a IA.
*   **Gestão como uma Guilda:** O usuário gerencia seu "roster" de agentes como o líder de uma guilda, monitorando seu progresso e desempenho.

## O Ciclo de Vida na Forja

A interação do usuário com um agente se divide em três grandes fases dentro da Forja:

1.  **A Forja (Criação):** Um wizard guiado permite ao usuário projetar um novo agente, definindo sua Classe (ex: Guardião de Testes), Atributos (ex: qual LLM usar, nível de resiliência) e Persona, com a ajuda de IAs que atuam como "consultores" de design em tempo real.

2.  **O Salão da Guilda (Gestão):** Um dashboard central exibe todos os agentes, seus status atuais, métricas de desempenho e permite ao usuário atribuir tarefas ou inspecionar seus perfis.

3.  **O Perfil (Jornada e Evolução):** Cada agente possui uma "ficha de personagem" detalhada, onde o usuário pode ver seu histórico completo de "missões" (tarefas), as "lições" que aprendeu (padrões a evitar), e gastar "XP" para "subir de nível", aprimorando seus atributos e habilidades ao longo do tempo.

## Ponto de Conexão Crítico: A Análise de Impacto

A ponte conceitual entre a Forja de Agentes (frontend) e o Conductor (backend) é a funcionalidade de **Análise de Impacto**.

*   **Funcionalidade na Forja:** Durante a criação de um agente, o usuário define seu domínio (ex: o arquivo `PaymentService.kt`). Um botão **[Analisar Vínculos]** aciona uma IA para analisar este arquivo.
*   **Interface para o Usuário:** A Forja exibe um mapa visual das dependências do arquivo e sugere permissões (ACLs) e agentes colaboradores, ajudando o humano a entender a complexidade do novo agente.
*   **Conexão com o Backend:** O resultado desta análise **alimenta diretamente o Grafo de Dependências** do Conductor. É este grafo que o "Orquestrador Condicional" do backend usa para determinar quais agentes devem ser ativados quando um arquivo é modificado.

Em suma, a Forja de Agentes não é apenas uma interface bonita; ela é uma ferramenta interativa para a **construção e manutenção do mapa de inteligência do sistema**, tornando o complexo processo de mapeamento de dependências uma atividade orgânica e integrada ao fluxo de trabalho.

## Funcionalidades Avançadas

A visão da Forja também inclui capacidades de alto nível, como o **"Laboratório de Testes A/B"**, onde o Arquiteto Humano pode colocar diferentes agentes para competir na mesma tarefa, analisando métricas de custo, latência e qualidade para determinar a configuração ótima, e então aplicar esse aprendizado a toda a "guilda" com um clique.
