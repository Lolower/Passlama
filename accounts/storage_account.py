import os
import json
import asyncio
import time
import base64
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.message import Message
from solders.system_program import CreateAccountParams, create_account

SYS_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
DEVNET_URL = ("https://api.devnet.solana.com")

def ensure_crypto_dir():
    """Створює папку crypto, якщо її немає"""
    os.makedirs("crypto", exist_ok=True)

def generate_and_save_keypair(filename):
    """Генерує та зберігає нову ключову пару"""
    ensure_crypto_dir()
    keypair = Keypair()
    with open(os.path.join("crypto", filename), 'w') as f:
        json.dump(list(keypair.to_bytes()), f)
    return keypair

def load_keypair(filename):
    """Завантажує ключову пару з файлу або генерує нову"""
    try:
        with open(os.path.join("crypto", filename), 'r') as f:
            key_bytes = json.load(f)
        return Keypair.from_bytes(bytes(key_bytes))
    except FileNotFoundError:
        print(f"Генерація нової ключової пари для {filename}...")
        return generate_and_save_keypair(filename)
    except Exception as e:
        print(f"❌ Помилка завантаження ключової пари: {str(e)}")
        raise

def save_encryption_key(key, filename):
    """Зберігає ключ шифрування у файл"""
    ensure_crypto_dir()
    with open(os.path.join("crypto", filename), 'wb') as f:
        f.write(base64.b64encode(key))
    print(f"🔑 Ключ шифрування збережено у {filename}")

async def get_minimum_balance_for_rent_exemption(client, space):
    """Отримує мінімальний баланс для звільнення від ренти"""
    print("📏 Отримання мінімального балансу для ренти...")
    try:
        async with asyncio.timeout(10):  # Таймаут 10 секунд
            resp = await client.get_minimum_balance_for_rent_exemption(space)
            return resp.value
    except asyncio.TimeoutError:
        print("❌ Таймаут при отриманні мінімального балансу")
        raise
    except Exception as e:
        print(f"❌ Помилка отримання мінімального балансу: {str(e)}")
        raise

async def request_airdrop_if_needed(client, pubkey, min_balance=500_000_000):
    """Запитує airdrop, якщо баланс нижче мінімального"""
    print("💰 Перевірка балансу...")
    try:
        async with asyncio.timeout(10):  # Таймаут 10 секунд
            balance_resp = await client.get_balance(pubkey, commitment=Confirmed)
            balance = balance_resp.value
            if balance >= min_balance:
                print(f"✅ Поточний баланс: {balance / 1_000_000_000} SOL (достатньо)")
                return True

            print(f"⚠️ Баланс низький ({balance / 1_000_000_000} SOL), запит airdrop...")
            airdrop_resp = await client.request_airdrop(pubkey, 1_000_000_000, commitment=Confirmed)
            tx_id = airdrop_resp.value

            # Очікування підтвердження з опитуванням
            start_time = time.time()
            timeout = 60
            while time.time() - start_time < timeout:
                confirmation = await client.get_transaction(tx_id, commitment=Confirmed)
                if confirmation.value and confirmation.value.transaction.meta.err is None:
                    balance_resp = await client.get_balance(pubkey, commitment=Confirmed)
                    if balance_resp.value > 0:
                        print("✅ Airdrop успішно отримано!")
                        return True
                await asyncio.sleep(5)
            print("❌ Помилка airdrop: таймаут")
            return False
    except asyncio.TimeoutError:
        print("❌ Таймаут при отриманні балансу або airdrop")
        return False
    except Exception as e:
        print(f"❌ Помилка отримання airdrop: {str(e)}")
        return False

def encrypt_password(password, key):
    """Шифрує пароль за допомогою AES-GCM"""
    print("🔐 Шифрування пароля...")
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(password.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

def decrypt_password(encrypted, key):
    """Розшифровує пароль"""
    print("🔓 Розшифрування пароля...")
    data = base64.b64decode(encrypted)
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()

async def store_encrypted_password(client, payer, storage_account, encrypted_password):
    """Резервує місце для зашифрованого пароля в акаунті"""
    print("🗄️ Резервування місця для пароля...")
    try:
        space = len(encrypted_password.encode()) + 8  # Додатковий простір для метаданих
        lamports = await get_minimum_balance_for_rent_exemption(client, space)
        return await create_storage_account(client, payer, storage_account, lamports, space)
    except Exception as e:
        print(f"❌ Помилка резервування місця для пароля: {str(e)}")
        raise

async def create_storage_account(client, payer, new_account, lamports, space):
    """Створює акаунт для зберігання з покращеною обробкою помилок"""
    print("🔨 Створення акаунта для зберігання...")
    max_retries = 3
    retry_count = 0

    # Перевірка, чи акаунт уже існує
    async with asyncio.timeout(10):  # Таймаут 10 секунд
        account_info = await client.get_account_info(new_account.pubkey(), commitment=Confirmed)
        if account_info.value is not None:
            print(f"⚠️ Акаунт {new_account.pubkey()} уже існує!")
            return True

    while retry_count < max_retries:
        try:
            # Отримання свіжого blockhash
            print(f"🔄 Отримання blockhash (спроба {retry_count + 1})...")
            async with asyncio.timeout(10):  # Таймаут 10 секунд
                blockhash_resp = await client.get_latest_blockhash(commitment=Confirmed)
                recent_blockhash = blockhash_resp.value.blockhash
                print(f"🔄 Використовується blockhash: {recent_blockhash}")

            # Створення інструкції для створення акаунта
            create_account_ix = create_account(
                CreateAccountParams(
                    from_pubkey=payer.pubkey(),
                    to_pubkey=new_account.pubkey(),
                    lamports=lamports,
                    space=space,
                    owner=SYS_PROGRAM_ID  # Власник - System Program
                )
            )

            # Створення повідомлення транзакції
            message = Message.new_with_blockhash(
                instructions=[create_account_ix],
                payer=payer.pubkey(),
                blockhash=recent_blockhash
            )

            # Створення транзакції
            txn = Transaction(
                from_keypairs=[payer, new_account],  # Передаємо підписантів
                message=message,                     # Передаємо повідомлення
                recent_blockhash=recent_blockhash   # Передаємо blockhash
            )

            # Налаштування параметрів відправки
            send_opts = TxOpts(
                skip_preflight=False,
                preflight_commitment=Confirmed,
                max_retries=3
            )

            # Відправка транзакції
            print("📤 Відправка транзакції...")
            async with asyncio.timeout(15):  # Таймаут 15 секунд
                result = await client.send_transaction(txn, opts=send_opts)
                tx_id = result.value
                print(f"📤 Транзакція відправлена з ID: {tx_id}")

            # Очікування підтвердження
            print("⏳ Очікування підтвердження транзакції...")
            max_confirm_retries = 5
            confirm_retry_count = 0
            while confirm_retry_count < max_confirm_retries:
                try:
                    async with asyncio.timeout(10):  # Таймаут 10 секунд для запиту
                        confirmation = await client.get_transaction(tx_id, commitment=Confirmed)
                        if confirmation is None or confirmation.value is None:
                            print(f"⚠️ Транзакція {tx_id} ще не підтверджена, повторна спроба {confirm_retry_count + 1}/{max_confirm_retries}...")
                            confirm_retry_count += 1
                            await asyncio.sleep(5)
                            continue
                        if confirmation.value.transaction.meta.err is None:
                            print(f"✅ Акаунт {new_account.pubkey()} успішно створено!")
                            return True
                        else:
                            print(f"❌ Помилка підтвердження: {confirmation.value.transaction.meta.err}")
                            break
                except asyncio.TimeoutError:
                    print(f"❌ Таймаут при отриманні підтвердження (спроба {confirm_retry_count + 1})")
                    confirm_retry_count += 1
                    await asyncio.sleep(5)
                    continue

            print(f"❌ Не вдалося підтвердити транзакцію {tx_id} після {max_confirm_retries} спроб")
            retry_count += 1
            await asyncio.sleep(2)
            continue

        except asyncio.TimeoutError:
            print(f"❌ Таймаут при створенні акаунта (спроба {retry_count + 1})")
            retry_count += 1
            await asyncio.sleep(2)
            continue
        except Exception as e:
            print(f"❌ Помилка створення акаунта (спроба {retry_count + 1}): {str(e)}")
            import traceback
            traceback.print_exc()
            retry_count += 1
            await asyncio.sleep(2)
            continue

    print(f"❌ Не вдалося створити акаунт після {max_retries} спроб")
    return False

async def main():
    """Головна функція програми"""
    print("🚀 Запуск програми...")
    client = AsyncClient(DEVNET_URL)
    try:
        # Ініціалізація ключів
        print("🔑 Ініціалізація ключів...")
        payer = load_keypair("payer.json")
        storage_account = load_keypair("storage_account.json")
        print(f"🔑 Payer: {payer.pubkey()}")
        print(f"🗄️ Storage account: {storage_account.pubkey()}")

        # Отримання тестових SOL
        print("🌧️ Перевірка необхідності airdrop...")
        if not await request_airdrop_if_needed(client, payer.pubkey()):
            print("\nℹ️ Отримайте SOL вручну через https://solfaucet.com/")
            print(f"Введіть ваш публічний ключ: {payer.pubkey()}\n")
            return

        # Введення пароля
        print("🔐 Очікування введення пароля...")
        password = input("Введіть пароль: ")  # Замінено getpass на input
        if not password:
            print("❌ Пароль не може бути порожнім")
            return

        # Шифрування пароля
        encryption_key = get_random_bytes(32)
        encrypted = encrypt_password(password, encryption_key)
        print(f"🔒 Зашифрований пароль: {encrypted[:50]}...")
        save_encryption_key(encryption_key, "encryption_key.txt")

        # Зберігання пароля
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
    