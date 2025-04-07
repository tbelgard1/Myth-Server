"""
Authentication system for Myth metaserver.
Provides user authentication, session management, and password encryption.
"""

from .auth import (
    EncryptionType,
    AuthenticationToken,
    encrypt_password,
    passwords_match,
    get_random_salt,
    get_current_time
)

from .hashing import (
    MD5,
    md5sum,
    get_block_size,
    get_digest_size
)

__all__ = [
    # Authentication
    'EncryptionType',
    'AuthenticationToken',
    'encrypt_password',
    'passwords_match',
    'get_random_salt',
    'get_current_time',
    
    # Hashing
    'MD5',
    'md5sum',
    'get_block_size',
    'get_digest_size'
]
