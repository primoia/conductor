### Plano de Execução: Estágio 19 - Testes Unitários para `ConductorService`

#### Contexto Arquitetônico

O `ConductorService` é o coração da nossa nova arquitetura. Ele contém a lógica de orquestração crítica, como o carregamento de configuração, a fábrica de armazenamento, a descoberta de agentes e o carregamento de ferramentas. Esta tarefa consiste em escrever um conjunto abrangente de testes unitários para isolar e validar cada um desses componentes lógicos.

#### Propósito Estratégico

O objetivo é criar uma "rede de segurança" de testes que garanta a estabilidade e a corretude do nosso serviço principal. Testes unitários nos permitem refatorar o serviço com confiança no futuro, sabendo que qualquer mudança que quebre um comportamento esperado será detectada imediatamente. Atingir uma alta cobertura de teste (>90%) é uma marca de qualidade de engenharia que paga dividendos a longo prazo na manutenibilidade do projeto.

#### Checklist de Execução

- [ ] Criar um novo arquivo de teste em `tests/core/test_conductor_service.py`.
- [ ] Usar `pytest` e a biblioteca `unittest.mock`.
- [ ] Escrever um teste para o carregador de configuração, mockando o `open` e o `yaml.safe_load` para testar cenários de sucesso e falha (arquivo não encontrado, YAML inválido).
- [ ] Escrever um teste para a `StorageFactory`, garantindo que ela instancia o repositório correto com base em uma configuração mockada.
- [ ] Escrever um teste para `discover_agents`, mockando a resposta do `IStateRepository` para garantir que o serviço mapeia os dados corretamente para os DTOs.
- [ ] Escrever um teste para `load_tools`, mockando o sistema de arquivos para simular a presença de um diretório de plugin e garantir que as ferramentas são carregadas dinamicamente.
- [ ] Atingir uma cobertura de teste de pelo menos 90% para `src/core/conductor_service.py`.
