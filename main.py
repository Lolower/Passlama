import sys
import asyncio
from PyQt6.QtWidgets import QApplication
from ui.welcome_window import WelcomeWindow

from accounts.solana_storage import generate_key, get_solana_client, load_keypair, create_storage_account

async def init_solana():
    print("Encryption key:", generate_key())

    client = get_solana_client()
    payer = load_keypair("keys/payer.json")
    storage_account = load_keypair("keys/storage_account.json")

    await create_storage_account(client, payer, storage_account)

async def main():
    # 1. Ініціалізуємо Solana
    await init_solana()

    # 2. Запускаємо PyQt
    app = QApplication(sys.argv)
    window = WelcomeWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    asyncio.run(main())
