# Especificação Técnica e Plano de Execução: 0012-criar-docker-compose-dev

#### **1. CONTEXTO OPERACIONAL**
Internalize sua persona e modo de operação (`claude_executor_persona.md`, `claude_executor_mode.md`). Opere como um executor literal.

#### **2. OBJETIVO ESTRATÉGICO (O "PORQUÊ")**
Esta tarefa cria um ambiente de desenvolvimento encapsulado e reprodutível com um único comando. Isso acelera drasticamente o onboarding de novos desenvolvedores e fornece uma plataforma estável e consistente para a execução de testes de integração, eliminando problemas de configuração de ambiente local.

#### **3. RESTRIÇÕES ARQUITETÔNICAS (REQUISITOS NÃO FUNCIONAIS)**
- **Localização:** O arquivo **DEVE** ser nomeado `docker-compose.yml` e localizado na raiz do projeto.
- **Hot-Reloading:** O serviço `conductor-service` **DEVE** montar o código-fonte local no contêiner para permitir o desenvolvimento iterativo sem a necessidade de reconstruir a imagem a cada mudança.
- **Rede:** Os serviços **DEVEM** se comunicar através de uma rede Docker customizada, não pela rede padrão.
- **Configuração:** A configuração do serviço, como a string de conexão do MongoDB, **DEVE** ser passada através de variáveis de ambiente.

#### **4. ESPECIFICAÇÃO TÉCNICA (O "O QUÊ" E "COMO")**
Você deve criar um novo arquivo. O conteúdo **DEVE** ser exatamente como especificado abaixo.

**Arquivo 1 (Novo): `docker-compose.yml`**
```yaml
version: '3.8'

services:
  conductor-service:
    build:
      context: .
      dockerfile: Dockerfile.service
    container_name: conductor_service
    ports:
      - "8000:8000" # Expondo uma porta para a futura API
    volumes:
      - ./src:/home/appuser/app/src # Montando o código para hot-reloading
    environment:
      - MONGODB_CONNECTION_STRING=mongodb://mongodb:27017/conductor
    networks:
      - conductor_net
    depends_on:
      - mongodb

  mongodb:
    image: mongo:5.0
    container_name: mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    networks:
      - conductor_net

networks:
  conductor_net:
    driver: bridge

volumes:
  mongodb_data:
```

#### **5. CRITÉRIOS DE ACEITAÇÃO**
Seu trabalho estará concluído quando o arquivo `docker-compose.yml` for criado na raiz do projeto exatamente como especificado.

#### **6. SINAL DE CONCLUSÃO**
Responda com: `TASK_COMPLETE`
