### Plano de Execução: Estágio 31 - Atualizar o `README.md` Principal

#### Contexto Arquitetônico

O `README.md` na raiz do projeto é o primeiro ponto de contato para qualquer pessoa que chegue ao repositório. Atualmente, ele reflete a arquitetura legada, com instruções de uso focadas nos CLIs `admin.py` e `agent.py` e sua lógica de diretórios fixos. Com a conclusão da migração, este documento está perigosamente desatualizado.

#### Propósito Estratégico

O objetivo é alinhar a documentação de "porta de entrada" do projeto com a nova realidade arquitetônica. Um `README.md` claro e preciso é crucial para o sucesso de um projeto de código aberto. Ele deve explicar a nova filosofia, o papel do `config.yaml` como fonte da verdade, e como usar o sistema sob o novo paradigma unificado, mesmo que através dos CLIs legados.

#### Checklist de Execução

- [ ] Abrir o arquivo `README.md` na raiz do projeto.
- [ ] Reescrever a seção "Como Usar" ou "Getting Started".
- [ ] As novas instruções devem focar na configuração do `config.yaml` como o primeiro passo.
- [ ] Explicar brevemente o conceito do `ConductorService` como o novo núcleo.
- [ ] Manter os exemplos de como rodar `admin.py` e `agent.py`, mas explicar que eles agora operam sob a nova arquitetura.
- [ ] Remover referências à estrutura de diretórios rígida como sendo a única forma de operação.
- [ ] Adicionar uma menção ao novo sistema de "Tool Plugins".
