# Especificação Técnica e Plano de Execução: 0028-depreciar-workspaces-yaml

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal de comandos e edições de código.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa elimina uma fonte de configuração legada e conflitante, consolidando o `config.yaml` como a única fonte da verdade. Isso simplifica a arquitetura, reduz a complexidade para novos desenvolvedores e previne bugs causados por configurações obsoletas.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Remoção Segura:** Antes da renomeação, uma busca no código **DEVE** ser feita para garantir que nenhuma lógica ativa ainda depende deste arquivo.
- **Comunicação Clara:** A renomeação e a adição de um comentário de depreciação **DEVEM** comunicar claramente que o arquivo não está mais em uso.
- **Validação:** A remoção da lógica **NÃO DEVE** quebrar nenhum teste existente.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve executar os seguintes passos em ordem.

**Passo 1: Busca por Usos (Verificação)**
Execute o seguinte comando para procurar por usos do arquivo. A expectativa é que, após as refatorações da Fase III, nenhum resultado seja encontrado em `src/`.
```bash
grep -r "workspaces.yaml" .
```

**Passo 2: Renomear o Arquivo**
Execute o seguinte comando para renomear o arquivo, marcando-o como depreciado.
```bash
mv config/workspaces.yaml config/workspaces.yaml.DEPRECATED
```

**Passo 3: Adicionar o Aviso de Depreciação**
Modifique o arquivo recém-renomeado para adicionar um aviso no topo.

**Arquivo 1 (Modificar): `config/workspaces.yaml.DEPRECATED`**
```yaml
# AVISO: ESTE ARQUIVO ESTÁ DEPRECIADO E NÃO É MAIS UTILIZADO PELO SISTEMA.
# A descoberta de agentes e projetos agora é gerenciada pelo ConductorService,
# que utiliza o backend de armazenamento configurado no `config.yaml` principal.
# Este arquivo é mantido apenas para referência histórica.

# ... (conteúdo original do workspaces.yaml) ...
```

**Passo 4: Validar a Estabilidade**
Execute a suíte de testes completa para garantir que a remoção do arquivo não quebrou nenhuma funcionalidade.
```bash
poetry run pytest
```
A execução deve ser bem-sucedida.

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `workspaces.yaml` for renomeado, seu conteúdo atualizado com o aviso de depreciação, e a suíte de testes completa passar com sucesso.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
