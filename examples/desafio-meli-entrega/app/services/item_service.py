import logging
import uuid
from typing import Optional

from app.models.item import Item, ItemCreateModel, ItemUpdateModel
from app.repository.item_repository import ItemRepository

logger = logging.getLogger(__name__)


class ItemNotFoundException(Exception):
    """
    Excecao lancada quando um item nao e encontrado.
    
    Esta excecao e usada na camada de servico para indicar
    que um item solicitado nao existe no sistema.
    """
    
    def __init__(self, item_id: str):
        self.item_id = item_id
        super().__init__(f"Item with ID '{item_id}' not found")


class ItemService:
    """
    Servico responsavel pela logica de negocio relacionada a itens.
    
    Esta classe atua como intermediaria entre a camada de API
    e a camada de acesso a dados, implementando a logica de negocio.
    """
    
    def __init__(self, item_repository: Optional[ItemRepository] = None):
        """
        Inicializa o servico com um repositorio de itens.
        
        Args:
            item_repository: Repositorio para acesso aos dados dos itens.
                           Se nao fornecido, sera criado um novo.
        """
        self.item_repository = item_repository or ItemRepository()
    
    def get_item_by_id(self, item_id: str) -> Item:
        """
        Busca um item pelo ID.
        
        Args:
            item_id: ID do item a ser buscado
            
        Returns:
            Item encontrado
            
        Raises:
            ItemNotFoundException: Quando o item nao e encontrado
        """
        logger.info(f"Searching for item with ID: {item_id}")
        
        item = self.item_repository.find_by_id(item_id)
        
        if item is None:
            logger.warning(f"Item not found: {item_id}")
            raise ItemNotFoundException(item_id)
        
        logger.info(f"Item found: {item.title} (ID: {item_id})")
        return item
    
    def create_item(self, item_data: ItemCreateModel) -> Item:
        """
        Cria um novo item.
        
        Args:
            item_data: Dados do item a ser criado
            
        Returns:
            Item criado com ID gerado
        """
        # Gera ID unico para o novo item
        new_id = f"MLB{uuid.uuid4().hex[:8].upper()}"
        
        logger.info(f"Creating new item with ID: {new_id}")
        
        # Cria instancia completa do Item
        item = Item(
            id=new_id,
            **item_data.model_dump()
        )
        
        # Persiste o item usando o repositorio
        saved_item = self.item_repository.save(item)
        
        logger.info(f"Item created successfully: {saved_item.title} (ID: {new_id})")
        return saved_item
    
    def update_item(self, item_id: str, item_data: ItemUpdateModel) -> Item:
        """
        Atualiza um item existente.
        
        Args:
            item_id: ID do item a ser atualizado
            item_data: Dados para atualizacao (campos opcionais)
            
        Returns:
            Item atualizado
            
        Raises:
            ItemNotFoundException: Quando o item nao e encontrado
        """
        logger.info(f"Updating item: {item_id}")
        
        # Busca item existente
        existing_item = self.item_repository.find_by_id(item_id)
        if existing_item is None:
            logger.warning(f"Item not found for update: {item_id}")
            raise ItemNotFoundException(item_id)
        
        # Cria dict com dados atuais do item
        updated_data = existing_item.model_dump()
        
        # Atualiza apenas os campos fornecidos (nao-None)
        for field, value in item_data.model_dump(exclude_none=True).items():
            updated_data[field] = value
        
        # Cria novo item com dados atualizados
        updated_item = Item(**updated_data)
        
        # Salva item atualizado
        saved_item = self.item_repository.save(updated_item)
        
        logger.info(f"Item updated successfully: {saved_item.title} (ID: {item_id})")
        return saved_item
    
    def delete_item(self, item_id: str) -> None:
        """
        Remove um item.
        
        Args:
            item_id: ID do item a ser removido
            
        Raises:
            ItemNotFoundException: Quando o item nao e encontrado
        """
        logger.info(f"Deleting item: {item_id}")
        
        # Tenta deletar o item
        deleted = self.item_repository.delete(item_id)
        
        if not deleted:
            logger.warning(f"Item not found for deletion: {item_id}")
            raise ItemNotFoundException(item_id)
        
        logger.info(f"Item deleted successfully: {item_id}")