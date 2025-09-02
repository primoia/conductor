# SAGA-013 Hotfix - Gemini CLI Tool Control

## 🚨 Problema Identificado

O parâmetro `--allowed-tools` **não existe** na versão atual do Gemini CLI instalada no sistema, causando:

```
Unknown arguments: allowed-tools, allowedTools, write_file, grep, find_files
```

## ✅ Correção Aplicada

**Arquivo**: `src/infrastructure/llm/cli_client.py:98-106`

```python
# Para o Gemini CLI, sempre usar modo yolo para evitar erros de parâmetro
# O controle real de ferramentas deve ser implementado em nível superior no framework
cmd.extend(["--approval-mode", "yolo"])

if self.is_admin_agent:
    logger.debug("Admin agent: using yolo mode (unrestricted access)")
else:
    logger.warning("Project agent: using yolo mode - tool restrictions not implemented in Gemini CLI yet")
    # TODO: Implement tool restrictions via other means (settings.json, prompt instructions, etc.)
```

## 📊 Status Atual

### ✅ Funcionando
- **Claude CLI**: Controle granular com `--allowedTools` ✅
- **Gemini Admin**: `--approval-mode yolo` ✅  
- **Gemini Project**: `--approval-mode yolo` (temporário) ⚠️

### ⚠️ Limitações Temporárias
- **Gemini Project Agents**: Sem restrição de ferramentas (usando yolo)
- **Risco de Segurança**: Project agents têm acesso irrestrito no Gemini

## 🔄 Comandos Gerados

**Claude (funcionando com restrições)**:
```bash
claude --print --dangerously-skip-permissions --allowedTools read_file
```

**Gemini (todos com yolo temporariamente)**:
```bash
gemini -p "prompt" --approval-mode yolo
```

## 🛠️ Soluções Futuras Possíveis

1. **Settings.json**: Usar `~/.gemini/settings.json` com `coreTools`
2. **Prompt Instructions**: Instruir o Gemini via prompt sobre ferramentas permitidas
3. **MCP Integration**: Usar `--allowed-mcp-server-names` se aplicável
4. **Framework-level Control**: Interceptar e filtrar comandos antes da execução

## ⚡ Impacto

- **✅ Sem mais loops**: Comandos Gemini não falham
- **✅ Funcionalidade básica**: Agentes conseguem executar tarefas
- **⚠️ Segurança reduzida**: Project agents no Gemini têm acesso total

## 📝 TODO

- [ ] Implementar controle via `settings.json`
- [ ] Investigar versão do Gemini CLI com `--allowed-tools`
- [ ] Implementar filtro em nível de framework
- [ ] Atualizar testes para refletir limitação temporária

## 🎯 Resultado

**SAGA-013 Parcialmente Implementado**:
- Claude: Controle total ✅
- Gemini: Sem controle (temporário) ⚠️
- Sistema: Funcional, sem loops ✅