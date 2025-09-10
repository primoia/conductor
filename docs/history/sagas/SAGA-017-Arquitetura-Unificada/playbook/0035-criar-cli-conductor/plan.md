### Plano de Execução: Estágio 35 - Criar o Ponto de Entrada `conductor.py`

#### Contexto Arquitetônico

Com a arquitetura interna totalmente unificada sob o `ConductorService`, o passo final lógico é unificar também a camada de entrada. Manter dois CLIs separados (`admin.py` e `agent.py`) é uma complexidade desnecessária a longo prazo. Esta tarefa consiste em criar um único ponto de entrada, `conductor.py`, que atuará como um "facade" unificado.

#### Propósito Estratégico

O objetivo é simplificar a experiência do usuário e criar uma interface de comando única e coesa para o sistema. Um único CLI `conductor` é mais intuitivo e profissional. Este estágio estabelece o ponto de entrada definitivo para a interação do usuário com o sistema, sobre o qual toda a funcionalidade futura, incluindo a orquestração do Maestro, será construída.

#### Checklist de Execução

- [x] Criar um novo arquivo `src/cli/conductor.py`.
- [x] Usar `argparse` para criar um parser principal (`conductor`).
- [x] Adicionar subparsers para os comandos `admin` e `agent`.
- [x] O subparser `admin` deve aceitar os mesmos argumentos que o `admin.py` legado.
- [x] O subparser `agent` deve aceitar os mesmos argumentos que o `agent.py` legado.
- [x] A lógica do script deve analisar os argumentos e, em seguida, invocar a lógica correspondente (que agora está encapsulada no `ConductorService`).
- [x] O script deve funcionar como um substituto "drop-in" para os dois CLIs antigos.
