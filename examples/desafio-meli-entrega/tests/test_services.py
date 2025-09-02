import pytest
from unittest.mock import Mock, patch
import uuid

from app.services.item_service import ItemService, ItemNotFoundException
from app.models.item import Item, ItemCreateModel
from app.repository.item_repository import ItemRepository


class TestItemService:
    """Testes unitarios para ItemService."""
    
    def setup_method(self):
        """Setup para cada teste."""
        self.mock_repository = Mock(spec=ItemRepository)
        self.service = ItemService(item_repository=self.mock_repository)
    
    def test_get_item_by_id_success(self):
        """Testa busca de item existente."""
        # Arrange
        item_id = "MLB12345678"
        expected_item = Item(
            id=item_id,
            title="Test Item",
            price=99.99,
            currency_id="BRL",
            description="Test description",
            condition="new"
        )
        self.mock_repository.find_by_id.return_value = expected_item
        
        # Act
        result = self.service.get_item_by_id(item_id)
        
        # Assert
        assert result == expected_item
        self.mock_repository.find_by_id.assert_called_once_with(item_id)
    
    def test_get_item_by_id_not_found(self):
        """Testa busca de item inexistente."""
        # Arrange
        item_id = "MLB99999999"
        self.mock_repository.find_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(ItemNotFoundException) as exc_info:
            self.service.get_item_by_id(item_id)
        
        assert item_id in str(exc_info.value)
        self.mock_repository.find_by_id.assert_called_once_with(item_id)
    
    @patch('app.services.item_service.uuid.uuid4')
    def test_create_item_success(self, mock_uuid):
        """Testa criacao de item com sucesso."""
        # Arrange
        mock_uuid.return_value = Mock(hex="abcd1234efgh5678")
        
        item_data = ItemCreateModel(
            title="New Test Item",
            price=199.99,
            currency_id="USD",
            description="New test description",
            condition="used"
        )
        
        expected_item = Item(
            id="MLBABCD1234",
            **item_data.model_dump()
        )
        
        self.mock_repository.save.return_value = expected_item
        
        # Act
        result = self.service.create_item(item_data)
        
        # Assert
        assert result == expected_item
        assert result.id.startswith("MLB")
        assert len(result.id) == 11
        self.mock_repository.save.assert_called_once()
        
        # Verifica se o item passado para save tem os dados corretos
        saved_item = self.mock_repository.save.call_args[0][0]
        assert saved_item.title == item_data.title
        assert saved_item.price == item_data.price