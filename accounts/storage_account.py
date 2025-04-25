from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import asyncio
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import create_account, SYS_PROGRAM_ID
from solana.rpc.types import TxOpts
from solana.publickey import PublicKey




# Функції для роботи з Solana
async def get_minimum_balance_for_rent_exemption(client, size=0):
    """Отримання мінімального балансу для оренди"""
    try:
        response = await client.get_minimum_balance_for_rent_exemption(size)
        return response['result']
    except Exception as e:
        print(f"Помилка отримання балансу: {e}")
        return 0


async def create_storage_account(client, payer, storage_account, lamports, space=0):
    """Створення акаунту для зберігання"""
    try:
        transaction = Transaction()
        transaction.add(
            create_account(
                from_pubkey=payer.public_key,
                new_account_pubkey=storage_account.public_key,
                lamports=lamports,
                space=space,
                program_id=SYS_PROGRAM_ID
            )
        )

        # Додаємо підтвердження транзакції
        opts = TxOpts(skip_confirmation=False, preflight_commitment="confirmed")
        response = await client.send_transaction(transaction, payer, opts=opts)

        # Очікуємо підтвердження
        await client.confirm_transaction(response['result'], commitment="confirmed")
        print(f"Акаунт успішно створено: {storage_account.public_key}")
        return True
    except Exception as e:
        print(f"Помилка створення акаунту: {e}")
        return False


async def store_encrypted_password(client, payer, storage_account, encrypted_password: str):
    """Зберігання зашифрованого пароля"""
    try:
        # Отримуємо необхідний баланс
        data_size = len(encrypted_password.encode('utf-8'))
        lamports = await get_minimum_balance_for_rent_exemption(client, data_size)

        # Створюємо акаунт
        success = await create_storage_account(
            client,
            payer,
            storage_account,
            lamports,
            data_size
        )

        if success:
            print(f"Пароль успішно збережено в акаунті {storage_account.public_key}")
            return True
        return False
    except Exception as e:
        print(f"Помилка збереження пароля: {e}")
        return False


async def request_airdrop_with_retry(client, public_key, lamports=1_000_000_000, retries=3):
    """Спроба отримати airdrop з кількома повтореннями"""
    for attempt in range(retries):
        try:
            print(f"Спроба {attempt + 1} отримати airdrop...")
            await client.request_airdrop(public_key, lamports, commitment="confirmed")
            await asyncio.sleep(15)  # Чекаємо підтвердження

            # Перевіряємо баланс
            balance = await client.get_balance(public_key)
            if balance['result']['value'] >= lamports:
                print(f"Успішно отримано {lamports} lamports")
                return True
            print("Airdrop не підтверджено, пробуємо знову...")
        except Exception as e:
            print(f"Помилка при спробі {attempt + 1}: {str(e)}")
        await asyncio.sleep(5)  # Зачекати перед наступною спробою
    return False


async def main():
    # Ініціалізація клієнта
    client = AsyncClient("https://rpc.ankr.com/solana_devnet/4e85c7ea2fb313b0200d5b4ce9a46fbac47588c061fa69c8309c1f56e4a633cb")

    try:
        # Генерація ключів
        payer = Keypair()
        storage_account = Keypair()

        print(f"Платник: {payer.public_key}")
        print(f"Акаунт зберігання: {storage_account.public_key}")

        # Отримання тестових коштів
        if not await request_airdrop_with_retry(client, payer.public_key):
            print("Не вдалося отримати airdrop. Спробуйте пізніше.")
            return

        # Шифрування пароля
        encryption_key = get_random_bytes(32)
        password = "my_secure_password"
        encrypted_password = encrypt_password(password, encryption_key)

        print(f"Оригінальний пароль: {password}")
        print(f"Зашифрований пароль: {encrypted_password[:50]}...")

        # Зберігання пароля
        await store_encrypted_password(
            client,
            payer,
            storage_account,
            encrypted_password
        )

        # Розшифрування для демонстрації
        decrypted = decrypt_password(encrypted_password, encryption_key)
        print(f"Розшифрований пароль: {decrypted}")

    except Exception as e:
        print(f"Сталася помилка: {str(e)}")
    finally:
        await client.close()
        print("З'єднання закрито")


if __name__ == "__main__":
    asyncio.run(main())