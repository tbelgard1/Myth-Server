"""
Hashing functionality for Myth metaserver.
Provides MD5 hashing with compatibility layer for legacy code.
"""

import hashlib
from typing import Union
from dataclasses import dataclass

@dataclass
class MD5State:
    """Internal state of the MD5 algorithm
    
    This class maintains compatibility with the original C implementation
    while using Python's hashlib internally.
    
    Attributes:
        count: Message length in bits, LSW first
        abcd: Digest buffer
        buf: Accumulate block
    """
    count: list[int]
    abcd: list[int]
    buf: bytearray
    
    def __init__(self):
        """Initialize MD5 state"""
        self.count = [0, 0]  # message length in bits
        self.abcd = [0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476]  # digest buffer
        self.buf = bytearray(64)  # accumulate block

class MD5:
    """MD5 hash implementation using Python's hashlib
    
    This class provides a compatibility layer for legacy code while using
    Python's built-in MD5 implementation internally.
    """
    
    def __init__(self):
        """Initialize the MD5 state"""
        self._md5 = hashlib.md5()
        self._state = MD5State()
        
    def update(self, data: Union[str, bytes, bytearray]) -> None:
        """Update the hash object with the bytes-like object.
        
        Args:
            data: The data to hash. Can be string, bytes or bytearray.
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        self._md5.update(data)
        
        # Update internal state for compatibility
        nbytes = len(data)
        # Update bit count
        self._state.count[0] = (self._state.count[0] + (nbytes << 3)) & 0xffffffff
        if self._state.count[0] < (nbytes << 3):
            self._state.count[1] = (self._state.count[1] + 1) & 0xffffffff
        self._state.count[1] = (self._state.count[1] + (nbytes >> 29)) & 0xffffffff
        
    def digest(self) -> bytes:
        """Return the digest of the bytes passed to the update() method so far
        as a bytes object."""
        return self._md5.digest()
        
    def hexdigest(self) -> str:
        """Return the digest of the bytes passed to the update() method so far
        as a string of hexadecimal digits."""
        return self._md5.hexdigest()
        
    def copy(self) -> 'MD5':
        """Return a copy of the hash object."""
        new_md5 = MD5()
        new_md5._md5 = self._md5.copy()
        new_md5._state = MD5State()
        new_md5._state.count = self._state.count.copy()
        new_md5._state.abcd = self._state.abcd.copy()
        new_md5._state.buf = self._state.buf.copy()
        return new_md5

def md5_init() -> MD5:
    """Initialize a new MD5 hash object
    
    Returns:
        New MD5 hash object
    """
    return MD5()

def md5_append(md5_obj: MD5, data: Union[str, bytes, bytearray]) -> None:
    """Append data to an existing MD5 hash object
    
    Args:
        md5_obj: The MD5 hash object
        data: Data to append
    """
    md5_obj.update(data)

def md5_finish(md5_obj: MD5) -> bytes:
    """Finish the hash and return the digest
    
    Args:
        md5_obj: The MD5 hash object
        
    Returns:
        16-byte digest
    """
    return md5_obj.digest()

def md5sum(data: Union[str, bytes, bytearray]) -> str:
    """Compute MD5 hash of data and return hexadecimal digest
    
    Args:
        data: Data to hash
        
    Returns:
        32-character hex string
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.md5(data).hexdigest()

# Compatibility functions that match the C API
def new() -> MD5:
    """Create a new MD5 hash object"""
    return md5_init()

def get_block_size() -> int:
    """Return the block size of the hash algorithm in bytes"""
    return 64

def get_digest_size() -> int:
    """Return the size of the resulting hash in bytes"""
    return 16
