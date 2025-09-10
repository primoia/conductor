# Especificação Técnica e Plano de Execução: 0031-atualizar-readme-principal

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa garante que a documentação mais visível do projeto (`README.md`) reflita com precisão a nova arquitetura unificada. Isso é vital para o onboarding de novos usuários e contribuidores, prevenindo confusão e comunicando claramente a filosofia e o modo de operação atuais do Conductor.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Clareza e Concisão:** As mudanças devem ser claras, concisas e focadas nos aspectos práticos de como usar o sistema agora.
- **Foco na Configuração:** A nova seção de uso **DEVE** enfatizar a importância do `config.yaml` como o ponto de partida.
- **Manter Exemplos:** Os exemplos de linha de comando para `admin.py` e `agent.py` **DEVEM** ser mantidos para familiaridade, mas o texto ao redor deve ser atualizado para explicar que eles operam sob o novo serviço.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve **reescrever** a seção "Getting Started" (ou equivalente) do `README.md` principal. A nova seção deve seguir a estrutura e o conteúdo descritos abaixo.

**Arquivo 1 (Modificar): `README.md`**
```markdown
# ... (início do README.md existente) ...

## Getting Started

O Conductor agora opera sob uma arquitetura unificada e orientada a serviços. Toda a configuração é centralizada no arquivo `config.yaml` na raiz do projeto.

### 1. Configuração

Antes de rodar qualquer agente, configure seu ambiente no `config.yaml`:

```yaml
# config.yaml
storage:
  type: filesystem
  path: .conductor_workspace

# Adicione aqui diretórios para suas ferramentas customizadas
tool_plugins:
  - custom_tools/
```

-   **storage**: Define onde os dados dos agentes são armazenados.
    -   `filesystem`: (Padrão) Ideal para desenvolvimento local, não requer dependências.
    -   `mongodb`: Para ambientes de equipe ou produção.
-   **tool_plugins**: Lista de diretórios onde o Conductor irá procurar por ferramentas customizadas.

### 2. Executando Agentes

Embora estejamos caminhando para um CLI unificado, você ainda pode usar os CLIs `admin.py` e `agent.py`. Eles agora operam como interfaces para o novo serviço central e respeitam o `config.yaml`.

**Para Meta-Agentes:**
```bash
poetry run python src/cli/admin.py --agent AgentCreator_Agent --input "Crie um novo agente para analisar logs."
```

**Para Agentes de Projeto:**
```bash
poetry run python src/cli/agent.py --environment develop --project desafio-meli --agent ProductAnalyst_Agent --input "Analise os dados de produtos."
```

# ... (resto do README.md existente) ...
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando a seção "Getting Started" do `README.md` principal for reescrita para refletir a nova arquitetura e o fluxo de configuração, conforme especificado acima.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
