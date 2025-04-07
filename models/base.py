"""
Base model functionality for Myth metaserver.
"""

from dataclasses import dataclass
from typing import Any, ClassVar, Type, TypeVar
import struct

T = TypeVar('T', bound='BaseModel')

@dataclass
class BaseModel:
    """Base class for all data models
    
    All models should inherit from this class and implement pack/unpack methods
    for serialization.
    """
    
    def pack(self) -> bytes:
        """Pack model into bytes
        
        Returns:
            Serialized model data
        """
        raise NotImplementedError
        
    @classmethod
    def unpack(cls: Type[T], data: bytes) -> T:
        """Unpack bytes into model
        
        Args:
            data: Serialized model data
            
        Returns:
            Unpacked model instance
        """
        raise NotImplementedError
        
    def size(self) -> int:
        """Get size of packed model in bytes
        
        Returns:
            Number of bytes needed to pack model
        """
        return len(self.pack())
        
    def __bytes__(self) -> bytes:
        """Convert model to bytes
        
        Returns:
            Packed model data
        """
        return self.pack()
