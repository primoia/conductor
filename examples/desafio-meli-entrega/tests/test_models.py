import pytest
from pydantic import ValidationError

from app.models.item import Item, ItemCreateModel


class TestItemModels:
    """Testes para validacao dos modelos Pydantic."""
    
    def test_item_create_model_valid(self):
        """Testa criacao de ItemCreateModel com dados validos."""
        valid_data = {
            "title": "Test Product",
            "price": 99.99,
            "currency_id": "BRL",
            "description": "A great test product",
            "condition": "new"
        }
        
        item = ItemCreateModel(**valid_data)
        
        assert item.title == "Test Product"
        assert item.price == 99.99
        assert item.currency_id == "BRL"
        assert item.condition == "new"
    
    def test_item_create_model_missing_required_field(self):
        """Testa erro quando campo obrigatorio esta ausente."""
        invalid_data = {
            "title": "Test Product",
            # price faltando
            "currency_id": "BRL",
            "description": "A great test product",
            "condition": "new"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ItemCreateModel(**invalid_data)
        
        assert "price" in str(exc_info.value)
    
    def test_item_create_model_invalid_price_type(self):
        """Testa erro com tipo invalido para preco."""
        invalid_data = {
            "title": "Test Product",
            "price": "invalid_price",  # string em vez de float
            "currency_id": "BRL", 
            "description": "A great test product",
            "condition": "new"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ItemCreateModel(**invalid_data)
        
        assert "price" in str(exc_info.value)
    
    def test_item_model_complete(self):
        """Testa criacao do modelo Item completo."""
        valid_data = {
            "id": "MLB12345678",
            "title": "Complete Test Product",
            "price": 199.99,
            "currency_id": "USD",
            "description": "A complete test product",
            "condition": "used"
        }
        
        item = Item(**valid_data)
        
        assert item.id == "MLB12345678"
        assert item.title == "Complete Test Product"
        assert item.price == 199.99
        assert item.currency_id == "USD"
        assert item.condition == "used"