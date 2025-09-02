import json
import logging
from typing import Optional
from pathlib import Path

from app.models.item import Item
from app.core.config import settings

logger = logging.getLogger(__name__)


class ItemRepository:
    """
    Repositorio para acesso aos dados de itens.
    
    Esta classe e responsavel por carregar e buscar itens
    a partir do arquivo JSON que simula um banco de dados.
    """
    
    def __init__(self, data_file_path: Optional[str] = None):
        """
        Inicializa o repositorio carregando os dados do arquivo JSON.
        
        Args:
            data_file_path: Caminho para o arquivo JSON com os dados dos itens.
                          Se nao fornecido, usa configuracao da aplicacao.
        """
        self.data_file_path = data_file_path or settings.DATA_FILE_PATH
        self._items: dict[str, Item] = {}
        self._load_items()
    
    def _load_items(self) -> None:
        """
        Carrega os itens do arquivo JSON para memoria.
        """
        try:
            file_path = Path(self.data_file_path)
            
            if not file_path.exists():
                logger.warning(f"Data file not found: {self.data_file_path}")
                return
            
            with open(file_path, "r", encoding="utf-8") as file:
                items_data = json.load(file)
            
            self._items = {
                item_data["id"]: Item(**item_data) 
                for item_data in items_data
            }
            
            logger.info(f"Loaded {len(self._items)} items from {self.data_file_path}")
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Error loading items from {self.data_file_path}: {e}")
            self._items = {}
    
    def find_by_id(self, item_id: str) -> Optional[Item]:
        """
        Busca um item pelo seu ID.
        
        Args:
            item_id: ID do item a ser buscado
            
        Returns:
            Item encontrado ou None se nao existir
        """
        logger.debug(f"Searching for item with ID: {item_id}")
        item = self._items.get(item_id)
        
        if item:
            logger.debug(f"Item found: {item.title}")
        else:
            logger.debug(f"Item not found for ID: {item_id}")
            
        return item
    
    def save(self, item: Item) -> Item:
        """
        Salva um item no arquivo JSON.
        
        Args:
            item: Item a ser salvo/atualizado
            
        Returns:
            Item salvo
        """
        logger.info(f"Saving item: {item.id}")
        
        # Adiciona/atualiza item na estrutura em memoria
        self._items[item.id] = item
        
        # Salva todos os itens no arquivo
        self._save_all_items()
        
        logger.info(f"Item saved successfully: {item.id}")
        return item
    
    def _save_all_items(self) -> None:
        """
        Salva todos os itens em memoria no arquivo JSON.
        """
        try:
            # Cria diretorio pai se nao existir
            file_path = Path(self.data_file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Converte itens para formato JSON
            items_data = [
                item.model_dump() for item in self._items.values()
            ]
            
            # Escreve arquivo JSON
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(items_data, file, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(self._items)} items to {self.data_file_path}")
            
        except (OSError, IOError) as e:
            logger.error(f"Error saving items to {self.data_file_path}: {e}")
            raise
    
    def delete(self, item_id: str) -> bool:
        """
        Remove um item pelo seu ID.
        
        Args:
            item_id: ID do item a ser removido
            
        Returns:
            True se um item foi removido, False se nao existia
        """
        logger.info(f"Deleting item: {item_id}")
        
        if item_id not in self._items:
            logger.warning(f"Item not found for deletion: {item_id}")
            return False
        
        # Remove item da estrutura em memoria
        del self._items[item_id]
        
        # Salva todos os itens no arquivo (sem o item removido)
        self._save_all_items()
        
        logger.info(f"Item deleted successfully: {item_id}")
        return True