### **Plano de Arquitetura: Saga 03 - Configuração e Modificação de Estado**

**Objetivo:**
Evoluir a aplicação em duas frentes de maturidade: externalizar configurações para um ambiente `.env` e implementar a capacidade de modificar o estado da aplicação através de um endpoint `POST`.

**Estado Inicial:**
A implementação da Saga 02 concluída, com endpoint de leitura e logging estruturado.

**Estado Final Desejado:**
*   A aplicação carregará configurações (como o caminho para o arquivo de dados) a partir de um arquivo `.env`, eliminando valores "hardcoded".
*   A API terá um endpoint `POST /api/v1/items` para criar novos itens.
*   A criação de um item resultará na sua persistência no arquivo `items.json`.
*   A resposta para uma criação bem-sucedida será `HTTP 201 Created`, contendo os dados do novo item, incluindo seu ID gerado.
*   A nova funcionalidade será coberta por testes de integração.

---

### **Passos de Implementação (Blueprint para o Implementador):**

**1. Implementar Configuração Centralizada:**
   - [X] Adicionar a dependência `pydantic-settings` ao projeto com `poetry add pydantic-settings`.
   - [X] Criar um arquivo `.env` na raiz do projeto (e garantir que esteja no `.gitignore`).
   - [X] No arquivo `.env`, definir a variável: `DATA_FILE_PATH="data/items.json"`.
   - [X] No módulo `app/core/config.py`, criar uma classe `Settings` que herda de `BaseSettings` (da `pydantic_settings`) para carregar as configurações.
   - [X] Refatorar o `ItemRepository` para receber a instância de `Settings` via injeção de dependência e usar `settings.DATA_FILE_PATH`.

**2. Estender a Camada de Persistência para Escrita:**
   - [X] No `ItemRepository`, criar um novo método `save(self, item: Item) -> Item`.
   - [X] **Lógica do método `save`:**
     1.  Ler todos os itens do arquivo `items.json`.
     2.  Adicionar/atualizar o novo item na estrutura de dados em memória.
     3.  Reescrever o arquivo `items.json` inteiro com os dados atualizados.
     4.  Retornar o item salvo.

**3. Estender a Lógica de Negócio para Criação:**
   - [X] Em `app/models/item.py`, criar um novo modelo Pydantic, `ItemCreateModel`, que contém todos os campos de `Item` **exceto** o `id`.
   - [X] Em `app/services/item_service.py`, criar um novo método `create_item(self, item_data: ItemCreateModel) -> Item`.
   - [X] **Lógica do método `create_item`:**
     1.  Gerar um novo ID único para o item (sugestão: usar a biblioteca `uuid` e `f"MLB{uuid.uuid4()}"`).
     2.  Criar uma instância completa do modelo `Item` a partir do `item_data` e do novo `id`.
     3.  Chamar o método `self.item_repository.save()` para persistir o novo item.
     4.  Retornar o item recém-criado.

**4. Expor o Endpoint de Criação:**
   - [X] Em `app/api/v1/items.py`, adicionar um novo endpoint `POST /items`.
   - [X] O endpoint deve receber o modelo `ItemCreateModel` no corpo da requisição.
   - [X] A função do endpoint deve chamar `item_service.create_item`.
   - [X] A resposta deve ter o código de status `201 Created`.

**5. Adicionar Testes para a Nova Funcionalidade:**
   - [X] Em `tests/test_api.py`, adicionar um novo teste `test_create_item_success`.
   - [X] **Lógica do teste:**
     1.  Definir um payload JSON para um novo item.
     2.  Fazer uma requisição `POST` para `/api/v1/items` com o payload.
     3.  Verificar se o código de status da resposta é `201`.
     4.  Verificar se o corpo da resposta contém os dados enviados e um campo `id` que não estava no payload original.

**6. Registrar o Marco (Commit):**
   - [X] Ao final, fazer um commit com uma mensagem clara, como `feat(items): implement create item endpoint and settings module`.
