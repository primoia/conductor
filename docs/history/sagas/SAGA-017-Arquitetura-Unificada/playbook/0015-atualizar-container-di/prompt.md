# Especificação Técnica e Plano de Execução: 0015-atualizar-container-di

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa centraliza a construção do `ConductorService` em nosso container de Injeção de Dependência. Isso garante que toda a aplicação acesse uma única instância (singleton) do serviço, o que é crucial para o gerenciamento de estado consistente (como o registro de ferramentas) e simplifica a forma como outros componentes (como os CLIs) obtêm acesso ao novo núcleo da aplicação.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** A lógica **DEVE** ser adicionada ao arquivo `src/container.py`.
- **Padrão Singleton:** A implementação **DEVE** garantir que uma nova instância do `ConductorService` não seja criada a cada vez que o serviço é solicitado. A mesma instância deve ser retornada.
- **Desacoplamento:** O container **DEVE** construir o serviço sem que o chamador precise conhecer os detalhes de sua construção.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve modificar o arquivo `src/container.py`. O conteúdo do arquivo **DEVE** ser modificado para corresponder ao especificado abaixo.

**Arquivo 1 (Modificar): `src/container.py`**
```python
# src/container.py
# ... (imports existentes, como dependency_injector) ...
from src.core.conductor_service import ConductorService # Importar o novo serviço

class Container(containers.DeclarativeContainer):
    # ... (config e outros providers existentes) ...

    # Adicionar o provider para o novo serviço
    conductor_service = providers.Singleton(ConductorService)

    # Manter os providers existentes para a lógica legada por enquanto
    # Exemplo:
    # agent_logic_provider = providers.Factory(...)

# ... (código existente para criar a instância do container) ...
```

*Nota: A implementação exata pode variar ligeiramente dependendo da biblioteca `dependency_injector` estar em uso ou de um padrão singleton manual. A especificação acima assume `dependency_injector.providers.Singleton`, que é a forma canônica de resolver este problema com a biblioteca.*

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `src/container.py` for modificado para incluir um provider `Singleton` para o `ConductorService`.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
