"""
Security functionality for Myth metaserver.
Provides encryption, key exchange, and authentication.
"""

from .diffie_hellman import (
    DiffieHellman,
    generate_key_pair,
    compute_shared_secret
)

from .auth import (
    EncryptionType,
    AuthenticationToken,
    encrypt_password,
    passwords_match,
    get_random_salt,
    get_current_time
)

__all__ = [
    # Diffie-Hellman key exchange
    'DiffieHellman',
    'generate_key_pair',
    'compute_shared_secret',
    
    # Authentication
    'EncryptionType',
    'AuthenticationToken',
    'encrypt_password',
    'passwords_match',
    'get_random_salt',
    'get_current_time'
]
