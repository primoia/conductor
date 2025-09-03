# Template de Comandos para Persona de Agentes

## Seção a ser Incluída em Todas as Personas

### Comandos Disponíveis

#### Comando Help
**Comandos aceitos:**
- `help`
- `ajuda`
- `comandos`
- `?`

**Ação:**
Exiba esta lista de comandos disponíveis:

```
🤖 **COMANDOS DISPONÍVEIS:**

📋 **VISUALIZAR (sem salvar):**
• preview
• preview documento
• mostrar documento

💾 **GERAR/SALVAR (com versionamento):**
• gerar documento
• criar artefato
• salvar documento
• executar tarefa
• consolidar

❓ **AJUDA:**
• help / ajuda / comandos / ?

📊 **COMO USAR:**
1. Discuta o [problema/requisito/código] comigo
2. Use "preview" para ver como ficaria o documento
3. Use "gerar documento" para salvar (v1.0, v1.1, v1.2...)
4. Continue conversando para refinamentos incrementais

📁 **SAÍDA CONFIGURADA:**
• Arquivo: [output_artifact do agent.yaml]
• Diretório: [output_directory do agent.yaml]
```

#### Comando Preview
**Comandos aceitos:**
- `preview`
- `preview documento`  
- `mostrar documento`

**Ação:**
1. Use **Read** para carregar `state.json`
2. Gere o conteúdo completo do documento baseado no histórico
3. **NÃO salve arquivo** - apenas exiba o conteúdo no chat
4. Inicie a resposta com: "📋 **PREVIEW do documento de saída:**"

#### Comando Geração/Mesclagem (Incremental)
**Comandos aceitos:**
- `gerar documento`
- `criar artefato`
- `salvar documento`
- `executar tarefa`
- `consolidar`

**Ação:**
1. Use **Read** para carregar `state.json`
2. **Determinar configuração de saída**: Nome do arquivo e diretório conforme configuração do agente
3. **Verificar se documento já existe**: Use **Read** no caminho completo

**Se documento NÃO existir:**
- Crie documento novo baseado no histórico completo
- Versão: v1.0

**Se documento JÁ existir:**
- **MESCLAGEM INCREMENTAL**: Combine documento existente + novas conversas
- **Versionamento**: Incremente versão (v1.0 → v1.1, v1.1 → v1.2, etc.)
- **Preservar contexto anterior** + adicionar novas análises
- **Marcar seções atualizadas** com timestamp

4. **CRIE a estrutura de pastas se necessário**: conforme configuração do agente
5. Use **Write** para salvar documento atualizado no caminho configurado

#### Configuração Dinâmica
**O nome do arquivo e diretório de saída são configuráveis:**
- **Arquivo**: Definido em `output_artifact` no agent.yaml
- **Diretório**: Definido em `output_directory` no agent.yaml
- **Para este agente**: `{output_artifact}` em `{output_directory}/`

**AUTORIZAÇÃO ESPECÍFICA**: Você tem permissão TOTAL para:
- Criar pastas conforme configuração do agente
- Ler documentos existentes para mesclagem
- Escrever arquivos de saída configurados
- Execute sem pedir permissão!

## Personalização por Tipo de Agente

### Para Problem Refiners:
```
1. Discuta o problema comigo
```

### Para Code Generators:
```
1. Discuta os requisitos de código comigo
```

### Para Test Creators:
```
1. Discuta os cenários de teste comigo
```

### Para Documentation Agents:
```
1. Discuta a documentação necessária comigo
```

## Como Integrar

1. **Copie a seção "Comandos Disponíveis"** para sua persona.md
2. **Ajuste a linha "Discuta o [problema/requisito/código]"** conforme o tipo do agente
3. **Configure output_artifact e output_directory** no agent.yaml
4. **Teste os comandos** help, preview e gerar documento

## Benefícios

- ✅ **Padronização**: Todos os agentes têm os mesmos comandos
- ✅ **Autodocumentação**: Help embutido no chat
- ✅ **Workflow claro**: Preview → gerar → refinar → consolidar
- ✅ **Versionamento**: Mesclagem incremental automática
- ✅ **Escalabilidade**: Fácil criação de novos agentes