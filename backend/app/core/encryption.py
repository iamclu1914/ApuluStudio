"""
Encryption utilities for sensitive data storage.

Uses Fernet symmetric encryption from the cryptography library for
encrypting OAuth tokens and other sensitive credentials before database storage.
"""
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""
    pass


@lru_cache()
def _get_fernet() -> Fernet:
    """
    Get cached Fernet instance for encryption/decryption.

    The encryption key is loaded from the ENCRYPTION_KEY environment variable.

    Returns:
        Fernet: Configured Fernet instance.

    Raises:
        EncryptionError: If ENCRYPTION_KEY is not set or invalid.
    """
    settings = get_settings()

    if not settings.encryption_key:
        raise EncryptionError(
            "ENCRYPTION_KEY environment variable is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    try:
        # Fernet key must be 32 url-safe base64-encoded bytes
        key = settings.encryption_key.encode() if isinstance(settings.encryption_key, str) else settings.encryption_key
        return Fernet(key)
    except Exception as e:
        raise EncryptionError(f"Invalid ENCRYPTION_KEY format: {e}")


def encrypt_token(plaintext: str) -> str:
    """
    Encrypt a plaintext token for secure database storage.

    Args:
        plaintext: The token to encrypt.

    Returns:
        The encrypted token as a base64-encoded string.

    Raises:
        EncryptionError: If encryption fails.
    """
    if not plaintext:
        return plaintext

    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(plaintext.encode())
        return encrypted.decode()
    except EncryptionError:
        raise
    except Exception as e:
        logger.error(f"Token encryption failed: {e}")
        raise EncryptionError(f"Failed to encrypt token: {e}")


def decrypt_token(ciphertext: str) -> str:
    """
    Decrypt an encrypted token from database storage.

    Args:
        ciphertext: The encrypted token (base64-encoded string).

    Returns:
        The decrypted plaintext token.

    Raises:
        EncryptionError: If decryption fails (invalid key or corrupted data).
    """
    if not ciphertext:
        return ciphertext

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(ciphertext.encode())
        return decrypted.decode()
    except InvalidToken:
        logger.error("Token decryption failed: invalid token or wrong encryption key")
        raise EncryptionError(
            "Failed to decrypt token. The token may be corrupted or "
            "was encrypted with a different key."
        )
    except EncryptionError:
        raise
    except Exception as e:
        logger.error(f"Token decryption failed: {e}")
        raise EncryptionError(f"Failed to decrypt token: {e}")


def is_encrypted(value: str) -> bool:
    """
    Attempt to determine if a value appears to be Fernet-encrypted.

    Fernet tokens have a specific format: gAAAAA... (base64 starting with timestamp).
    This is a heuristic check, not a guarantee.

    Args:
        value: The string to check.

    Returns:
        True if the value appears to be Fernet-encrypted, False otherwise.
    """
    if not value:
        return False

    # Fernet tokens are base64-encoded and start with 'gAAAAA'
    # They also have a minimum length (timestamp + IV + ciphertext + HMAC)
    return (
        value.startswith('gAAAAA') and
        len(value) >= 100  # Minimum Fernet token length
    )


def decrypt_token_safe(ciphertext: str, fallback: str | None = None) -> str:
    """
    Safely decrypt a token with graceful fallback for migration support.

    This function handles the transition from plaintext to encrypted tokens:
    - If the value is not encrypted (plaintext), returns it as-is
    - If decryption fails, returns the fallback value or original
    - If decryption succeeds, returns the decrypted value

    This is useful during migration when some tokens may still be plaintext.

    Args:
        ciphertext: The potentially encrypted token.
        fallback: Value to return if decryption fails (defaults to ciphertext).

    Returns:
        The decrypted token, or fallback/original if decryption fails.

    Example:
        # During migration, handles both old plaintext and new encrypted tokens:
        token = decrypt_token_safe(stored_token)
    """
    if not ciphertext:
        return ciphertext

    # If not encrypted, return as-is (migration support for plaintext tokens)
    if not is_encrypted(ciphertext):
        return ciphertext

    try:
        return decrypt_token(ciphertext)
    except EncryptionError:
        logger.warning(
            "Failed to decrypt token, returning fallback. "
            "This may indicate a key rotation or corrupted token."
        )
        return fallback if fallback is not None else ciphertext
