# Sistema de Ferramentas com Escopo de Escrita

Agentes podem receber "ferramentas" que lhes dão a capacidade de interagir com o sistema de arquivos e executar comandos.

**Segurança em Primeiro Lugar:**
Para evitar operações destrutivas ou indesejadas, a ferramenta de escrita (`Write`) é restrita por um **escopo de escrita**.

**Configuração:**
- No arquivo `agent.yaml`, a chave `output_scope` define um padrão `glob` que restringe onde o agente pode escrever arquivos. Por exemplo: `src/main/kotlin/**/*.kt`.

Qualquer tentativa de escrita fora desse padrão será bloqueada, garantindo a integridade da base de código.
