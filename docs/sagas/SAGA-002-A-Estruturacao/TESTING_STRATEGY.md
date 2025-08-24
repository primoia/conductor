# Estratégia de Testes: Garantindo Qualidade e Segurança no Framework Maestro

**1. Visão Geral e Filosofia:**

*   **Objetivo:** Assegurar a qualidade, segurança, robustez, performance e manutenibilidade do Framework Maestro em todas as suas camadas.
*   **Filosofia:** Testes são uma parte intrínseca do processo de desenvolvimento ("Qualidade embutida"), não uma fase pós-desenvolvimento. Buscamos a detecção precoce de defeitos e a validação contínua.

**2. Pilares da Estratégia (A Pirâmide de Testes Adaptada):**

*   **2.1. Testes Unitários (A Base Sólida):**
    *   **Foco:** Validar a menor unidade de código isoladamente (funções, métodos, classes).
    *   **Onde Aplicar:** Lógica de parsing de argumentos, carregamento de `agent.yaml`, validação de schemas, funções individuais do `Toolbelt` (ex: `read_file`, `write_file`), lógica de construção de prompts no `LLMClient`, gestão de estado (`state.json`).
    *   **Ferramentas:** `pytest`.
    *   **Métrica:** Alta cobertura de código (alvo: 80%+ de cobertura de linha para lógica de negócio).
    *   **Benefício:** Detecção precoce de bugs, refatoração segura, feedback rápido para desenvolvedores.

*   **2.2. Testes de Integração (Conectando as Peças):**
    *   **Foco:** Validar a interação entre dois ou mais componentes.
    *   **Onde Aplicar:** Fluxos de carregamento completo de um agente (Gênesis carregando `agent.yaml`, `persona.md`, `state.json`), execução de ferramentas (mockando o sistema de arquivos e a API do LLM), persistência de estado (`/save`).
    *   **Ferramentas:** `pytest`.
    *   **Benefício:** Validação de interfaces e contratos.

*   **2.3. Testes de Sistema/Funcionais (End-to-End - E2E):**
    *   **Foco:** Validar fluxos completos do usuário, simulando a experiência real.
    *   **Onde Aplicar:** Simulação de sessões REPL completas, onboarding, criação de agente, análise de problema, criação de plano, validação de arquivos criados/modificados no disco.
    *   **Ferramentas:** `pytest` com simulação de input/output, ou frameworks de automação de CLI.
    *   **Benefício:** Validação da experiência do usuário e da integração de alto nível.

*   **2.4. Testes de Segurança (Camada Crítica e Contínua):**
    *   **Foco:** Identificar e mitigar vulnerabilidades.
    *   **Onde Aplicar:**
        *   **`run_shell_command`:** Testes de fuzzing com entradas maliciosas, validação da `allowlist` e `denylist` de comandos.
        *   **`write_file`:** Tentativas de escrita fora de diretórios permitidos, path traversal.
        *   **`agent.yaml` / `team_template.yaml` parsing:** Testes com templates maliciosos ou malformados que tentam injetar código ou dados perigosos.
        *   **Validação de Input do Usuário:** Sanitização e validação rigorosa de todos os inputs conversacionais.
    *   **Ferramentas:** Testes unitários/integração dedicados, ferramentas de análise estática de código (SAST), testes de penetração (fuzzing).
    *   **Benefício:** Proteção contra ataques, uso indevido e garantia da integridade do sistema.

*   **2.5. Testes de Performance e Custo (Escalabilidade e Eficiência):**
    *   **Foco:** Latência das respostas do LLM, uso de tokens, consumo de memória/CPU, tempo de execução de operações intensivas de I/O.
    *   **Onde Aplicar:** Chamadas à API do LLM, operações de I/O intensivas (leitura/escrita de grandes arquivos), gestão de histórico de conversa (impacto da janela deslizante).
    *   **Ferramentas:** Scripts de carga, monitoramento de API, ferramentas de profiling.
    *   **Benefício:** Otimização de recursos e controle de custos e garantia de uma experiência de usuário fluida.

**3. Estratégia Evolutiva e de Manutenção:**

*   **3.1. Testes como Código:** Todos os testes devem ser versionados junto com o código-fonte.
*   **3.2. Integração Contínua (CI/CD):** Automatizar a execução de todos os testes em cada push/pull request. Falhas no CI/CD devem bloquear o merge.
*   **3.3. Testabilidade por Design:** Incentivar a escrita de código modular, com baixo acoplamento e interfaces claras, facilitando a criação de mocks e testes unitários.
*   **3.4. Gerenciamento de Dados de Teste:** Criar e manter um conjunto de dados de teste realistas e reproduzíveis para garantir a consistência dos resultados.
*   **3.5. Ambientes de Teste:** Garantir ambientes de teste consistentes e isolados para evitar interferências.

**4. Responsabilidades:**

*   **Desenvolvedores (Staff):** São os principais responsáveis por escrever testes unitários e de integração para o código que produzem.
*   **CTO (Eu):** Definir a estratégia geral, garantir a cobertura de segurança e performance, e revisar a qualidade e a abrangência dos testes.

**5. Próximos Passos (Implementação da Estratégia):**

*   **Fase 1 (Imediata):**
    *   Revisar e expandir os testes unitários existentes para o `genesis_agent.py` e `Toolbelt`, focando na cobertura de casos de borda e tratamento de erros.
    *   Criar testes de integração para o carregamento de agentes e chamadas de ferramentas.
    *   Adicionar testes de segurança para `run_shell_command` (fuzzing de comandos perigosos e validação da allowlist).
*   **Fase 2 (Contínua):**
    *   Integrar testes E2E para o fluxo de onboarding.
    *   Implementar monitoramento de métricas de performance e custo.
    *   Expandir a cobertura de testes de segurança para parsing de YAML e validação de input.
