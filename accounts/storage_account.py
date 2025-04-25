import os
import json
import asyncio
import httpx
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
from solders.pubkey import Pubkey

SYS_PROGRAM_ID = PublicKey("11111111111111111111111111111111")
DEVNET_URL = "https://api.devnet.solana.com"


def ensure_crypto_dir():
    os.makedirs("crypto", exist_ok=True)


def generate_and_save_keypair(filename):
    ensure_crypto_dir()
    keypair = Keypair.generate()
    with open(os.path.join("crypto", filename), 'w') as f:
        json.dump(list(keypair.secret_key), f)
    return keypair


def load_keypair(filename):
    try:
        with open(os.path.join("crypto", filename), 'r') as f:
            secret_key = json.load(f)
        return Keypair.from_secret_key(bytes(secret_key))
    except FileNotFoundError:
        print(f"Generating new keypair for {filename}...")
        return generate_and_save_keypair(filename)


async def get_minimum_balance_for_rent_exemption(client, space):
    return (await client.get_minimum_balance_for_rent_exemption(space)).value


async def create_storage_account(client, payer, new_account, lamports, space):
    try:
        recent_blockhash = (await client.get_recent_blockhash()).value.blockhash

        txn = Transaction()
        txn.recent_blockhash = recent_blockhash
        txn.fee_payer = payer.public_key

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
        txn.sign(payer, new_account)

        result = await client.send_transaction(
            txn,
            payer,
            new_account,
            opts=TxOpts(skip_preflight=True, preflight_commitment=Confirmed)
        )

        tx_id = result.value
        await client.confirm_transaction(tx_id, commitment=Confirmed)
        return True

    except Exception as e:
        print(f"Account creation error: {str(e)}")
        return False


async def request_airdrop_with_retry(client, public_key, lamports=1_000_000_000, retries=3):
    """Покращена версія з обробкою обмежень"""
    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1} to get airdrop...")

            # Додаємо випадкову затримку між спробами
            await asyncio.sleep(5 * (attempt + 1))

            # Використовуємо інший RPC endpoint
            alt_rpc = "https://api.devnet.solana.com" if attempt % 2 else "https://devnet.solana.com"
            client._provider.endpoint_uri = alt_rpc

            result = await client.request_airdrop(
                public_key,
                lamports,
                commitment="confirmed"
            )

            if hasattr(result, 'error'):
                print(f"Airdrop error: {result.error}")
                continue

            # Чекаємо довше для підтвердження
            await asyncio.sleep(30)

            # Перевіряємо баланс
            balance = await client.get_balance(public_key)
            if balance.value >= lamports:
                print(f"Successfully received {lamports} lamports")
                return True

            print("Airdrop not confirmed yet...")

        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {str(e)}")

            # Якщо це помилка 429, чекаємо довше
            if "429" in str(e):
                wait_time = 60 * (attempt + 1)
                print(f"Rate limited, waiting {wait_time} seconds...")
                await asyncio.sleep(wait_time)

    # Якщо автоматичний airdrop не спрацював
    print("\nAutomatic airdrop failed. Please get test SOL manually:")
    print(f"1. Go to https://solfaucet.com/")
    print(f"2. Enter your public key: {public_key}")
    print(f"3. Request 1 SOL and wait for confirmation\n")
    return False

async def try_alternative_faucet(public_key):
    try:
        pubkey_str = str(public_key)
        async with httpx.AsyncClient() as client:
            # Спробуємо кілька популярних faucet
            faucets = [
                "https://faucet.solana.com/request",
                "https://solfaucet.com/api/request",
                "https://api.faucet.metaplex.systems/airdrop"
            ]

            for faucet in faucets:
                try:
                    response = await client.post(
                        faucet,
                        json={"address": pubkey_str, "amount": 1},
                        timeout=30
                    )

                    if response.status_code == 200:
                        print(f"Success from {faucet}")
                        await asyncio.sleep(30)
                        return True
                    else:
                        print(f"Error from {faucet}: {response.text}")
                except Exception as e:
                    print(f"Faucet {faucet} error: {str(e)}")

            return False
    except Exception as e:
        print(f"Alternative faucet error: {str(e)}")
        return False


def encrypt_password(password, key):
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(password.encode())
    return base64.b64encode(cipher.nonce + tag + ciphertext).decode()


def decrypt_password(encrypted, key):
    data = base64.b64decode(encrypted)
    nonce, tag, ciphertext = data[:16], data[16:32], data[32:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode()


async def store_encrypted_password(client, payer, storage_account, encrypted_password):
    space = len(encrypted_password.encode())
    lamports = await get_minimum_balance_for_rent_exemption(client, space)
    return await create_storage_account(client, payer, storage_account, lamports, space)


async def main():
    client = AsyncClient(DEVNET_URL)
    try:
        payer = load_keypair("payer.json")
        storage_account = load_keypair("storage_account.json")

        print(f"Payer: {payer.public_key}")
        print(f"Storage account: {storage_account.public_key}")

        if not await request_airdrop_with_retry(client, payer.public_key):
            print("Failed to get airdrop, please try again later")
            print("You can also get test SOL manually from: https://solfaucet.com/")
            return

        balance = await client.get_balance(payer.public_key)
        print(f"Current balance: {balance.value} lamports")

        encryption_key = get_random_bytes(32)
        password = "my_secure_password"
        encrypted = encrypt_password(password, encryption_key)

        if await store_encrypted_password(client, payer, storage_account, encrypted):
            print("Password successfully stored!")

        decrypted = decrypt_password(encrypted, encryption_key)
        print(f"Original: {password}")
        print(f"Decrypted: {decrypted}")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())