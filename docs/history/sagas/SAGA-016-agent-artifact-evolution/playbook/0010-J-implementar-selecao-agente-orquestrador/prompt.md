# [NOVO PADRÃO] Especificação Técnica e Plano de Execução: 0010-J

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
O objetivo é criar o **Cérebro Decisório** do Conductor: o `Orchestrator`. Este componente implementa um processo de seleção de agentes em duas etapas, otimizado para eficiência e precisão. Ao usar uma filtragem rápida e barata baseada em metadados (`definition.yaml`) antes de uma decisão semântica cara baseada em LLM (`persona.md`), garantimos que o sistema possa escalar para centenas de agentes sem degradação de performance, ao mesmo tempo que seleciona o especialista mais adequado para cada tarefa.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITO NÃO FUNCIONAL)**
- **Processo de Seleção em Duas Etapas:** O método `find_best_agent_for_task` **DEVE** implementar a lógica de filtragem em duas etapas. Ele não deve ler a `persona.md` de todos os agentes.
- **Injeção de Dependência:** O `Orchestrator` **DEVE** receber suas dependências (`AgentService`, etc.) em seu construtor para facilitar os testes e a manutenção.
- **Separação de Camadas:** A lógica do orquestrador **DEVE** residir em `src/core/orchestrator.py`.
- **Fallback Simples:** Para esta implementação inicial, se nenhum agente for encontrado após a filtragem, o método **DEVE** levantar uma exceção `NoSuitableAgentFoundError`. A integração com o `AgentCreator_Agent` será feita em um plano futuro.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**

**1. Criar o arquivo `src/core/orchestrator.py`:**

```python
# src/core/orchestrator.py

from typing import List

from src.core.domain import AgentDefinition
from src.core.agent_service import AgentService

class NoSuitableAgentFoundError(Exception):
    pass

class Orchestrator:
    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service
        # O LLM para a decisão semântica seria injetado aqui também
        # self.llm_client = llm_client 

    def find_best_agent_for_task(self, task_description: str) -> AgentDefinition:
        """
        Encontra o agente mais adequado para uma tarefa usando um processo de duas etapas.
        """
        # Etapa 0 (Simplificada): Extrair palavras-chave da tarefa.
        # Numa implementação real, isso usaria um LLM ou NLP. Aqui, faremos uma busca simples.
        required_capabilities = self._extract_keywords(task_description)

        # Etapa 1: Filtragem Rápida
        all_definitions = self.agent_service.list_all_agent_definitions()
        
        candidates = [
            defn for defn in all_definitions
            if any(cap in defn.capabilities for cap in required_capabilities)
        ]

        if not candidates:
            raise NoSuitableAgentFoundError(f"Nenhum agente encontrado com as capacidades: {required_capabilities}")

        if len(candidates) == 1:
            return candidates[0]

        # Etapa 2: Decisão Semântica (Placeholder)
        # Se tivéssemos múltiplos candidatos, aqui leríamos suas personas
        # e usaríamos um LLM para decidir qual é o melhor.
        # Por enquanto, retornamos o primeiro candidato encontrado.
        print(f"Múltiplos candidatos encontrados. Selecionando o primeiro: {[c.name for c in candidates]}")
        return candidates[0]

    def _extract_keywords(self, task_description: str) -> List[str]:
        """
        Placeholder para a lógica de extração de palavras-chave.
        """
        # Lógica simples para o exemplo.
        # Ex: "criar um scaffold para um agente" -> ["create_agent_scaffold"]
        if "scaffold" in task_description or "create agent" in task_description:
            return ["create_agent_scaffold"]
        if "commit message" in task_description:
            return ["generate_commit_message_from_diff"]
        return [word for word in task_description.split() if not word.isspace()]
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
- O arquivo `orchestrator.py` foi criado com a classe `Orchestrator` e a exceção `NoSuitableAgentFoundError`.
- O método `find_best_agent_for_task` foi implementado, seguindo a lógica de duas etapas (mesmo que a segunda etapa seja um placeholder).
- O `AgentService` precisará de um novo método `list_all_agent_definitions()` que você deve assumir ou implementar.

#### **6. SINAL DE CONCLUSÃO**
`TASK_COMPLETE`
