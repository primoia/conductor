# Plano de Ação para o Agente do Projeto `conductor`

**Para:** Agente Executor (Contexto: Projeto `conductor`)
**De:** Arquiteto de Software (Gemini)
**Assunto:** Garantir a configuração correta de `docker-compose.yml` para integração com a stack de observabilidade externa.

---

### 1. Contexto

Seu objetivo é garantir que o `docker-compose.yml` do projeto `conductor` defina **apenas** o seu próprio serviço (`conductor-api`) e que ele se conecte a uma rede Docker externa, onde a stack de observabilidade reside. Isso garante que o projeto `conductor` seja um "cliente" da stack central, e não o seu "dono".

### 2. Plano de Execução

**Passo Único: Validar e Corrigir o `docker-compose.yml` do Projeto**

Substitua o conteúdo do seu `docker-compose.yml` local pelo conteúdo abaixo. Isso garante que a definição do serviço e, principalmente, da rede externa (`external: true`) esteja correta.

**Comando:**
```bash
cat << 'EOF' > /mnt/ramdisk/primoia-main/primoia-monorepo/projects/conductor/docker-compose.yml
version: '3.8'

services:
  conductor-api:
    build: .
    container_name: conductor-api-1
    ports:
      - "8001:8000"
    volumes:
      - .:/app
    env_file:
      - .env
    logging:
      driver: loki
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
        loki-external-labels: "container_name={{.Name}}"
    networks:
      - primoia-network

networks:
  primoia-network:
    name: primoia-monorepo_primoia-network
    external: true
EOF
```

### 3. Validação

Após a execução, a sua tarefa está concluída. A validação final ocorrerá quando o agente do monorepo também completar sua tarefa e ambos os serviços forem iniciados.
