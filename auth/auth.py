"""
Core authentication functionality for Myth metaserver.
Handles user authentication, session management, and password encryption.
"""

import time
import os
import struct
import hashlib
import logging
from typing import Optional, Tuple, Union
from dataclasses import dataclass
from enum import IntEnum

from .hashing import md5sum

logger = logging.getLogger(__name__)

# Time constants
TIME_IN_SECONDS = 60
TIME_IN_MINUTES = TIME_IN_SECONDS * 60
TIME_IN_HOURS = TIME_IN_MINUTES * 60
TIME_IN_DAYS = 24 * TIME_IN_HOURS
AUTHENTICATION_EXPIRATION_TIME = 2 * TIME_IN_DAYS

# Size constants
MAXIMUM_SALT_SIZE = 16
MAXIMUM_ENCRYPTED_PASSWORD_SIZE = MAXIMUM_SALT_SIZE
MD5_MAXIMUM_ENCRYPTED_PASSWORD_SIZE = 32  # for md5 passwords
EXTENDED_MAXIMUM_ENCRYPTED_PASSWORD_SIZE = 64  # for other auth types with room to grow
MAXIMUM_HANDOFF_TOKEN_SIZE = 32

class EncryptionType(IntEnum):
    """Password encryption types"""
    PLAINTEXT = 0  # Not recommended, only for testing
    SIMPLE = 1    # Legacy XOR-based encryption
    MD5 = 2       # MD5 hash with salt
    BCRYPT = 3    # Modern bcrypt hash (recommended)
    ARGON2 = 4    # Argon2 hash (most secure but slower)

def get_current_time() -> int:
    """Get current time in seconds since epoch"""
    return int(time.time())

def get_random_salt(size: int = MAXIMUM_SALT_SIZE) -> bytes:
    """Generate cryptographically secure random salt
    
    Args:
        size: Size of salt in bytes
        
    Returns:
        Random bytes for salt
    """
    return os.urandom(size)

def encrypt_password(password: str, salt: bytes, encryption_type: EncryptionType) -> str:
    """Encrypt password using specified encryption type
    
    Args:
        password: Plain text password
        salt: Salt bytes
        encryption_type: Type of encryption to use
        
    Returns:
        Encrypted password string
    
    Raises:
        ValueError: If password is empty or salt is invalid
    """
    if not password:
        raise ValueError("Password cannot be empty")
    if not salt or len(salt) > MAXIMUM_SALT_SIZE:
        raise ValueError(f"Salt must be 1-{MAXIMUM_SALT_SIZE} bytes")
        
    if encryption_type == EncryptionType.PLAINTEXT:
        logger.warning("Using plaintext password - not recommended for production!")
        return password
        
    elif encryption_type == EncryptionType.SIMPLE:
        # Legacy XOR-based encryption
        result = bytearray(len(password))
        for i in range(len(password)):
            result[i] = ord(password[i]) ^ salt[i % len(salt)]
        return result.hex()
        
    elif encryption_type == EncryptionType.MD5:
        # MD5 hash with salt
        return md5sum(password.encode() + salt)
        
    elif encryption_type == EncryptionType.BCRYPT:
        # Modern bcrypt hash
        import bcrypt
        return bcrypt.hashpw(password.encode(), salt).hex()
        
    elif encryption_type == EncryptionType.ARGON2:
        # Argon2 hash (most secure)
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        return ph.hash(password)
        
    else:
        raise ValueError(f"Invalid encryption type: {encryption_type}")

def passwords_match(password: str, encrypted_password: str, salt: bytes, 
                   encryption_type: EncryptionType) -> bool:
    """Check if password matches encrypted password
    
    Args:
        password: Plain text password to check
        encrypted_password: Previously encrypted password
        salt: Salt used for encryption
        encryption_type: Type of encryption used
        
    Returns:
        True if passwords match
    """
    if encryption_type in (EncryptionType.BCRYPT, EncryptionType.ARGON2):
        # These algorithms handle salt internally
        try:
            if encryption_type == EncryptionType.BCRYPT:
                import bcrypt
                return bcrypt.checkpw(password.encode(), bytes.fromhex(encrypted_password))
            else:  # ARGON2
                from argon2 import PasswordHasher
                ph = PasswordHasher()
                return ph.verify(encrypted_password, password)
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    else:
        # For other types, encrypt with same salt and compare
        try:
            encrypted = encrypt_password(password, salt, encryption_type)
            return encrypted == encrypted_password
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

@dataclass
class AuthenticationToken:
    """Authentication token for user sessions
    
    Attributes:
        data: Raw token data
    """
    data: bytearray
    
    def __init__(self):
        """Initialize empty token"""
        self.data = bytearray(MAXIMUM_HANDOFF_TOKEN_SIZE)
        
    @classmethod
    def generate(cls, host_address: int, user_id: int, 
                expiration_time: Optional[int] = None) -> 'AuthenticationToken':
        """Generate new authentication token
        
        Args:
            host_address: Client's IP address
            user_id: User ID to authenticate
            expiration_time: Optional expiration time (seconds since epoch)
            
        Returns:
            New authentication token
        """
        token = cls()
        
        # Use current time + 2 days if no expiration specified
        if expiration_time is None:
            expiration_time = get_current_time() + AUTHENTICATION_EXPIRATION_TIME
            
        # Pack token data: host (4), user_id (4), expiration (4), random (20)
        struct.pack_into('<III', token.data, 0,
            host_address,    # Client IP
            user_id,         # User ID
            expiration_time  # Expiration time
        )
        
        # Add random padding for security
        padding = os.urandom(MAXIMUM_HANDOFF_TOKEN_SIZE - 12)
        token.data[12:] = padding
        
        return token
        
    @classmethod
    def generate_guest(cls) -> 'AuthenticationToken':
        """Generate guest authentication token
        
        Returns:
            New guest token with user_id 0
        """
        return cls.generate(0, 0)
        
    def authenticate(self, client_address: int, current_time: Optional[int] = None) -> Tuple[bool, Optional[int]]:
        """Authenticate this token
        
        Args:
            client_address: Client's IP address
            current_time: Optional current time (seconds since epoch)
            
        Returns:
            Tuple of (is_valid, user_id)
            If token is invalid, user_id will be None
        """
        if current_time is None:
            current_time = get_current_time()
            
        try:
            # Unpack token data
            token_address, user_id, expiration = struct.unpack_from('<III', self.data, 0)
            
            # Validate token
            if token_address != client_address:
                logger.warning(f"Token IP mismatch: expected {token_address}, got {client_address}")
                return False, None
                
            if current_time > expiration:
                logger.warning(f"Token expired at {expiration}, current time {current_time}")
                return False, None
                
            return True, user_id
            
        except struct.error as e:
            logger.error(f"Failed to unpack token data: {e}")
            return False, None
            
    def __bytes__(self) -> bytes:
        """Convert token to bytes"""
        return bytes(self.data)
        
    def __str__(self) -> str:
        """Convert token to string representation"""
        return self.data.hex()

def test_authentication() -> None:
    """Run authentication system tests"""
    # Test password encryption
    password = "test123"
    salt = get_random_salt()
    
    for enc_type in EncryptionType:
        try:
            encrypted = encrypt_password(password, salt, enc_type)
            assert passwords_match(password, encrypted, salt, enc_type)
            assert not passwords_match("wrong", encrypted, salt, enc_type)
            logger.info(f"Password encryption test passed for {enc_type.name}")
        except ImportError:
            # Skip if encryption type not available
            logger.warning(f"Skipping {enc_type.name} test - package not installed")
        except Exception as e:
            logger.error(f"Test failed for {enc_type.name}: {e}")
            raise
        
    # Test authentication tokens
    host = 0x7F000001  # 127.0.0.1
    user_id = 12345
    token = AuthenticationToken.generate(host, user_id)
    
    # Should authenticate
    valid, auth_id = token.authenticate(host)
    assert valid and auth_id == user_id
    
    # Wrong IP should fail
    valid, auth_id = token.authenticate(0x7F000002)
    assert not valid
    
    # Expired token should fail
    token = AuthenticationToken.generate(host, user_id, get_current_time() - 1)
    valid, auth_id = token.authenticate(host)
    assert not valid
    
    # Guest token should work
    token = AuthenticationToken.generate_guest()
    valid, auth_id = token.authenticate(0)
    assert valid and auth_id == 0
    
    logger.info("All authentication tests passed!")
