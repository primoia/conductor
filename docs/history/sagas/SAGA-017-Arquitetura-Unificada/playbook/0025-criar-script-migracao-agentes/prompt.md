# Especificação Técnica e Plano de Execução: 0025-criar-script-migracao-agentes

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa cria a ferramenta essencial para trazer nossos agentes existentes para a nova arquitetura. Um script de migração automatizado garante um processo de transição consistente, rápido e livre de erros, que é fundamental para a adoção bem-sucedida do novo sistema unificado.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** O script **DEVE** ser criado em `scripts/migrate_legacy_agents.py`.
- **Interface:** O script **DEVE** ser executável a partir da linha de comando e usar `argparse` para receber o diretório de origem e de destino.
- **Formato de Saída:** O artefato de saída para cada agente migrado **DEVE** ser um único arquivo JSON.
- **Idempotência:** O script deve, idealmente, ser idempotente. Se um agente já existe no destino, ele pode ser ignorado ou sobrescrito com um aviso.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `scripts/migrate_legacy_agents.py`**
```python
# scripts/migrate_legacy_agents.py
import argparse
import yaml
import json
from pathlib import Path

def migrate_agent(agent_source_dir: Path, target_dir: Path):
    """
    Lê a estrutura de diretório de um agente legado e a converte em um único artefato JSON.
    """
    print(f"Migrando agente de: {agent_source_dir}...")
    
    agent_id = agent_source_dir.name
    agent_state = {
        "agent_id": agent_id,
        "agent_home_path": str(agent_source_dir.resolve()), # Preserva o caminho original para referência
    }

    # Carregar agent.yaml (que contém a definição)
    try:
        with open(agent_source_dir / "agent.yaml", 'r') as f:
            agent_yaml = yaml.safe_load(f)
            # A chave 'definition' pode ou não existir no formato antigo, adaptamos aqui
            agent_state.update(agent_yaml)
    except FileNotFoundError:
        print(f"  AVISO: agent.yaml não encontrado para {agent_id}. Pulando definição.")
        return

    # Carregar persona.md
    try:
        with open(agent_source_dir / "persona.md", 'r') as f:
            agent_state["persona"] = f.read()
    except FileNotFoundError:
        print(f"  INFO: persona.md não encontrada para {agent_id}.")

    # Carregar playbook.yaml (opcional)
    try:
        with open(agent_source_dir / "playbook.yaml", 'r') as f:
            agent_state["playbook"] = yaml.safe_load(f)
    except FileNotFoundError:
        pass # É opcional

    # Salvar o novo artefato JSON
    target_file = target_dir / f"{agent_id}.json"
    with open(target_file, 'w') as f:
        json.dump(agent_state, f, indent=2)
    
    print(f"  -> Sucesso! Artefato salvo em: {target_file}")

def main():
    parser = argparse.ArgumentParser(description="Migra agentes da estrutura legada para a nova estrutura de artefatos SAGA-016.")
    parser.add_argument("--source-dir", required=True, help="Diretório raiz contendo as pastas dos agentes legados (ex: projects/_common/agents).")
    parser.add_argument("--target-dir", required=True, help="Diretório de destino para salvar os novos artefatos JSON.")
    args = parser.parse_args()

    source_path = Path(args.source_dir)
    target_path = Path(args.target_dir)

    if not source_path.is_dir():
        print(f"ERRO: Diretório de origem não encontrado: {source_path}")
        return
    
    target_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Iniciando migração de agentes de '{source_path}' para '{target_path}'...")
    for agent_dir in source_path.iterdir():
        if agent_dir.is_dir():
            migrate_agent(agent_dir, target_path)
    
    print("Migração concluída.")

if __name__ == "__main__":
    main()
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `scripts/migrate_legacy_agents.py` for criado exatamente como especificado. O script deve ser executável e capaz de processar um diretório de agentes legados.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
