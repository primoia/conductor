### **Plano de Projeto Final: Conclusão do Desafio**

#### **Saga 3.1: CRUD Completo e Testes de Ciclo de Vida**

**Objetivo:**
Completar a funcionalidade da API implementando as operações de modificação de estado (`Update` e `Delete`) e validar todo o ciclo de vida de um recurso com um teste End-to-End.

**Blueprint para o Implementador (Claude):**

**1. Estender a Camada de Persistência (`Repository`):**
   - **Local:** `app/repository/item_repository.py`
   - **Ação:** Implementar o método `delete(self, item_id: str) -> bool`.
   - **Lógica:** Ler o arquivo JSON, remover o item com o `item_id` correspondente, e reescrever o arquivo. Retornar `True` se um item foi removido, `False` caso contrário.

**2. Estender a Lógica de Negócio (`Service`):**
   - **Local:** `app/models/item.py`
   - **Ação:** Criar o modelo Pydantic `ItemUpdateModel`, onde todos os campos são opcionais, para representar o payload de uma atualização.
   - **Local:** `app/services/item_service.py`
   - **Ação:** Implementar o método `update_item(self, item_id: str, item_data: ItemUpdateModel) -> Item`.
     - **Lógica:** Buscar o item existente. Se não encontrar, levantar `ItemNotFoundException`. Atualizar os campos do item com os dados recebidos e salvar o item atualizado usando o repositório.
   - **Ação:** Implementar o método `delete_item(self, item_id: str) -> None`.
     - **Lógica:** Chamar o método `delete` do repositório. Se ele retornar `False` (indicando que o item não existia), levantar `ItemNotFoundException`.

**3. Expor os Endpoints da API:**
   - **Local:** `app/api/v1/items.py`
   - **Ação:** Implementar o endpoint `PUT /items/{item_id}`. Ele deve chamar o `item_service.update_item` e retornar o item atualizado com status `200 OK`.
   - **Ação:** Implementar o endpoint `DELETE /items/{item_id}`. Ele deve chamar o `item_service.delete_item` e retornar uma resposta vazia com status `204 No Content`.

**4. Implementar o Teste de Ciclo de Vida E2E:**
   - **Local:** `tests/test_api.py` (ou um novo arquivo `tests/test_e2e.py`).
   - **Ação:** Criar o teste `test_item_lifecycle_e2e`.
   - **Fluxo do Teste:**
     1.  **CREATE:** Fazer `POST` para `/items` para criar um novo item. Validar status `201` e guardar o `id`.
     2.  **READ (Verify Create):** Fazer `GET` para `/items/{id}` e validar se os dados correspondem.
     3.  **UPDATE:** Fazer `PUT` para `/items/{id}` com um novo `price`. Validar status `200` e o corpo da resposta.
     4.  **READ (Verify Update):** Fazer `GET` para `/items/{id}` novamente e validar se o `price` foi atualizado.
     5.  **DELETE:** Fazer `DELETE` para `/items/{id}`. Validar status `204`.
     6.  **READ (Verify Delete):** Fazer `GET` para `/items/{id}` e validar que o status agora é `404 Not Found`.

**5. Registrar o Marco:**
   - **Ação:** Realizar um commit com a mensagem `feat(items): implement update and delete endpoints`.

---

#### **Saga 04: Documentação e Empacotamento Final**

**Objetivo:**
Realizar a revisão final de todos os artefatos do projeto, aprimorar a documentação para atender 100% aos requisitos do briefing e preparar o projeto para a entrega.

**Blueprint para o Arquiteto (Gemini):**

**1. Criar o Diagrama de Arquitetura:**
   - **Ação:** Desenvolver um diagrama de componentes simples usando a sintaxe Mermaid.
   - **Conteúdo:** O diagrama ilustrará visualmente a interação entre as camadas: `API Layer` -> `Service Layer` -> `Repository Layer` -> `Data (JSON)`.
   - **Entrega:** O diagrama será inserido em uma nova seção no `README.md`.

**2. Finalizar a Documentação Principal (`README.md`):**
   - **Ação:** Adicionar a seção "Diagrama de Arquitetura".
   - **Ação:** Adicionar uma seção "Plano de Projeto", explicando que o plano de desenvolvimento incremental está detalhado nos documentos da pasta `docs/sagas/`.
   - **Ação:** Fazer uma revisão completa de todo o `README.md` para garantir clareza, consistência e profissionalismo.

**3. Revisão Final dos Documentos de Suporte:**
   - **Ação:** Revisar `run.md` e `prompts.md` para garantir que estejam atualizados e claros.

**4. Preparar para a Entrega:**
   - **Ação:** Após a conclusão de todas as sagas de código e documentação, instruir a criação do arquivo `.zip` final para submissão, garantindo que nenhum arquivo desnecessário (como `.venv`, `__pycache__`) seja incluído.
