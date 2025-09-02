from typing import Optional
from pydantic import BaseModel


class Item(BaseModel):
    """
    Modelo que representa um item do catalogo.
    
    Attributes:
        id: Identificador unico do item
        title: Titulo/nome do item
        price: Preco do item
        currency_id: Codigo da moeda (ex: 'BRL', 'USD')
        description: Descricao detalhada do item
        condition: Condicao do item ('new', 'used', etc.)
    """
    id: str
    title: str
    price: float
    currency_id: str
    description: str
    condition: str


class ItemCreateModel(BaseModel):
    """
    Modelo para criacao de novos itens.
    
    Contem todos os campos de Item exceto o 'id',
    que sera gerado automaticamente pelo sistema.
    """
    title: str
    price: float
    currency_id: str
    description: str
    condition: str


class ItemUpdateModel(BaseModel):
    """
    Modelo para atualizacao de itens existentes.
    
    Todos os campos sao opcionais, permitindo atualizacao parcial.
    """
    title: Optional[str] = None
    price: Optional[float] = None
    currency_id: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[str] = None