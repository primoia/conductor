from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, Architect! The foundation is solid."}


def test_get_item_success():
    """
    Testa o endpoint GET /api/v1/items/{item_id} com ID válido.
    
    Verifica se retorna status 200 e os dados corretos do item.
    """
    item_id = "MLB123456789"
    response = client.get(f"/api/v1/items/{item_id}")
    
    assert response.status_code == 200
    
    item_data = response.json()
    assert item_data["id"] == item_id
    assert item_data["title"] == "iPhone 14 Pro Max 128GB Azul Sierra"
    assert item_data["price"] == 6499.99
    assert item_data["currency_id"] == "BRL"
    assert item_data["condition"] == "new"
    assert "description" in item_data


def test_get_item_not_found():
    """
    Testa o endpoint GET /api/v1/items/{item_id} com ID inválido.
    
    Verifica se retorna status 404 e mensagem de erro apropriada.
    """
    invalid_item_id = "INVALID123"
    response = client.get(f"/api/v1/items/{invalid_item_id}")
    
    assert response.status_code == 404
    
    error_data = response.json()
    assert "detail" in error_data
    assert invalid_item_id in error_data["detail"]


def test_get_all_test_items():
    """
    Testa se todos os itens do arquivo de dados podem ser buscados com sucesso.
    """
    test_item_ids = ["MLB123456789", "MLB987654321", "MLB555444333"]
    
    for item_id in test_item_ids:
        response = client.get(f"/api/v1/items/{item_id}")
        assert response.status_code == 200
        
        item_data = response.json()
        assert item_data["id"] == item_id
        assert "title" in item_data
        assert "price" in item_data
        assert "currency_id" in item_data


def test_create_item_success():
    """
    Testa o endpoint POST /api/v1/items para criacao de um novo item.
    
    Verifica se retorna status 201 e o item criado com ID gerado.
    """
    new_item_payload = {
        "title": "Smartphone Samsung Galaxy S23",
        "price": 3499.99,
        "currency_id": "BRL",
        "description": "Smartphone Samsung Galaxy S23 com tela de 6.1 polegadas, camera de 50MP e processador Snapdragon 8 Gen 2.",
        "condition": "new"
    }
    
    response = client.post("/api/v1/items", json=new_item_payload)
    
    # Verifica status 201 Created
    assert response.status_code == 201
    
    # Verifica dados do item criado
    created_item = response.json()
    
    # Verifica se ID foi gerado (formato MLB + 8 caracteres)
    assert "id" in created_item
    assert created_item["id"].startswith("MLB")
    assert len(created_item["id"]) == 11  # MLB + 8 caracteres
    
    # Verifica se todos os dados enviados estao presentes
    assert created_item["title"] == new_item_payload["title"]
    assert created_item["price"] == new_item_payload["price"]
    assert created_item["currency_id"] == new_item_payload["currency_id"]
    assert created_item["description"] == new_item_payload["description"]
    assert created_item["condition"] == new_item_payload["condition"]
    
    # Verifica se o item pode ser recuperado por GET
    item_id = created_item["id"]
    get_response = client.get(f"/api/v1/items/{item_id}")
    assert get_response.status_code == 200
    
    retrieved_item = get_response.json()
    assert retrieved_item == created_item


def test_create_item_invalid_payload():
    """
    Testa erro de validacao com payload invalido.
    """
    invalid_payload = {
        "title": "Valid Title",
        # price faltando - campo obrigatorio
        "currency_id": "BRL",
        "description": "Valid description",
        "condition": "new"
    }
    
    response = client.post("/api/v1/items", json=invalid_payload)
    
    # Verifica status 422 Unprocessable Entity (erro de validacao)
    assert response.status_code == 422
    
    error_data = response.json()
    assert "detail" in error_data
    
    # Verifica se menciona o campo price
    error_details = str(error_data["detail"])
    assert "price" in error_details.lower()


def test_create_item_with_invalid_price():
    """
    Testa erro com tipo de dados invalido para price.
    """
    invalid_payload = {
        "title": "Valid Title",
        "price": "not_a_number",  # tipo invalido
        "currency_id": "BRL", 
        "description": "Valid description",
        "condition": "new"
    }
    
    response = client.post("/api/v1/items", json=invalid_payload)
    
    assert response.status_code == 422
    error_data = response.json()
    assert "detail" in error_data


def test_item_lifecycle_e2e():
    """
    Teste End-to-End completo do ciclo de vida de um item.
    
    Testa todas as operacoes CRUD em sequencia:
    CREATE -> READ -> UPDATE -> READ -> DELETE -> READ (404)
    """
    # 1. CREATE: Criar um novo item
    create_payload = {
        "title": "E2E Test Product",
        "price": 299.99,
        "currency_id": "USD",
        "description": "Product for end-to-end testing",
        "condition": "new"
    }
    
    create_response = client.post("/api/v1/items", json=create_payload)
    assert create_response.status_code == 201
    
    created_item = create_response.json()
    item_id = created_item["id"]
    assert item_id.startswith("MLB")
    
    # 2. READ (Verify Create): Verificar se item foi criado corretamente
    read_response_1 = client.get(f"/api/v1/items/{item_id}")
    assert read_response_1.status_code == 200
    
    read_item_1 = read_response_1.json()
    assert read_item_1["title"] == create_payload["title"]
    assert read_item_1["price"] == create_payload["price"]
    assert read_item_1["condition"] == create_payload["condition"]
    
    # 3. UPDATE: Atualizar preco e descricao do item
    update_payload = {
        "price": 399.99,
        "description": "Updated description for E2E testing"
    }
    
    update_response = client.put(f"/api/v1/items/{item_id}", json=update_payload)
    assert update_response.status_code == 200
    
    updated_item = update_response.json()
    assert updated_item["price"] == update_payload["price"]
    assert updated_item["description"] == update_payload["description"]
    # Outros campos devem permanecer inalterados
    assert updated_item["title"] == create_payload["title"]
    assert updated_item["condition"] == create_payload["condition"]
    
    # 4. READ (Verify Update): Verificar se atualizacao foi persistida
    read_response_2 = client.get(f"/api/v1/items/{item_id}")
    assert read_response_2.status_code == 200
    
    read_item_2 = read_response_2.json()
    assert read_item_2["price"] == 399.99
    assert read_item_2["description"] == "Updated description for E2E testing"
    assert read_item_2["title"] == create_payload["title"]  # Nao mudou
    
    # 5. DELETE: Remover o item
    delete_response = client.delete(f"/api/v1/items/{item_id}")
    assert delete_response.status_code == 204
    
    # Verifica se resposta esta vazia (No Content)
    assert delete_response.content == b""
    
    # 6. READ (Verify Delete): Verificar se item foi removido
    read_response_3 = client.get(f"/api/v1/items/{item_id}")
    assert read_response_3.status_code == 404
    
    error_data = read_response_3.json()
    assert "detail" in error_data
    assert item_id in error_data["detail"]
