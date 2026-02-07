"""
One-time migration script to encrypt existing plaintext OAuth tokens.

Run this script after:
1. Setting the ENCRYPTION_KEY environment variable
2. Running the encrypt_oauth_tokens migration

Usage:
    python -m app.scripts.encrypt_existing_tokens

The script will:
- Find all social accounts with plaintext (unencrypted) tokens
- Encrypt them using the configured ENCRYPTION_KEY
- Report on success/failure counts
"""
import asyncio
import logging
import sys

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.encryption import encrypt_token, is_encrypted, EncryptionError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def encrypt_existing_tokens() -> dict:
    """
    Encrypt all plaintext OAuth tokens in the database.

    Returns:
        Dictionary with counts: processed, encrypted, skipped, failed
    """
    stats = {
        'processed': 0,
        'encrypted': 0,
        'skipped': 0,
        'failed': 0,
    }

    async with AsyncSessionLocal() as session:
        # Raw SQL to avoid ORM's automatic decryption
        result = await session.execute(
            text("SELECT id, access_token, refresh_token FROM social_accounts")
        )
        rows = result.fetchall()

        logger.info(f"Found {len(rows)} social accounts to check")

        for row in rows:
            account_id, access_token, refresh_token = row
            stats['processed'] += 1

            try:
                needs_update = False
                update_values = {}

                # Check and encrypt access_token
                if access_token and not is_encrypted(access_token):
                    encrypted_access = encrypt_token(access_token)
                    update_values['access_token'] = encrypted_access
                    needs_update = True
                    logger.debug(f"Account {account_id}: access_token needs encryption")

                # Check and encrypt refresh_token
                if refresh_token and not is_encrypted(refresh_token):
                    encrypted_refresh = encrypt_token(refresh_token)
                    update_values['refresh_token'] = encrypted_refresh
                    needs_update = True
                    logger.debug(f"Account {account_id}: refresh_token needs encryption")

                if needs_update:
                    # Update using raw SQL to bypass ORM encryption
                    set_clause = ", ".join(
                        f"{k} = :{k}" for k in update_values.keys()
                    )
                    await session.execute(
                        text(f"UPDATE social_accounts SET {set_clause} WHERE id = :id"),
                        {**update_values, 'id': account_id}
                    )
                    stats['encrypted'] += 1
                    logger.info(f"Encrypted tokens for account {account_id}")
                else:
                    stats['skipped'] += 1
                    logger.debug(f"Account {account_id}: tokens already encrypted or empty")

            except EncryptionError as e:
                stats['failed'] += 1
                logger.error(f"Failed to encrypt tokens for account {account_id}: {e}")
            except Exception as e:
                stats['failed'] += 1
                logger.error(f"Unexpected error for account {account_id}: {e}")

        # Commit all changes
        await session.commit()

    return stats


async def main():
    """Main entry point for the encryption migration script."""
    logger.info("=" * 60)
    logger.info("OAuth Token Encryption Migration")
    logger.info("=" * 60)

    try:
        stats = await encrypt_existing_tokens()

        logger.info("")
        logger.info("Migration Complete!")
        logger.info("-" * 40)
        logger.info(f"Total accounts processed: {stats['processed']}")
        logger.info(f"Tokens encrypted:         {stats['encrypted']}")
        logger.info(f"Already encrypted/empty:  {stats['skipped']}")
        logger.info(f"Failed:                   {stats['failed']}")
        logger.info("-" * 40)

        if stats['failed'] > 0:
            logger.warning(
                "Some tokens failed to encrypt. Check the logs above for details."
            )
            sys.exit(1)
        else:
            logger.info("All tokens successfully encrypted!")
            sys.exit(0)

    except EncryptionError as e:
        logger.error(f"Encryption not configured: {e}")
        logger.error(
            "Make sure ENCRYPTION_KEY is set in your environment. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
