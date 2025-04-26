import os
import json
import asyncio
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import CreateAccountParams, create_account
from solana.rpc.commitment import Confirmed
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts

SYS_PROGRAM_ID = PublicKey("11111111111111111111111111111111")
DEVNET_URL = "https://api.devnet.solana.com"


def ensure_crypto_dir():
    """Створює папку crypto якщо її немає"""
    os.makedirs("crypto", exist_ok=True)


def generate_and_save_keypair(filename):
    """Генерує та зберігає новий ключ"""
    ensure_crypto_dir()
    keypair = Keypair.generate()
    with open(os.path.join("crypto", filename), 'w') as f:
        json.dump(list(keypair.secret_key), f)
    return keypair


def load_keypair(filename):
    """Завантажує ключ з файлу або генерує новий"""
    try:
        with open(os.path.join("crypto", filename), 'r') as f:
            secret_key = json.load(f)
        return Keypair.from_secret_key(bytes(secret_key))
    except FileNotFoundError:
        print(f"Generating new keypair for {filename}...")
        return generate_and_save_keypair(filename)


async def get_minimum_balance_for_rent_exemption(client, space):
    """Отримує мінімальний баланс для аренди"""
    resp = await client.get_minimum_balance_for_rent_exemption(space)
    return resp['result']


async def store_encrypted_password(client, payer, storage_account, encrypted_password):
    """Функція для зберігання зашифрованого паролю в акаунті"""
    space = len(encrypted_password.encode())  # Розмір місця для зберігання
    lamports = await get_minimum_balance_for_rent_exemption(client, space)
    return await create_storage_account(client, payer, storage_account, lamports, space)


async def create_storage_account(client, payer, new_account, lamports, space):
    """Створює акаунт для зберігання з покращеною обробкою помилок"""
    try:
        # Отримання останнього blockhash
        blockhash_resp = await client.get_recent_blockhash()
        recent_blockhash = blockhash_resp['result']['value']['blockhash']

        # Створення транзакції
        txn = Transaction()
        txn.recent_blockhash = recent_blockhash
        txn.fee_payer = payer.public_key

        # Додавання інструкції створення акаунту
        create_account_ix = create_account(
            CreateAccountParams(
                from_pubkey=payer.public_key,
                new_account_pubkey=new_account.public_key,
                lamports=lamports,
                space=space,
                program_id=SYS_PROGRAM_ID
            )
        )
        txn.add(create_account_ix)

        # Підпис транзакції
        txn.sign(payer, new_account)

        # Відправка транзакції
        send_opts = TxOpts(
            skip_preflight=False,  # Changed to False for better error detection
            preflight_commitment=Confirmed,
            max_retries=3
        )

        # Send transaction with all required signers
        result = await client.send_transaction(
            txn,
            payer,
            new_account,
            opts=send_opts
        )

        if 'result' not in result:
            print(f"❌ Помилка відправки транзакції: {result}")
            return False

        tx_id = result['result']
        print(f"📤 Транзакція відправлена з ID: {tx_id}")

        # Очікування підтвердження
        await asyncio.sleep(5)  # Short delay for confirmation
        confirmation = await client.confirm_transaction(
            tx_id,
            commitment=Confirmed
        )

        if confirmation['result']['value']['err'] is None:
            print(f"✅ Акаунт {new_account.public_key} успішно створено!")
            return True
        else:
            print(f"❌ Помилка підтвердження: {confirmation['result']['value']['err']}")
            return False

    except Exception as e:
        print(f"❌ Помилка створення акаунту: {str(e)}")
        return False


async def request_airdrop_if_needed(client, pubkey, min_balance=500_000_000):
    """Запит airdrop тільки якщо баланс нижче мінімального"""
    try:
        balance_resp = await client.get_balance(pubkey)
        balance = balance_resp['result']['value']

        if balance >= min_balance:
            print(f"✅ Поточний баланс: {balance / 1e9} SOL (достатньо)")
            return True

        print(f"⚠️ Баланс низький ({balance / 1e9} SOL), запит airdrop...")
        airdrop_resp = await client.request_airdrop(pubkey, 1_000_000_000)  # 1 SOL
        tx_id = airdrop_resp['result']

        # Чекаємо підтвердження
        await asyncio.sleep(30)
        confirmation = await client.confirm_transaction(tx_id)
        if confirmation['result']['value']['err'] is None:
            print("✅ Airdrop успішно отримано!")
            return True
        else:
            print(f"❌ Помилка airdrop: {confirmation['result']['value']['err']}")
            return False

    except Exception as e:
        print(f"❌ Помилка отримання airdrop: {str(e)}")
        return False


def encrypt_password(password, key):
    """Шифрує пароль за допомогою AES-GCM"""
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(password.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()


def decrypt_password(encrypted, key):
    """Розшифровує пароль"""
    data = base64.b64decode(encrypted)
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()


async def main():
    """Головна функція програми"""
    client = AsyncClient(DEVNET_URL)
    try:
        # Ініціалізація ключів
        payer = load_keypair("payer.json")
        storage_account = load_keypair("storage_account.json")

        print(f"🔑 Payer: {payer.public_key}")
        print(f"🗄️ Storage account: {storage_account.public_key}")

        # Отримання тестових SOL
        if not await request_airdrop_if_needed(client, payer.public_key):
            print("\nℹ️ Отримайте SOL вручну через https://solfaucet.com/")
            print(f"Введіть ваш публічний ключ: {payer.public_key}\n")
            return

        # Шифрування паролю
        encryption_key = get_random_bytes(32)
        password = "my_secure_password"
        encrypted = encrypt_password(password, encryption_key)
        print(f"🔒 Зашифрований пароль: {encrypted[:50]}...")

        # Зберігання паролю
        if await store_encrypted_password(client, payer, storage_account, encrypted):
            print("💾 Пароль успішно збережено в акаунті!")

        # Демонстрація роботи
        decrypted = decrypt_password(encrypted, encryption_key)
        print(f"🔓 Оригінальний пароль: {password}")
        print(f"🔓 Розшифрований пароль: {decrypted}")

    except Exception as e:
        print(f"🔥 Критична помилка: {str(e)}")
    finally:
        await client.close()
        print("🔌 З'єднання закрито")


if __name__ == "__main__":
    asyncio.run(main())