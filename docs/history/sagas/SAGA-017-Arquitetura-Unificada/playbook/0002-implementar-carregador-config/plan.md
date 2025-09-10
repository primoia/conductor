### Plano de Execução: Estágio 2 - Implementação do Carregador de Configuração

#### Contexto Arquitetônico

Com o contrato do serviço definido, o primeiro passo concreto na implementação do `ConductorService` é torná-lo ciente de seu ambiente. A fonte da verdade para o comportamento do sistema é o `config.yaml`. Esta tarefa consiste em construir o mecanismo que lê, valida e internaliza essa configuração. Utilizaremos Pydantic para definir um schema robusto para o `config.yaml`, garantindo que qualquer configuração inválida ou malformada seja rejeitada na inicialização com feedback claro, prevenindo erros em tempo de execução.

#### Propósito Estratégico

O objetivo é estabelecer um ponto de entrada de configuração único e à prova de falhas. Ao centralizar a lógica de carregamento e validação no construtor do `ConductorService`, garantimos que nenhuma instância do serviço possa existir em um estado mal configurado. Isso erradica uma classe inteira de bugs relacionados a configurações ausentes ou inválidas e torna o comportamento do sistema previsível e dependente de um artefato de configuração explícito, conforme a visão da SAGA-016.

#### Checklist de Execução

- [x] Criar um novo arquivo `src/core/config_schema.py` para as definições Pydantic.
- [x] No novo arquivo, definir modelos Pydantic para `StorageConfig`, `ToolPluginConfig` e o `GlobalConfig` principal.
- [x] Criar um novo arquivo `src/core/conductor_service.py`.
- [x] Nele, criar a classe `ConductorService` que implementa a interface `IConductorService`.
- [x] No `__init__` do `ConductorService`, implementar a lógica para ler o `config.yaml`.
- [x] Utilizar os modelos Pydantic para validar o conteúdo do `config.yaml`, armazenando a configuração validada em um atributo privado (ex: `self._config`).
- [x] Garantir que uma exceção `ConfigurationError` seja lançada se o arquivo não existir ou for inválido.
