### **Proposta de Melhoria: Executor de Administração (`admin.py`)**

**Status:** Proposta
**Autor:** Gemini (com base na sugestão do usuário)

#### **1. Problema**

A invocação de meta-agentes (como o `AgentCreator_Agent`) conflita com o fluxo de trabalho dos agentes de projeto padrão. Forçar o `genesis_agent.py` a lidar com ambos os casos adiciona complexidade desnecessária ao seu código (lógica condicional de argumentos) e à sua responsabilidade.

#### **2. Proposta**

Seguindo o **Princípio da Responsabilidade Única**, propõe-se a criação de um novo ponto de entrada para o framework, focado exclusivamente em tarefas administrativas e de metadados.

-   **`scripts/genesis_agent.py` (Executor de Projeto):**
    -   **Função:** Mantém sua única responsabilidade de executar agentes que operam em projetos alvo.
    -   **Comando:** `python scripts/genesis_agent.py --environment <env> --project <proj> --agent <id>`
    -   **Lógica:** Seus parâmetros (`--environment`, `--project`) são sempre obrigatórios. O código é simples e direto.

-   **`scripts/admin.py` (Novo Executor de Administração):**
    -   **Função:** Executar meta-agentes que gerenciam o próprio framework (ex: `AgentCreator_Agent`, `migrate_agents_v2.py`).
    -   **Comando:** `python scripts/admin.py --agent <meta_agent_id>`
    -   **Lógica:** Não requer contexto de projeto/ambiente. Busca os agentes em um diretório comum (ex: `projects/_common/agents/`).

#### **3. Ação de Implementação**

1.  **Criar `scripts/admin.py`:** Implementar o novo script com seu parser de argumentos simplificado.
2.  **Refatorar Lógica Comum:** Extrair o código de carregamento de agente e o loop de sessão para um módulo compartilhado, que será usado tanto pelo `genesis_agent.py` quanto pelo `admin.py` para evitar duplicação.
3.  **Atualizar Documentação:** Adicionar a explicação sobre os dois executores e quando usar cada um.

#### **4. Benefícios**

-   **Alta Coesão:** Cada script tem uma responsabilidade clara e única.
-   **Código Mais Limpo:** Elimina a necessidade de lógica condicional no `genesis_agent.py`.
-   **Clareza para o Usuário:** A separação entre "usar" e "administrar" o framework se torna explícita.
