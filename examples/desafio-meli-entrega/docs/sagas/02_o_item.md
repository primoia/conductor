### **Plano de Arquitetura: Saga 02 - O Item**

**Objetivo:**
Implementar a lógica de dados, o serviço e o endpoint principal para buscar os detalhes de um item, conforme especificado nos requisitos do desafio. Faremos isso seguindo uma arquitetura limpa e implementando a estratégia de logging que planejamos.

**Estado Inicial:**
A fundação concluída da Saga 01.

**Estado Final Desejado:**
*   A aplicação terá um sistema de logging configurado e funcional.
*   A API terá um endpoint `GET /api/v1/items/{item_id}`.
*   Ao ser chamado com um ID válido, o endpoint retornará os dados de um item a partir de um arquivo `items.json`.
*   Ao ser chamado com um ID inválido, o endpoint retornará um erro `404 Not Found` com uma mensagem clara.
*   A lógica de negócio estará devidamente separada da camada de acesso a dados e da camada de API.
*   O novo código será coberto por testes de unidade e de integração.

---

### **Passos de Implementação (Blueprint para o Implementador):**

**1. Estrutura de Arquivos e Diretórios:**
   - [X] Criar a estrutura de diretórios: `app/api/v1`, `app/core`, `app/models`, `app/repository`, `app/services`, `data`.
   - [X] Criar os arquivos Python vazios (`__init__.py` quando necessário):
     - `app/api/v1/items.py`
     - `app/core/logging_config.py`
     - `app/models/item.py`
     - `app/repository/item_repository.py`
     - `app/services/item_service.py`
   - [X] Criar o arquivo de dados vazio: `data/items.json`.

**2. Implementar a Estratégia de Logging:**
   - [X] Em `app/core/logging_config.py`, criar uma função que configure o `logging` do Python para `stdout` com um formato claro.
   - [X] Em `app/main.py`, importar e chamar a função de configuração de logging na inicialização da aplicação.

**3. Definir o Contrato de Dados (Model):**
   - [X] Em `app/models/item.py`, definir a classe `Item` usando Pydantic.
   - [X] Campos sugeridos: `id: str`, `title: str`, `price: float`, `currency_id: str`, `description: str`, `condition: str`.

**4. Criar o "Banco de Dados" Falso:**
   - [X] Popular o arquivo `data/items.json` com uma lista contendo 2 ou 3 objetos de item de exemplo.

**5. Implementar a Camada de Acesso a Dados (Repository):**
   - [X] Em `app/repository/item_repository.py`, criar a classe `ItemRepository`.
   - [X] Esta classe deve ler o arquivo `data/items.json` em sua inicialização.
   - [X] Implementar o método `find_by_id(self, item_id: str) -> Item | None`.

**6. Implementar a Lógica de Negócio (Service):**
   - [X] Em `app/services/item_service.py`, criar uma exceção customizada `ItemNotFoundException`.
   - [X] Criar a classe `ItemService`, que depende de `ItemRepository`.
   - [X] Implementar o método `get_item_by_id(self, item_id: str) -> Item`, que chama o repositório e levanta `ItemNotFoundException` se o item não for encontrado.

**7. Expor o Endpoint (API):**
   - [X] Em `app/api/v1/items.py`, criar um `APIRouter`.
   - [X] Implementar o endpoint `GET /items/{item_id}` que injeta a dependência do `ItemService`.
   - [X] O endpoint deve chamar o serviço e retornar o item.
   - [X] Implementar um `exception_handler` no `app/main.py` para capturar `ItemNotFoundException` e retornar uma resposta `HTTP 404`.
   - [X] Incluir o novo router no `app/main.py` com o prefixo `/api/v1`.

**8. Implementar Testes:**
   - [X] Em `tests/test_api.py`, escrever testes de integração para o endpoint `/api/v1/items/{item_id}`, cobrindo:
     - Caso de sucesso com um ID válido (retorno 200 e o JSON correto).
     - Caso de falha com um ID inválido (retorno 404).

**9. Registrar o Marco (Commit):**
   - [X] Ao final de todos os passos, fazer um commit com uma mensagem clara, como `feat(items): implement get item details endpoint`.
