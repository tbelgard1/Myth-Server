"""
Diffie-Hellman key exchange implementation for Myth metaserver.
"""

import os
from dataclasses import dataclass
from typing import Tuple
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import serialization

@dataclass
class DiffieHellman:
    """Diffie-Hellman key exchange state
    
    Attributes:
        parameters: DH parameters (p, g)
        private_key: Private key
        public_key: Public key
        shared_key: Computed shared key (after exchange)
    """
    parameters: dh.DHParameters
    private_key: dh.DHPrivateKey
    public_key: dh.DHPublicKey
    shared_key: bytes = None
    
    @classmethod
    def generate(cls, key_size: int = 2048) -> 'DiffieHellman':
        """Generate new Diffie-Hellman parameters and key pair
        
        Args:
            key_size: Size of prime in bits
            
        Returns:
            New DiffieHellman instance
        """
        # Generate parameters
        parameters = dh.generate_parameters(generator=2, key_size=key_size)
        
        # Generate key pair
        private_key = parameters.generate_private_key()
        public_key = private_key.public_key()
        
        return cls(parameters, private_key, public_key)
        
    def compute_shared_key(self, peer_public_key: dh.DHPublicKey) -> bytes:
        """Compute shared key using peer's public key
        
        Args:
            peer_public_key: Peer's public key
            
        Returns:
            Shared key bytes
        """
        self.shared_key = self.private_key.exchange(peer_public_key)
        return self.shared_key
        
    def get_public_bytes(self) -> bytes:
        """Get public key as bytes
        
        Returns:
            Public key in PKCS#1 format
        """
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

def generate_key_pair(key_size: int = 2048) -> Tuple[bytes, bytes]:
    """Generate a new Diffie-Hellman key pair
    
    Args:
        key_size: Size of prime in bits
        
    Returns:
        Tuple of (private_key_bytes, public_key_bytes)
    """
    dh_state = DiffieHellman.generate(key_size)
    
    private_bytes = dh_state.private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_bytes = dh_state.get_public_bytes()
    
    return private_bytes, public_bytes

def compute_shared_secret(private_key: bytes, peer_public_key: bytes) -> bytes:
    """Compute shared secret from private key and peer's public key
    
    Args:
        private_key: Private key in PKCS#8 format
        peer_public_key: Peer's public key in PKCS#1 format
        
    Returns:
        Shared secret bytes
    """
    # Load keys
    private_key = serialization.load_der_private_key(
        private_key,
        password=None
    )
    
    peer_public_key = serialization.load_der_public_key(
        peer_public_key
    )
    
    # Compute shared secret
    return private_key.exchange(peer_public_key)

def test_diffie_hellman() -> None:
    """Run Diffie-Hellman tests"""
    # Generate key pairs
    alice = DiffieHellman.generate()
    bob = DiffieHellman.generate()
    
    # Exchange public keys and compute shared secrets
    alice_shared = alice.compute_shared_key(bob.public_key)
    bob_shared = bob.compute_shared_key(alice.public_key)
    
    # Verify shared secrets match
    assert alice_shared == bob_shared
    
    # Test key serialization
    priv1, pub1 = generate_key_pair()
    priv2, pub2 = generate_key_pair()
    
    shared1 = compute_shared_secret(priv1, pub2)
    shared2 = compute_shared_secret(priv2, pub1)
    
    assert shared1 == shared2
