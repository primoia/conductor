# Metaprogramação com AgentCreator

Metaprogramação é a capacidade de um programa escrever ou manipular outros programas. No Conductor, isso se manifesta através do `AgentCreator_Agent`.

**O que é:**
- O `AgentCreator_Agent` é um **meta-agente** (um agente que gerencia outros agentes).
- Ele guia o usuário através de um diálogo para criar a estrutura de diretórios e os arquivos de configuração (`agent.yaml`, `persona.md`) para um novo agente.

**Como usar:**
- Execute o `admin.py` para invocar o `AgentCreator_Agent`:
  ```bash
  python scripts/admin.py --agent AgentCreator_Agent --repl
  ```
