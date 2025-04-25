from solana.keypair import Keypair
import json

# Генерація нового ключа
keypair = Keypair()

# Отримання секретного ключа
secret_key = keypair.secret_key

# Збереження секретного ключа у файл
with open("crypto/storage_account.json", "w") as f:
    json.dump(list(secret_key), f)

print("Нова пара ключів збережена в crypto/storage_account.json")
