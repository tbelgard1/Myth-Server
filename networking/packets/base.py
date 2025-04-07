"""
Base packet system for Myth metaserver.
Provides common functionality for all packet types.
"""

from dataclasses import dataclass
from enum import IntEnum
import struct
from typing import Any, ClassVar, Type, TypeVar, Generic

T = TypeVar('T', bound='PacketHeader')

@dataclass
class PacketHeader:
    """Base class for all packet headers"""
    type: IntEnum
    length: int = 0

    def pack(self) -> bytes:
        """Pack header into bytes"""
        return struct.pack('<HH', self.type, self.length)

    @classmethod
    def unpack(cls: Type[T], data: bytes) -> T:
        """Unpack header from bytes"""
        type_, length = struct.unpack('<HH', data[:4])
        return cls(type_, length)

class PacketBuilder(Generic[T]):
    """Generic packet builder for all packet types"""
    
    def __init__(self, packet_type: IntEnum, header_class: Type[T]):
        self.header = header_class(type=packet_type)
        self.buffer = bytearray(self.header.pack())

    def append_data(self, data: Any) -> None:
        """Append data to packet"""
        if hasattr(data, 'pack'):
            data = data.pack()
        elif isinstance(data, (str, bytes)):
            if isinstance(data, str):
                data = data.encode('utf-8') + b'\0'
            elif isinstance(data, bytes):
                data = data + b'\0'
        elif isinstance(data, bool):
            data = struct.pack('<?', data)
        elif isinstance(data, int):
            if data > 32767 or data < -32768:
                data = struct.pack('<l', data)
            else:
                data = struct.pack('<h', data)
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

        self.buffer.extend(data)
        self.header.length = len(self.buffer)
        
        # Update header in buffer
        header_bytes = self.header.pack()
        self.buffer[0:4] = header_bytes

    def get_packet(self) -> bytes:
        """Get complete packet bytes"""
        return bytes(self.buffer)

@dataclass
class Packet:
    """Base class for all packets"""
    PACKET_TYPE: ClassVar[IntEnum]
    header: PacketHeader

    def pack(self) -> bytes:
        """Pack packet into bytes"""
        raise NotImplementedError

    @classmethod
    def unpack(cls, data: bytes) -> 'Packet':
        """Unpack packet from bytes"""
        raise NotImplementedError
