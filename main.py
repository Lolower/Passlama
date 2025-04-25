import sys
import os
import asyncio
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from Crypto.Random import get_random_bytes

from PyQt6.QtWidgets import QApplication
from ui.welcome_window import WelcomeWindow

from accounts.storage_account import (
    load_keypair,
    store_encrypted_password,
    get_minimum_balance_for_rent_exemption,
    create_storage_account,
    request_airdrop_with_retry,
    encrypt_password,
    decrypt_password
)
# Налаштування середовища
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"


async def init_solana():
    """Ініціалізація Solana-клієнта та акаунтів"""
    try:
        print("Generating encryption key:", get_random_bytes(32))

        # Підключення до DevNet
        client = AsyncClient("https://api.devnet.solana.com")

        # Завантаження ключів
        payer = load_keypair("payer.json")  # без шляху crypto/
        storage_account = load_keypair("storage_account.json")  # без шляху crypto/

        # Створення акаунту для зберігання
        data_size = 1024
        lamports = await get_minimum_balance_for_rent_exemption(client, data_size)
        success = await create_storage_account(client, payer, storage_account, lamports, data_size)

        return client, payer, storage_account if success else None

    except Exception as e:
        print(f"Solana initialization error: {e}")
        return None, None, None


def run_qt_application():
    """Запуск Qt додатку"""
    app = QApplication(sys.argv)
    window = WelcomeWindow()
    window.show()
    sys.exit(app.exec())


async def async_main():
    """Асинхронна головна функція"""
    # Ініціалізація Solana
    client, payer, storage_account = await init_solana()
    if not all([client, payer, storage_account]):
        print("Failed to initialize Solana components")
        return

    # Запуск Qt додатку в окремому потоці
    run_qt_application()


def main():
    """Точка входу"""
    try:
        # Для Windows потрібно встановити політику event loop
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        asyncio.run(async_main())
    except Exception as e:
        print(f"Application error: {e}")


if __name__ == "__main__":
    main()