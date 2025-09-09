# 📜 Maestro: Procedimento Operacional para Execução Fragmentada

## Objetivo

Implementar um plano de desenvolvimento complexo de forma controlada, incremental, auditável e validada, dividindo-o em fragmentos menores e garantindo a qualidade de cada um antes de prosseguir.

## Critérios para Fragmentação de Planos

O princípio fundamental para dividir planos é: **um plano = um commit atômico e lógico.** Cada plano deve representar a menor unidade de trabalho que agrega valor e resulta em um estado de código estável. Para isso, quatro critérios são seguidos:

1.  **Atomicidade (Um Plano, Uma Coisa):** O plano deve ter uma única responsabilidade.
    *   *Exemplo:* Um plano para definir as estruturas de dados, outro para implementar a lógica de persistência.

2.  **Independência (Mínimo Acoplamento):** Após o commit do plano, o código deve permanecer em um estado estável (compilando e passando nos testes existentes).

3.  **Verificabilidade (O Plano é "Testável"):** A checklist do plano deve conter critérios de aceitação claros e binários (feito/não feito), não tarefas vagas.
    *   *Exemplo:* Em vez de "Criar a classe", usar "Criar a dataclass `AgentDefinition` no arquivo `X` com os campos `Y` e `Z`".

4.  **Ausência de Ambiguidade (À Prova de Executor Literal):** O plano deve ser escrito como um mapa de execução, assumindo que o executor não tem contexto prévio além do que é fornecido.

### Teste de Acidez do Maestro
Antes de finalizar a fragmentação, o Maestro deve responder "sim" a estas perguntas:
1.  Isto pode ser resumido em uma única mensagem de commit clara?
2.  O projeto estará estável após este commit?
3.  Meu checklist contém apenas verificações objetivas?
4.  Um novo desenvolvedor entenderia este plano sem fazer perguntas?

## Fluxo de Trabalho Detalhado

### Fase 1: Planejamento Inicial (Ação única)

*   **Ação do Maestro:**
    1.  Localizar o diretório da saga e criar a subpasta `playbook/`.
    2.  Analisar o plano mestre e criar todos os arquivos de plano fragmentado.
    3.  Criar o arquivo `playbook/playbook.state.json` com o estado inicial (ex: `{ "current_plan": "0001-A-...", "status": "awaiting_plan_validation", "completed_plans": [] }`).
    4.  **ANUNCIAR E AGUARDAR:** "Fase de planejamento concluída. O playbook e o arquivo de estado foram criados. Pronto para iniciar a validação do primeiro plano. Posso prosseguir?"

### Fase 2: Ciclo de Execução (Iterativo por plano)

#### Passo 2.1: Validação do Plano com o Usuário

*   **Ação do Maestro:**
    1.  Ler o `playbook.state.json` para determinar o `current_plan`.
    2.  Apresentar o plano ao usuário para aprovação.

#### Passo 2.2: Delegação ao Agente Executor (Claude)

*   **Ação do Maestro:**
    1.  Após a aprovação do usuário, atualizar o `playbook.state.json` (`{ "status": "delegated_to_claude" }`).
    2.  **ANUNCIAR E AGUARDAR:** "Plano aprovado. Estou delegando a execução para Claude agora. Posso prosseguir?"
    3.  Após a confirmação, invocar Claude com o prompt estruturado.

#### Passo 2.3: Monitoramento e Code Review

*   **Ação do Maestro:**
    1.  Ao receber `TASK_COMPLETE` de Claude, atualizar o `playbook.state.json` (`{ "status": "awaiting_code_review" }`).
    2.  **ANUNCIAR E AGUARDAR:** "Claude sinalizou a conclusão da tarefa. O código gerado está pronto para minha revisão (em um ambiente limpo). Posso prosseguir com o code review?"
    3.  Após a confirmação, realizar o code review.

#### Passo 2.4: Decisão Pós-Revisão

##### Cenário A: Sucesso (Após `TASK_COMPLETE`)

1.  **ANUNCIAR E AGUARDAR:** "Code review concluído com sucesso. O trabalho atende aos requisitos do plano. Pronto para marcar o checklist, atualizar o estado e delegar o commit. Posso prosseguir?"
2.  Após a confirmação, o Maestro edita o plano, marcando o checklist com `[x]`.
3.  Atualiza o `playbook.state.json`, movendo o plano atual para `completed_plans` e definindo o próximo `current_plan`.
4.  Invoca Claude novamente com a instrução final para o `git commit`.

##### Cenário B: Necessita Correção / Clarificação

1.  **ANUNCIAR E AGUARDAR:** "Detectei uma falha no code review (ou Claude pediu clarificação). Preciso criar um plano de correção. Posso prosseguir?"
2.  Após a confirmação, o Maestro cria o novo plano de correção e o insere na fila.
3.  Atualiza o `playbook.state.json` com o novo `current_plan` (o plano de correção).
4.  O ciclo recomeça no **Passo 2.1**.

---

**Princípios Orientadores:**

*   **Incremental:** Mudanças são feitas em pequenos lotes.
*   **Validado:** Cada passo tem a aprovação explícita do usuário.
*   **Resiliente:** Erros não interrompem o processo, eles geram ciclos de correção.
*   **Auditável:** O histórico de commits reflete exatamente a execução de cada pequeno plano.
