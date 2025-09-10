### Plano de Execução: Estágio 15 - Atualizar o Container de Injeção de Dependência

#### Contexto Arquitetônico

O arquivo `src/container.py` atua como nosso "hub" de Injeção de Dependência, responsável por construir e fornecer instâncias de serviços para a aplicação. Atualmente, ele sabe como construir o `AgentLogic` legado. Para que os CLIs possam usar o novo `ConductorService`, precisamos ensinar o container a construir e fornecer uma instância singleton do nosso novo serviço.

#### Propósito Estratégico

O objetivo é centralizar a lógica de construção de objetos complexos e garantir que toda a aplicação use a mesma instância (singleton) do `ConductorService`. Isso evita estados inconsistentes e garante que a configuração seja carregada e as ferramentas sejam registradas apenas uma vez na inicialização da aplicação. Este estágio prepara o terreno para que os CLIs possam simplesmente "pedir" pelo serviço, sem precisar saber como construí-lo.

#### Checklist de Execução

- [ ] Abrir o arquivo `src/container.py`.
- [ ] Importar a classe `ConductorService`.
- [ ] Adicionar um novo método ou propriedade ao `container` que constrói uma instância de `ConductorService`.
- [ ] Implementar a lógica para garantir que esta instância seja um singleton (ou seja, é criada apenas na primeira vez que é solicitada e reutilizada nas chamadas subsequentes).
- [ ] Garantir que o container possa ser inicializado sem erros.
