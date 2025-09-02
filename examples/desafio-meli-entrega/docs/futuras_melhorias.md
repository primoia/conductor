# Roadmap de Futuras Melhorias

Este documento descreve um roadmap de melhorias potenciais que poderiam ser implementadas para evoluir este projeto de um protótipo robusto para um sistema de produção completo, resiliente e escalável.

---

### 1. Aprimoramento da Camada de Persistência

-   **Banco de Dados Real:** Substituir o `ItemRepository` baseado em arquivo JSON por uma implementação que se conecte a um banco de dados real.
    -   **SQL:** Usar PostgreSQL com SQLAlchemy para garantir transações atômicas e consistência forte.
    -   **NoSQL:** Usar MongoDB para maior flexibilidade no esquema de dados.
-   **Cache Distribuído:** Introduzir uma camada de cache (como Redis) na frente do banco de dados para otimizar drasticamente as operações de leitura (`GET`), diminuindo a latência para itens frequentemente acessados.

### 2. Robustez da API e Segurança

-   **Autenticação e Autorização:** Implementar um mecanismo de autenticação (ex: OAuth2 com JWT) para proteger os endpoints de escrita (`POST`, `PUT`, `DELETE`), garantindo que apenas usuários/serviços autorizados possam modificar os dados.
-   **Rate Limiting:** Adicionar um limitador de requisições para prevenir abuso e ataques de negação de serviço (DoS).
-   **Versionamento de API:** Evoluir o versionamento da API (ex: de `/api/v1` para `/api/v2`) para permitir mudanças significativas sem quebrar a compatibilidade com clientes antigos.

### 3. Expansão da Cobertura de Testes

-   **Testes de Mutação:** Introduzir testes de mutação (com ferramentas como `mutmut`) para verificar a eficácia da nossa suíte de testes, garantindo que os testes falhem se a lógica do código for alterada indevidamente.
-   **Testes de Contrato:** Se esta API fosse consumida por outro serviço, poderíamos implementar testes de contrato (usando uma ferramenta como Pact) para garantir que as integrações não quebrem.
-   **Testes de Performance:** Realizar testes de carga e estresse (com ferramentas como Locust ou k6) para entender os limites da aplicação sob alta demanda e identificar gargalos de performance.

### 4. Infraestrutura e Deploy (CI/CD)

-   **Proxy Reverso com Nginx:** Introduzir o Nginx como um proxy reverso na frente da aplicação para gerenciar o tráfego de entrada, servir arquivos estáticos e lidar com a terminação SSL (HTTPS), liberando o servidor de aplicação Python dessa responsabilidade.
-   **Pipeline de CI/CD:** Criar um pipeline automatizado (ex: com GitHub Actions) que, a cada push para a branch principal, execute o linting, os testes e, se passarem, construa e publique a imagem Docker em um registro (como o Docker Hub ou AWS ECR).
-   **Orquestração de Containers:** Para um ambiente de produção real, migrar do Docker Compose para um orquestrador mais robusto como Kubernetes, permitindo auto-scaling, rolling updates e alta disponibilidade.

### 5. Observabilidade Avançada

-   **Métricas:** Implementar a exportação de métricas (usando `Prometheus-FastAPI-Instrumentator`) para monitoramento em tempo real da saúde da aplicação (latência, taxa de erros, requisições por segundo) em dashboards (com Grafana).
-   **Tracing Distribuído:** Se o sistema evoluísse para uma arquitetura de microsserviços, integrar OpenTelemetry para permitir o rastreamento de requisições através dos diferentes serviços, facilitando a depuração de problemas complexos.
