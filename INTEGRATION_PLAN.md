# Plano de Integração: .bmad-core + conductor

Este documento descreve o plano de ação faseado para integrar o sistema de metodologia `.bmad-core` com o orquestrador de execução `conductor`.

## Nível de Complexidade: Médio

- **Baixa Complexidade Conceitual:** Os projetos têm responsabilidades bem separadas (Planejamento vs. Execução).
- **Média Complexidade de Implementação:** O desafio principal é construir a "ponte" entre os sistemas: o artefato `ImplementationPlan`.

## Estratégia Central

A integração será feita **alterando o agente `@dev` existente** para que ele possa gerar um plano de implementação estruturado, que será consumido e executado pelo sistema `conductor`. Isso evita a criação de comandos redundantes e torna o agente `@dev` mais flexível e poderoso.

---

## Fase 1: Definição do "Contrato" - O Artefato `ImplementationPlan`

- **Objetivo:** Criar um padrão claro, legível por máquina e humano, para o plano de implementação.
- **Tarefas:**
    1.  **Escolher o Formato:** **YAML** é a escolha ideal pela sua estrutura e legibilidade.
    2.  **Definir a Estrutura:** Criar um arquivo modelo `implementation-plan-template.yaml`.
        ```yaml
        # projects/develop/workspace/implementation-plan-template.yaml
        storyId: "stories/story-015.md"
        description: "Plano para implementar o novo endpoint de cotação de frete."
        
        # Lista de tarefas sequenciais ou paralelas para o Conductor
        tasks:
          - name: "create-test-scenarios"
            description: "Criar os arquivos de teste unitário e de integração para o novo serviço."
            agent: "QuotationReceiptService_Test_Agent" # O worker específico do Conductor
            inputs:
              - "docs/architecture/coding-standards.md"
              - "stories/story-015.md#acceptance-criteria"
            outputs:
              - "src/test/kotlin/.../QuotationReceiptServiceTest.kt"
        
          - name: "implement-service-logic"
            description: "Implementar a lógica de negócio principal no serviço."
            agent: "QuotationReceiptService_Implementation_Agent"
            depends_on: "create-test-scenarios" # Garante a execução sequencial
            inputs:
              - "src/main/kotlin/.../QuotationReceiptService.kt"
              - "stories/story-015.md#business-logic"
            outputs:
              - "src/main/kotlin/.../QuotationReceiptService.kt" # O mesmo arquivo, modificado
        
        # Como validar que o plano foi concluído com sucesso
        validationCriteria:
          - "Todos os testes em QuotationReceiptServiceTest.kt devem passar."
          - "O linter não deve reportar erros."
        ```
- **Esforço:** **Baixo**.
- **Resultado:** Um template claro que servirá como a "API" entre os dois sistemas.

---

## Fase 2: Modificação do Agente `@dev` (O Produtor)

- **Objetivo:** Ensinar o `@dev` a preencher o `ImplementationPlan` em YAML.
- **Tarefas:**
    1.  **Criar uma Nova Tarefa no BMAD:** Adicionar um arquivo em `.bmad-core/tasks/` chamado `create-implementation-plan.md`.
    2.  **Engenharia de Prompt:** O conteúdo deste novo arquivo de tarefa instruirá a IA (`@dev`) a analisar a história e os artefatos do projeto para preencher o template `implementation-plan-template.yaml` e salvar o resultado em um novo arquivo.
    3.  **Atualizar a Persona do `@dev`:** Adicionar a tarefa `create-implementation-plan` às capacidades do agente `dev.md`.
- **Esforço:** **Médio**.
- **Resultado:** O agente `@dev` ganha a capacidade de delegar a execução para o `conductor`.

---

## Fase 3: Adaptação do `conductor` (O Consumidor)

- **Objetivo:** Tornar o `conductor` capaz de entender e executar um `ImplementationPlan`.
- **Tarefas:**
    1.  **Criar o Orquestrador:** Desenvolver um script principal (ex: `run_conductor.py`).
    2.  **Desenvolver o Parser:** O script precisa ler e interpretar o arquivo `plan.yaml`.
    3.  **Implementar a Lógica de Execução:** O script fará um loop pela seção `tasks` do YAML, invocando os `agents` especificados com os `inputs` definidos e gerenciando as dependências (`depends_on`).
- **Esforço:** **Alto**. Esta é a maior parte do trabalho de codificação.
- **Resultado:** Um `conductor` que pode ser invocado com um único comando para executar um plano completo.

---

## Fase 4: Teste End-to-End e Refinamento

- **Objetivo:** Garantir que a integração funciona sem problemas.
- **Tarefas:**
    1.  **Executar o Fluxo Completo:** Desde o pedido ao `@dev` até a execução final pelo `conductor`.
    2.  **Depurar e Iterar:** Ajustar o template YAML, os prompts do `@dev` e a lógica do orquestrador.
    3.  **Documentar o Novo Workflow:** Criar um guia de como usar o novo fluxo integrado.
- **Esforço:** **Médio**.
- **Resultado:** Um sistema integrado, testado e documentado.
