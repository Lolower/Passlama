import json
import asyncio
import base64
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solana.rpc.api import Client as SyncClient
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.system_program import create_account_with_seed
import os
from cryptography.fernet import Fernet
import random

DEVNET_URL = "https://api.devnet.solana.com"
SYS_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
PROGRAM_ID = Pubkey.from_string("FAjsXV6jUnBB48aydJpRXonx1jwRCbPiHTuATnTWCDiP")



def ensure_crypto_dir():
    os.makedirs("cryptod", exist_ok=True)

def generate_and_save_keypair(filename):
    ensure_crypto_dir()
    keypair = Keypair()
    with open(os.path.join("cryptod", filename), 'w') as f:
        json.dump(list(keypair.to_bytes()), f)
    return keypair

def load_keypair(filename):
    try:
        with open(os.path.join("cryptod", filename), 'r') as f:
            key_bytes = json.load(f)
        return Keypair.from_bytes(bytes(key_bytes))
    except FileNotFoundError:
        print(f"Генерація нової ключової пари для {filename}...")
        return generate_and_save_keypair(filename)

def save_encryption_key(key, filename):
    ensure_crypto_dir()
    with open(os.path.join("cryptod", filename), 'wb') as f:
        f.write(base64.b64encode(key))
    print(f"🔑 Ключ шифрування збережено у {filename}")

async def get_minimum_balance_for_rent_exemption(client, space):
    print("📏 Отримання мінімального балансу для ренти...")
    async with asyncio.timeout(10):
        resp = await client.get_minimum_balance_for_rent_exemption(space)
        return resp.value

async def request_airdrop_if_needed(client, pubkey, min_balance=500_000_000):
    print("💰 Перевірка балансу...")
    async with asyncio.timeout(10):
        balance_resp = await client.get_balance(pubkey, commitment=Confirmed)
        balance = balance_resp.value
        if balance >= min_balance:
            print(f"✅ Поточний баланс: {balance / 1_000_000_000} SOL (достатньо)")
            return True
        print(f"⚠️ Баланс низький ({balance / 1_000_000_000} SOL), запит airdrop...")
        airdrop_resp = await client.request_airdrop(pubkey, 1_000_000_000, commitment=Confirmed)
        tx_id = airdrop_resp.value
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

def encrypt_password(password, key):
    print("🔐 Шифрування пароля...")
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(password.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()

def decrypt_password(encrypted, key):
    print("🔓 Розшифрування пароля...")
    data = base64.b64decode(encrypted)
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()

async def create_storage_account(client, payer, storage_account, lamports, space):
    print("🔨 Створення акаунта для зберігання...")
    max_retries = 3
    retry_count = 0

    async with asyncio.timeout(10):
        account_info = await client.get_account_info(storage_account.pubkey(), commitment=Confirmed)
        if account_info.value is not None:
            print(f"⚠️ Акаунт {storage_account.pubkey()} уже існує!")
            return True

    while retry_count < max_retries:
        try:
            print(f"🔄 Отримання blockhash (спроба {retry_count + 1})...")
            async with asyncio.timeout(10):
                blockhash_resp = await client.get_latest_blockhash(commitment=Confirmed)
                recent_blockhash = blockhash_resp.value.blockhash
                print(f"🔄 Використовується blockhash: {recent_blockhash}")

            create_account_ix = sp.CreateAccountWithSeedParams(
                from_pubkey=payer.pubkey(),
                to_pubkey=storage_account.pubkey(),
                base_pubkey=payer.pubkey(),
                seed="storage",
                lamports=lamports,
                space=space,
                program_id=PROGRAM_ID
            ).to_instruction()

            message = MessageV0.compile(
                payer=payer.pubkey(),
                instructions=[create_account_ix],
                recent_blockhash=recent_blockhash
            )

            txn = VersionedTransaction(
                message=message,
                keypairs=[payer]
            )

            send_opts = TxOpts(
                skip_preflight=False,
                preflight_commitment=Confirmed,
                max_retries=3
            )

            print("📤 Відправка транзакції...")
            async with asyncio.timeout(15):
                result = await client.send_transaction(txn, opts=send_opts)
                tx_id = result.value
                print(f"📤 Транзакція відправлена з ID: {tx_id}")

            print("⏳ Очікування підтвердження транзакції...")
            async with asyncio.timeout(15):
                confirmation = await client.get_transaction(tx_id, commitment=Confirmed)
                if confirmation.value and confirmation.value.transaction.meta.err is None:
                    print(f"✅ Акаунт {storage_account.pubkey()} успішно створено!")
                    return True
                else:
                    print(f"❌ Помилка підтвердження: {confirmation.value.transaction.meta.err}")
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
            retry_count += 1
            await asyncio.sleep(2)
            continue

    print(f"❌ Не вдалося створити акаунт після {max_retries} спроб")
    return False



async def store_encrypted_password(client, payer, storage_account_pubkey: Pubkey, encrypted_password: str, bump: int) -> bool:
    print("🗄️ Зберігання пароля в акаунті...")
    try:
        space = 8 + 1 + 4 + 1024 + 1  # Відповідає розміру в lib.rs
        lamports = await get_minimum_balance_for_rent_exemption(client, space)
        print(f"📊 Потрібно lamports: {lamports}")
        account_info = await client.get_account_info(storage_account_pubkey, commitment=Confirmed)
        is_initialized = account_info.value is not None
        print(f"ℹ️ Акаунт ініціалізований: {is_initialized}")

        encrypted_bytes = base64.b64decode(encrypted_password)
        print(f"🔒 Розмір зашифрованого пароля: {len(encrypted_bytes)} байт")

        if not is_initialized:
            # Створюємо Keypair для payer, але використовуємо Pubkey для storage_account
            storage_account = Keypair()  # Тимчасовий Keypair для створення акаунта
            success = await create_storage_account(client, payer, storage_account, lamports, space)
            if not success:
                print("❌ Не вдалося створити акаунт")
                return False

        # Оновлений дискримінатор для "global:initialize"
        import hashlib
        function_name = "global:initialize"
        discriminator = hashlib.sha256(function_name.encode()).digest()[:8]
        instruction_data = discriminator + encrypted_bytes + bytes([bump])

        accounts = [
            AccountMeta(pubkey=storage_account_pubkey, is_signer=False, is_writable=True),
            AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=True),
            AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        ]

        initialize_ix = Instruction(
            program_id=PROGRAM_ID,
            accounts=accounts,
            data=instruction_data
        )

        # Додавання інструкцій для compute budget
        compute_unit_limit_ix = set_compute_unit_limit(200_000)
        compute_unit_price_ix = set_compute_unit_price(0)

        # Оновлення recent_blockhash
        async with asyncio.timeout(10):
            blockhash_resp = await client.get_latest_blockhash(commitment=Confirmed)
            recent_blockhash = blockhash_resp.value.blockhash
            print(f"🔄 Використовується blockhash: {recent_blockhash}")

        message = MessageV0.compile(
            payer=payer.pubkey(),
            instructions=[compute_unit_limit_ix, compute_unit_price_ix, initialize_ix],
            recent_blockhash=recent_blockhash
        )

        txn = VersionedTransaction(
            message=message,
            keypairs=[payer]
        )

        send_opts = TxOpts(
            skip_preflight=False,
            preflight_commitment=Confirmed,
            max_retries=3
        )

        print("📤 Відправка транзакції ініціалізації...")
        result = await client.send_transaction(txn, opts=send_opts)
        tx_id = result.value
        print(f"📤 Транзакція відправлена з ID: {tx_id}")

        print("⏳ Очікування підтвердження транзакції...")
        async with asyncio.timeout(15):
            confirmation = await client.get_transaction(tx_id, commitment=Confirmed)
            if confirmation.value and confirmation.value.transaction.meta.err is None:
                print("✅ Акаунт ініціалізовано та пароль збережено!")
            else:
                print(f"❌ Помилка ініціалізації: {confirmation.value.transaction.meta.err}")
                return False

        return True
    except Exception as e:
        print(f"❌ Помилка зберігання пароля: {str(e)}")
        raise

async def retrieve_encrypted_password(client, storage_account_pubkey: Pubkey) -> str:
    print("📥 Отримання пароля з акаунта...")
    try:
        account_info = await client.get_account_info(storage_account_pubkey, commitment=Confirmed)
        if account_info.value is None:
            print("❌ Акаунт не існує")
            raise Exception("Account not found")

        data = account_info.value.data
        if len(data) < 8:
            print("❌ Недостатньо даних в акаунті")
            raise Exception("Invalid account data")

        encrypted_bytes = data[8:]  # Пропускаємо дискримінатор
        encrypted = base64.b64encode(encrypted_bytes).decode()
        print("✅ Зашифрований пароль отриміано!")
        return encrypted
    except Exception as e:
        print(f"❌ Помилка отримання пароля: {str(e)}")
        raise

async def main():
    print("🚀 Запуск програми...")
    client = AsyncClient(DEVNET_URL)
    try:
        print("🔑 Ініціалізація ключів...")
        payer = load_keypair("payer.json")
        # Генерація PDA для storage_account
        seeds = [b"password_vault"]  # Відповідає seeds у lib.rs
        storage_account_pubkey, bump = Pubkey.find_program_address(seeds, PROGRAM_ID)
        print(f"🗄️ Storage account (PDA): {storage_account_pubkey}")
        print(f"🔑 Payer: {payer.pubkey()}")

        print("🌧️ Перевірка необхідності airdrop...")
        if not await request_airdrop_if_needed(client, payer.pubkey()):
            print("\nℹ️ Отримійте SOL вручну через https://solfaucet.com...")
            print(f"Введіть ваш публічний ключ: {payer.pubkey()}\n")
            return

        print("🔐 Очікування введення пароля...")
        password = input("Введіть пароль: ")
        if not password:
            print("❌ Пароль не може бути порожнім")
            return

        encryption_key = get_random_bytes(32)
        encrypted = encrypt_password(password, encryption_key)
        print(f"🔒 Зашифрований пароль: {encrypted[:50]}...")
        save_encryption_key(encryption_key, "encryption_key.txt")

        # Передаємо storage_account_pubkey як Pubkey, а не Keypair
        if await store_encrypted_password(client, payer, storage_account_pubkey, encrypted, bump):
            print("💾 Пароль успішно збережено в акаунті!")

            retrieved_encrypted = await retrieve_encrypted_password(client, storage_account_pubkey)
            print(f"📥 Отриміано зашифрований пароль: {retrieved_encrypted[:50]}...")

            decrypted = decrypt_password(retrieved_encrypted, encryption_key)
            print(f"🔓 Оригінальний пароль: {password}")
            print(f"🔓 Розшифрований пароль: {decrypted}")
        else:
            print("❌ Не вдалося зберегти пароль")

    except Exception as e:
        print(f"🔥 Критична помилка: {str(e)}")
    finally:
        await client.close()
        print("🔌 З'єднання закрито")

if __name__ == "__main__":
    asyncio.run(main())

