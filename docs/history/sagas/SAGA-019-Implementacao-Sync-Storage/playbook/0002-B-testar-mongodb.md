# Plano: 0002-B - Testar Integração com MongoDB

**Objetivo:** Validar funcionalidade completa com MongoDB, incluindo configuração do .env e testes bidirecionais.

**Status:** PRÓXIMO PASSO

**Executor:** Usuário (primeira experiência com MongoDB)

---

### Pré-requisitos

- [ ] **1. MongoDB Instalado e Rodando:**
  ```bash
  # Ubuntu/Debian
  sudo systemctl start mongod
  sudo systemctl status mongod
  
  # Docker (alternativa)
  docker run -d --name conductor-mongo -p 27017:27017 mongo:latest
  ```

- [ ] **2. Configurar .env:**
  ```bash
  # Adicionar ao .env
  MONGO_URI=mongodb://localhost:27017
  MONGO_DATABASE=conductor_state
  MONGO_COLLECTION=agent_states
  ```

- [ ] **3. Instalar Dependências Python:**
  ```bash
  pip install pymongo
  ```

### Testes Recomendados

#### **Teste 1: Backup Filesystem → MongoDB**
```bash
# Backup seguro (sem alterar config.yaml)
conductor --migrate-to mongodb --no-config-update
```

**Resultado Esperado:**
- ✅ Conectividade MongoDB verificada
- ✅ 19 agentes transferidos
- ✅ config.yaml preservado (type=filesystem)

#### **Teste 2: Restore MongoDB → Filesystem**
```bash
# Simular perda da RAMDisk
rm -rf .conductor_workspace/agents/TestAgent

# Restore do MongoDB (sem alterar config)
conductor --migrate-to filesystem --no-config-update

# Verificar se TestAgent voltou
ls .conductor_workspace/agents/TestAgent
```

#### **Teste 3: Migração Permanente**
```bash
# Migração definitiva para MongoDB
conductor --migrate-to mongodb

# Verificar se config.yaml foi atualizado
cat config.yaml  # deve mostrar type: mongodb
```

#### **Teste 4: Coexistência com Backup SSD**
```bash
# Backup tradicional ainda deve funcionar
conductor --backup

# Verificar se rsync funcionou
ls ~/conductor_backup/.conductor_workspace/agents/
```

### Troubleshooting

**Erro: "MongoDB não configurado"**
- Verificar MONGO_URI no .env
- Testar conexão: `mongo mongodb://localhost:27017`

**Erro: "MongoDB não acessível"**
- Verificar se mongod está rodando
- Verificar firewall/portas

**Erro: "ModuleNotFoundError: pymongo"**
- Instalar: `pip install pymongo`

### Validação Final

- [ ] Backup RAMDisk → MongoDB funciona
- [ ] Restore MongoDB → RAMDisk funciona  
- [ ] Migração permanente funciona
- [ ] config.yaml atualizado corretamente
- [ ] Backup SSD tradicional ainda funciona
- [ ] Logs detalhados mostram progresso
