"""
Byte swapping utilities for network communication.
"""

import struct
from typing import Union, Any

def swap_bytes(value: Union[int, float], size: int = None) -> Union[int, float]:
    """Swap bytes in an integer or float value
    
    Args:
        value: Value to swap bytes in
        size: Optional size in bytes, will be inferred if not provided
        
    Returns:
        Value with bytes swapped
    """
    if isinstance(value, float):
        # Convert float to bytes, swap, convert back
        if size == 4:
            return struct.unpack('>f', struct.pack('<f', value))[0]
        else:
            return struct.unpack('>d', struct.pack('<d', value))[0]
            
    elif isinstance(value, int):
        # Determine size if not provided
        if size is None:
            if value > 0xFFFFFFFF:
                size = 8
            elif value > 0xFFFF:
                size = 4
            else:
                size = 2
                
        # Swap bytes using struct
        if size == 2:
            return struct.unpack('>H', struct.pack('<H', value))[0]
        elif size == 4:
            return struct.unpack('>L', struct.pack('<L', value))[0]
        elif size == 8:
            return struct.unpack('>Q', struct.pack('<Q', value))[0]
        else:
            raise ValueError(f"Invalid size: {size}")
            
    else:
        raise TypeError(f"Cannot swap bytes in {type(value)}")

def swap_bytes_in_place(data: bytearray, offset: int, size: int) -> None:
    """Swap bytes in-place in a bytearray
    
    Args:
        data: Bytearray to modify
        offset: Offset into data
        size: Size in bytes to swap (2, 4, or 8)
    """
    if size == 2:
        data[offset], data[offset+1] = data[offset+1], data[offset]
    elif size == 4:
        data[offset], data[offset+3] = data[offset+3], data[offset]
        data[offset+1], data[offset+2] = data[offset+2], data[offset+1]
    elif size == 8:
        for i in range(4):
            data[offset+i], data[offset+7-i] = data[offset+7-i], data[offset+i]
    else:
        raise ValueError(f"Invalid size: {size}")

def test_byte_swapping() -> None:
    """Run byte swapping tests"""
    # Test integer swapping
    assert swap_bytes(0x1234, 2) == 0x3412
    assert swap_bytes(0x12345678, 4) == 0x78563412
    assert swap_bytes(0x1234567890ABCDEF, 8) == 0xEFCDAB9078563412
    
    # Test float swapping
    assert abs(swap_bytes(1.234, 4) - struct.unpack('>f', struct.pack('<f', 1.234))[0]) < 0.0001
    assert abs(swap_bytes(1.234) - struct.unpack('>d', struct.pack('<d', 1.234))[0]) < 0.0001
    
    # Test in-place swapping
    data = bytearray([1,2,3,4,5,6,7,8])
    swap_bytes_in_place(data, 0, 2)
    assert data == bytearray([2,1,3,4,5,6,7,8])
    
    data = bytearray([1,2,3,4,5,6,7,8])
    swap_bytes_in_place(data, 0, 4)
    assert data == bytearray([4,3,2,1,5,6,7,8])
    
    data = bytearray([1,2,3,4,5,6,7,8])
    swap_bytes_in_place(data, 0, 8)
    assert data == bytearray([8,7,6,5,4,3,2,1])
