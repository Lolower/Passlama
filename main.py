import sys
import os
import asyncio
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import create_account, SYS_PROGRAM_ID
from solana.rpc.types import TxOpts
from solana.publickey import PublicKey
from Crypto.Random import get_random_bytes

from importlib import import_module

from PyQt6.QtWidgets import QApplication

from crypto.encryption import encrypt_password
from ui.welcome_window import WelcomeWindow

from crypto.encryption import encrypt_password, decrypt_password
from accounts.storage_account import load_keypair, store_encrypted_password, get_minimum_balance_for_rent_exemption, create_storage_account, request_airdrop_with_retry

# Налаштування середовища перед створенням QApplication


async def init_solana():
    print("Encryption key:", get_random_bytes(32))  # Генерація випадкового ключа

    client = AsyncClient("https://rpc.ankr.com/solana_devnet/4e85c7ea2fb313b0200d5b4ce9a46fbac47588c061fa69c8309c1f56e4a633cb")

    # Завантаження ключів
    payer = Keypair.from_secret_key(load_keypair("crypto/payer.json"))
    storage_account = Keypair.from_secret_key(load_keypair("crypto/storage_account.json"))

    # Отримання мінімального балансу для оренди акаунта
    data_size = 1024  # Приклад розміру акаунта
    lamports = await get_minimum_balance_for_rent_exemption(client, data_size)

    # Створення акаунту для зберігання
    success = await create_storage_account(client, payer, storage_account, lamports, data_size)

    if success:
        print("Storage account successfully created.")
    else:
        print("Failed to create storage account.")


def main():
    app = QApplication(sys.argv)

    window = WelcomeWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Application error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
