import hashlib
import json
import time
import uuid
from typing import Tuple


def generate_key_pair() -> Tuple[str, str]:
    """
    Generate a simulated key pair for signing and verifying transactions.
    
    This is a simplified implementation for the voting system demo.
    In a real blockchain application, you would use proper cryptographic 
    libraries like cryptography.hazmat.primitives.
    
    Returns:
        Tuple of (private_key, public_key)
    """
    # Generate a unique identifier as the base for our keys
    base_id = str(uuid.uuid4())
    
    # Create private key (in a real system, this would be properly generated)
    private_key = hashlib.sha256((base_id + str(time.time())).encode()).hexdigest()
    
    # Create public key derived from private key
    public_key = hashlib.sha256(private_key.encode()).hexdigest()
    
    return private_key, public_key


def sign_message(message: str, private_key: str) -> str:
    """
    Sign a message with a private key.
    
    Args:
        message: Message to sign
        private_key: Private key to sign with
        
    Returns:
        Signature
    """
    # In a real system, this would use proper cryptographic algorithms
    # For this demo, we'll just create a hash of the message and private key
    return hashlib.sha256((message + private_key).encode()).hexdigest()


def verify_signature(message: str, signature: str, public_key: str) -> bool:
    """
    Verify a signature with a public key.
    
    Args:
        message: Original message
        signature: Signature to verify
        public_key: Public key to verify with
        
    Returns:
        True if the signature is valid, False otherwise
    """
    # In a real system, this would use proper cryptographic verification
    # For this demo, we'll just check if the signature matches our expected format
    expected_format = hashlib.sha256((message + get_private_key_for_demo(public_key)).encode()).hexdigest()
    return signature == expected_format


def get_private_key_for_demo(public_key: str) -> str:
    """
    This function is NOT secure and should only be used for demo purposes.
    It simulates retrieving a private key from a public key, which is not
    possible in a real cryptographic system.
    
    Args:
        public_key: Public key
        
    Returns:
        Simulated private key
    """
    # This is a simplified, insecure implementation for demo purposes only
    return hashlib.sha256(("DEMO_ONLY_" + public_key).encode()).hexdigest()