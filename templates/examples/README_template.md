# 🎼 {{project_name}} - Conductor Example Project

Bem-vindo ao seu projeto criado pelo **{{team_name}}**!

## 📋 Informações do Projeto

- **Nome:** {{project_name}}
- **Ambiente:** {{environment}}
- **Team Template:** {{team_name}}
- **Diretório:** `{{project_root}}`
- **Criado em:** {{generated_at}}

## 🤖 Agentes Configurados

{{#agents_list}}
- **{{agent_id}}**: Localizado em `{{agent_path}}`
{{/agents_list}}

## 📁 Arquivos de Exemplo Criados

{{#created_files}}
- `{{file_path}}`: {{file_description}}
{{/created_files}}

## 🚀 Como Usar

### Modo Interativo (Conversar com um agente)
```bash
# Incorporar um agente específico
python scripts/genesis_agent.py --embody [AGENT_ID] --project-root {{project_root}} --repl
```

### Modo Automático (Executar workflows)
```bash
# Executar um workflow pré-configurado
python scripts/run_conductor.py --projeto {{project_root}} workflows/[WORKFLOW_NAME].yaml
```

## 🎯 Próximos Passos

1. **Explore os agentes**: Use o modo interativo para conversar com cada agente
2. **Execute workflows**: Use os workflows pré-configurados para tarefas comuns  
3. **Customize**: Modifique os agent.yaml conforme suas necessidades
4. **Teste os exemplos**: Execute os arquivos de exemplo criados

## 📚 Documentação

- [Maestro Framework Documentation](../docs/)
- [Agent Configuration Guide](../docs/agents/)
- [Workflow Creation Guide](../docs/workflows/)

---
*Gerado automaticamente pelo Conductor Onboarding System v{{system_version}}*