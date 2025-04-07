"""
Packet encoding and decoding for Myth metaserver.
"""

import struct
from typing import Any, Tuple, Optional
from .packets.base import Packet, PacketHeader

def encode_packet(packet: Packet) -> bytes:
    """Encode a packet into bytes
    
    Args:
        packet: Packet to encode
        
    Returns:
        Encoded packet bytes
    """
    return packet.pack()

def decode_packet(data: bytes, packet_type: Any) -> Optional[Packet]:
    """Decode bytes into a packet
    
    Args:
        data: Packet bytes to decode
        packet_type: Type of packet to create
        
    Returns:
        Decoded packet, or None if decoding fails
    """
    try:
        return packet_type.unpack(data)
    except Exception as e:
        # Log error and return None
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to decode packet: {e}")
        return None
