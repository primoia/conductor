# Especificação Técnica e Plano de Execução: 0001-A-definir-contrato-servico

#### **1. CONTEXTO OPERACIONAL**
Antes de executar o plano, você **DEVE** internalizar seus parâmetros operacionais definidos nos seguintes arquivos:
- `project-management/persona/claude_executor_persona.md`
- `project-management/persona/claude_executor_mode.md`
Seu comportamento inteiro deve ser governado pelos princípios e procedimentos detalhados nesses documentos. Você é um executor literal; você não infere, você implementa.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa é a pedra angular da arquitetura da SAGA-017. Seu propósito é estabelecer um **Contrato de Serviço** formal para o novo núcleo do Conductor. Ao criar uma interface abstrata, estamos aplicando o Princípio da Inversão de Dependência, o que garante que os componentes de UI (CLIs, e futuramente a API) dependam de uma abstração estável, e não de uma implementação concreta. Este arquivo é a "Constituição" da nova arquitetura, a fundação sobre a qual toda a lógica de serviços será construída e testada.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Separação de Camadas:** A interface **DEVE** ser localizada em um novo arquivo em `src/ports/conductor_service.py`. O diretório `ports` é destinado a definir as interfaces (portas) que o núcleo da aplicação (`core`) implementará.
- **Abstração Pura:** A classe **DEVE** herdar de `abc.ABC` e todos os seus métodos **DEVEM** ser decorados com `@abstractmethod`. Nenhuma lógica de implementação concreta é permitida neste arquivo.
- **Clareza e Tipagem:** Todos os métodos e argumentos **DEVEM** ter dicas de tipo explícitas importadas do módulo `typing`. Use referências de tipo como strings (ex: `'TaskDTO'`) para evitar importações circulares, pois os tipos concretos ainda não existem.
- **Documentação Essencial:** Cada método na interface **DEVE** incluir um docstring claro e conciso explicando seu propósito.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um único arquivo, `src/ports/conductor_service.py`. O arquivo **DEVE** conter o seguinte conteúdo exatamente. Não adicione, remova ou altere nenhuma parte desta especificação.

```python
# src/ports/conductor_service.py
from abc import ABC, abstractmethod
from typing import List

class IConductorService(ABC):
    """
    Define o contrato para o serviço central que orquestra todo o ecossistema do Conductor.
    Esta interface desacopla a lógica do núcleo dos pontos de entrada (CLIs, APIs).
    """

    @abstractmethod
    def discover_agents(self) -> List['AgentDefinition']:
        """
        Consulta o backend de armazenamento configurado e retorna a definição de todos os agentes disponíveis.
        """
        raise NotImplementedError

    @abstractmethod
    def execute_task(self, task: 'TaskDTO') -> 'TaskResultDTO':
        """
        Orquestra a execução de uma única tarefa, desde a seleção do agente até a sua conclusão.
        Este é o principal ponto de entrada para a lógica de execução.
        """
        raise NotImplementedError

    @abstractmethod
    def load_tools(self) -> None:
        """
        Carrega as ferramentas (core e plugins) conforme a configuração global.
        Deve ser chamado durante a inicialização do serviço.
        """
        raise NotImplementedError
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho será considerado concluído **somente quando** o arquivo `src/ports/conductor_service.py` for criado e seu conteúdo for uma correspondência exata com o bloco de código fornecido na Especificação Técnica acima. O arquivo deve estar livre de quaisquer erros de sintaxe. Nenhum outro arquivo deve ser criado ou modificado.

#### **6. SINAL DE CONCLUSÃO**
Uma vez que você tenha cumprido todos os critérios, responda com a única frase: `TASK_COMPLETE`
