# Arquitetura Detalhada do Conductor

## 🏛️ Visão Arquitetural Geral

### Principles Fundamentais

1. **Single Responsibility per Agent**: Cada agente tem uma única função bem definida
2. **Event-Driven Coordination**: Coordenação via eventos, não via calls diretos
3. **Persistent State**: Estado sobrevive a reinicializações
4. **Human Orchestration**: Humano como supervisor estratégico
5. **Emergent Behavior**: Comportamento complexo emerge de regras simples

## 🎭 Modelo de Agentes

Para uma descrição exaustiva da estrutura interna e do ciclo de vida de cada agente, consulte o documento [Anatomia e Ciclo de Vida de um Agente Conductor](agent-anatomy.md).

Esta seção descreve os papéis e tipos de agentes no sistema.

### Anatomia de um Agente

```
agent-{name}/
├── agent.md           # Definição: função, regras, restrições
├── {n}.txt           # Comandos sequenciais (1.txt, 2.txt, ...)
├── state.json        # Estado persistente atual
└── history/          # Histórico de execuções (futuro)
```

### Ciclo de Vida do Agente

```
[IDLE] → [TRIGGERED] → [PROCESSING] → [REPORTING] → [IDLE]
   ↑                                                    ↓
   └─────────── STATE PERSISTENCE ←──────────────────────
```

### Tipos de Agentes

#### 1. **Inspection Agents** (Coletores)
- **Função**: Coletar dados, verificar status
- **Exemplo**: Gradle Checker, Test Status Checker
- **Características**: Stateless entre execuções, fast execution

#### 2. **Processing Agents** (Processadores)
- **Função**: Transformar dados, executar mudanças
- **Exemplo**: Code Fixer, Service Implementer
- **Características**: Stateful, context-aware, longer execution

#### 3. **Analysis Agents** (Analisadores)
- **Função**: Consolidar, analisar, reportar insights
- **Exemplo**: Documentation Agent, Inconsistency Detector
- **Características**: Multi-input, analytical, report generation

#### 4. **Meta Agents** (Meta-processamento)
- **Função**: Gerenciar outros agentes
- **Exemplo**: Context Compressor, State Manager
- **Características**: Agent-aware, optimization focus

## 🔄 Coordenação e Orquestração

### Event Flow Pattern

```
[Human/Orchestrator] → [Event Queue] → [Agent] → [Result Queue] → [Next Trigger]
```

### Tipos de Eventos

#### 1. **Command Events**
```json
{
  "type": "command",
  "target_agent": "gradle-checker-x",
  "command": "check gradle version microservice-x",
  "timestamp": "2025-01-09T10:30:00Z",
  "correlation_id": "demo-001"
}
```

#### 2. **Result Events**
```json
{
  "type": "result",
  "source_agent": "gradle-checker-x",
  "status": "SUCCESS",
  "data": {
    "version": "7.5.1",
    "path": "microservice-x/build.gradle"
  },
  "timestamp": "2025-01-09T10:30:15Z",
  "correlation_id": "demo-001"
}
```

#### 3. **State Events**
```json
{
  "type": "state_change",
  "agent": "gradle-checker-x",
  "old_state": "idle",
  "new_state": "processing",
  "timestamp": "2025-01-09T10:30:01Z"
}
```

## 🗄️ Persistência de Estado

### Estratégias de Persistência

#### 1. **Simple State (Protótipo Atual)**
```json
{
  "agent_id": "gradle-checker-x",
  "current_status": "idle",
  "last_command": "check gradle version microservice-x",
  "last_execution": "2025-01-09T10:30:00Z",
  "state": {
    "last_version_found": "7.5.1",
    "execution_count": 1
  }
}
```

#### 2. **Event Sourcing (Implementação Futura)**
- Todos os eventos são armazenados sequencialmente
- Estado atual é reconstruído via replay de eventos
- Permite "time travel" e debugging avançado

#### 3. **Snapshot + Incremental (Escala)**
- Snapshots periódicos do estado completo
- Eventos incrementais desde último snapshot
- Otimização para agentes com longo histórico

### Recuperação de Estado

```bash
# Processo de "boot" do agente
1. Lê state.json (estado atual)
2. Verifica último evento processado
3. Reconstrói contexto se necessário
4. Marca-se como "ready" para novos comandos
```

## 🎯 Padrões de Coordenação

### 1. **Pipeline Sequential**
```
Agent A → Agent B → Agent C
```
- Um agente depende da conclusão do anterior
- Exemplo: TDD → Implementation → Documentation

### 2. **Fan-Out/Fan-In**
```
        → Agent B1 ↘
Agent A → Agent B2 → Agent C
        → Agent B3 ↗
```
- Processamento paralelo seguido de consolidação
- Exemplo: Multiple Test Checkers → Documentation

### 3. **Feedback Loop**
```
Agent A ⟷ Agent B
```
- Agentes se refinam mutuamente
- Exemplo: TDD Writer ⟷ Service Implementer

### 4. **Broadcast Pattern**
```
Trigger → [All Test Workers]
```
- Um evento dispara múltiplos agentes idênticos
- Exemplo: 400 test workers rodando simultaneamente

## 🔧 Implementação Técnica

### Protótipo (Arquivos Texto)
```
Vantagens:
- Debugging visual
- Versionamento natural (git)
- Simplicidade extrema
- Facilidade de modificação

Limitações:
- Execução manual
- Sem paralelismo real
- Estado não é dinâmico
```

### Implementação Real (Futura)
```
Stack Sugerida:
- Message Broker: Redis Streams / Apache Kafka
- Containerization: Docker + Docker Compose
- Orchestration: Custom Python/Node.js coordinator
- AI Integration: OpenAI/Gemini APIs
- State Storage: PostgreSQL / MongoDB
- Monitoring: Custom dashboard + logging
```

## 🧠 Context Management

### Problema do Contexto Crescente
- LLMs têm limite de tokens
- Contexto acumula ao longo do tempo
- Performance degrada com contexto grande

### Soluções Arquiteturais

#### 1. **Context Compression Agent**
```
Input: Thread longa (50+ iterações)
Process: Identifica padrões, learnings, decisões chave
Output: Contexto comprimido com essência
```

#### 2. **Hierarchical Context**
```
Global Context: Conhecimento do projeto
Agent Context: Específico do agente
Session Context: Contexto da sessão atual
```

#### 3. **Context Rotation**
```
Recent Context (últimas 10 iterações)
+ Compressed History (resumo das anteriores)
+ Key Learnings (padrões identificados)
```

## 📊 Escalabilidade

### Scaling Strategies

#### 1. **Horizontal Agent Scaling**
```
1 Test → 10 Tests → 100 Tests → 400 Tests
```
- Adicionar agentes idênticos para tarefas paralelas
- Resource pooling inteligente

#### 2. **Vertical Specialization**
```
Generic Agent → Specialized Agents
```
- Agents especializam-se em contextos específicos
- Expertise acumulada ao longo do tempo

#### 3. **Meta-Agent Scaling**
```
Agents → Meta-Agents → Meta-Meta-Agents
```
- Agents que gerenciam outros agents
- Hierarquia de responsabilidades

### Performance Considerations

- **Latency**: Event processing deve ser < 100ms
- **Throughput**: Sistema deve handle 100+ agents simultâneos
- **Memory**: Estado por agent deve ser < 10MB
- **Storage**: Eventos devem ser compressed/archived periodicamente

## 🛡️ Resilience Patterns

### Fault Tolerance
- **Agent Restart**: Agent falha → restart automático com último estado
- **Event Replay**: Eventos perdidos podem ser reprocessados
- **Partial Failure**: Falha de um agent não afeta outros
- **Circuit Breaker**: Agent com muitas falhas é temporariamente desabilitado

### Monitoring & Observability
- **Health Checks**: Cada agent reporta saúde periodicamente
- **Event Tracing**: Correlation IDs para rastrear fluxos completos
- **Performance Metrics**: Latência, throughput, success rate por agent
- **Alerting**: Notificações para padrões anômalos

## 🎯 Advanced Concepts: Conditional Activation & Hybrid Architecture

### Conditional Agent Activation (Game Theory Refined)

#### Problem with Traditional Approach
- **Naive assumption**: All agents run on every trigger
- **Reality**: Most agents are irrelevant for specific changes
- **Cost**: Unnecessary API calls and resource waste

#### Smart Activation Pattern
```
Change in ServiceA.java
    ↓
Impact Analysis
    ↓
Selective Activation:
- test-serviceA-unit-* (5 agents)
- test-serviceA-integration-* (3 agents)  
- test-end-to-end-flows-using-serviceA (2 agents)
    ↓
= 10 agents activated (not 400)
= 95% cost reduction
```

#### Implementation Strategy
```python
class ConditionalOrchestrator:
    def __init__(self):
        self.dependency_graph = self.build_dependency_graph()
        
    def activate_agents_for_change(self, changed_files):
        relevant_agents = []
        for file in changed_files:
            relevant_agents.extend(
                self.dependency_graph.get(file, [])
            )
        return deduplicate(relevant_agents)
        
    def build_dependency_graph(self):
        return {
            "UserService.java": [
                "test-user-validation",
                "test-user-integration-auth", 
                "test-e2e-user-registration"
            ],
            "PaymentService.java": [
                "test-payment-processing",
                "test-payment-security"
            ]
        }
```

#### Economic Impact
```
Traditional: 400 agents × $0.05 = $20 per execution
Conditional: 15 agents × $0.05 = $0.75 per execution
Savings: 96.25% cost reduction
```

### Hybrid Architecture: Local GPU + Cloud APIs

#### Tiered Agent Classification

##### Tier 1: Local GPU (Near-Zero Cost)
```
Simple Tasks - Small Models (7B-13B parameters)
- Test executors: "Run test X" → Pass/Fail
- Syntax validators: "Check Java syntax" → Valid/Invalid
- File operations: "Check if file exists" → True/False
- Basic formatting: "Format JSON" → Formatted output

Cost: ~$0 (electricity only)
Latency: 50-200ms
Throughput: 100+ req/sec
```

##### Tier 2: Cheap APIs (GPT-3.5/Gemini Flash)
```
Intermediate Tasks - Moderate Analysis
- Code quality: Basic code smell detection
- Security scanning: Common vulnerability patterns
- Test coverage: Coverage percentage calculation
- Simple documentation: Basic API docs

Cost: $0.0002-0.002 per 1K tokens
Use case: 20% of agent executions
```

##### Tier 3: Premium APIs (GPT-4/Claude/Gemini Pro)
```
Complex Tasks - Deep Analysis
- Architecture review: Design pattern violations
- Advanced security: Authentication flow analysis
- Performance optimization: Complex bottleneck detection
- Business logic validation: Domain rule verification

Cost: $0.015-0.03 per 1K tokens
Use case: 10% of agent executions (high-impact only)
```

#### Smart Routing Algorithm
```python
class HybridRouter:
    def route_task(self, task, context):
        complexity = self.calculate_complexity(task, context)
        
        if complexity < 0.3:
            return LocalGPUAgent(task)
        elif complexity < 0.7:
            return CheapAPIAgent(task)
        else:
            return PremiumAPIAgent(task)
    
    def calculate_complexity(self, task, context):
        factors = [
            task.requires_deep_context,
            task.involves_business_logic,
            task.affects_security,
            task.needs_multi_step_reasoning,
            len(context.related_files) > 5
        ]
        return sum(factors) / len(factors)
```

#### Escalation Pattern
```
Local Agent (confidence < 80%) → Cheap API
Cheap API (confidence < 90%) → Premium API
Premium API → Definitive result
```

#### Economic Model Example
```
100 PR reviews/month:
- 70% tasks → Local GPU = $0
- 20% tasks → Cheap API = $50/month  
- 10% tasks → Premium API = $200/month
────────────────────────────────────
Total: $250/month vs $2000+ all-premium

ROI: 8x cost reduction with maintained quality
```

#### Technical Stack
```
Local GPU Setup:
- Hardware: RTX 4090 or similar
- Models: Llama 2 7B, CodeLlama 13B, StarCoder
- Framework: vLLM, Ollama, TensorRT-LLM
- Deployment: Docker containers with GPU access

Cloud APIs:
- Cheap: Gemini Flash ($0.00015/1K), GPT-3.5 ($0.002/1K)
- Premium: Claude Sonnet ($0.015/1K), GPT-4 ($0.03/1K)
```

#### Competitive Advantages
1. **Cost Efficiency**: 10-20x cheaper than cloud-only solutions
2. **Data Privacy**: Sensitive code never leaves local environment
3. **Low Latency**: Local processing eliminates network overhead
4. **Customization**: Fine-tune local models for specific projects
5. **Scalability**: Add GPU capacity as needed

---

Esta arquitetura foi pensada para crescer organicamente, começando simples (protótipo com arquivos) e evoluindo para sistema robusto de produção mantendo os mesmos princípios fundamentais, agora com otimizações econômicas e técnicas avançadas.

---

## Evolução e Refatoração de Agentes: O Princípio da Bifurcação

A estratégia mais avançada do Conductor para gerenciar a complexidade não é técnica, mas arquitetural. Ela se baseia em um princípio análogo à refatoração de software.

### A Tese Central: Complexidade é um "Code Smell" para Agentes

O crescimento excessivo do contexto de um agente (seu `log/`, `persona.md`, etc.) não é um problema a ser resolvido com compressão de dados. É um **sintoma** de que o agente assumiu responsabilidades demais.

A solução não é tratar o sintoma (comprimir o contexto), mas sim curar a doença: **refatorar o agente**.

### O Processo de Bifurcação

Assim como um programador refatora uma "Classe Deus" em classes menores e mais focadas, o Conductor prevê um mecanismo para "bifurcar" um agente sobrecarregado.

1.  **Gatilho (Trigger):** A bifurcação é sugerida quando um agente excede certos limites de complexidade (ex: tamanho do histórico, diversidade de tarefas em seu log).
2.  **Análise:** Um "Arquiteto" (humano ou um Meta-Agente) analisa o histórico do agente para identificar sub-domínios distintos de responsabilidade.
3.  **Criação e Migração:** Dois ou mais agentes "filhos" são criados. O histórico do agente "pai" é cuidadosamente dividido e migrado para os filhos relevantes. Esta é uma **refatoração sem perdas**, preservando todo o conhecimento institucional.
4.  **Aposentadoria:** O agente original é aposentado ou se torna uma "Fachada" que delega tarefas para seus filhos agora especializados.

### Benefícios da Bifurcação

*   **Previne a Compressão com Perdas:** Em vez de resumir (e potencialmente perder) informações históricas valiosas, a bifurcação as preserva em um novo contexto mais focado.
*   **Mantém o Contexto Limpo:** Garante que os prompts enviados para a IA sejam sempre densos em informação relevante, maximizando a qualidade das respostas e minimizando custos.
*   **Escalabilidade Sustentável:** O sistema se auto-organiza para combater a entropia e a complexidade, garantindo que ele permaneça ágil e manutenível à medida que cresce.

Este princípio garante que a arquitetura de agentes do Conductor evolua de forma saudável, espelhando as melhores práticas de arquitetura de software do mundo real.

---

## Interface Humana: A Forja de Agentes

A interação estratégica e o gerenciamento da complexa força de trabalho de agentes do Conductor são projetados para ocorrer através de uma interface gráfica e gamificada. Esta interface, conhecida como "A Forja de Agentes", desacopla o Arquiteto Humano da complexidade do backend.

Ela permite a criação, o monitoramento e a evolução dos agentes usando uma metáfora de RPG, e serve como o principal mecanismo para popular e refinar o grafo de dependências do sistema de forma interativa.

Para a visão completa deste componente, consulte o documento: **[Visão: A Forja de Agentes](vision-agent-forge.md)**.