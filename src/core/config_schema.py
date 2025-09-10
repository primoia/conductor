# src/core/config_schema.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class StorageConfig(BaseModel):
    type: str
    path: str = Field(default=None) # Ex: .conductor_workspace
    connection_string: str = Field(default=None) # Ex: mongodb://...

class GlobalConfig(BaseModel):
    storage: StorageConfig
    tool_plugins: List[str] = Field(default_factory=list)