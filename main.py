import asyncio
from accounts.storage_account import create_storage_account
from solana.solana_client import get_solana_client
from crypto.encryption import generate_key
from utils.config import load_keypair

async def main():
    print("Encryption key:", generate_key())

    client = get_solana_client()
    payer = load_keypair("keys/payer.json")
    storage_account = load_keypair("keys/storage_account.json")

    await create_storage_account(client, payer, storage_account)

if __name__ == "__main__":
    asyncio.run(main())
