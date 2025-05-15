import base58

# Байтове представлення ключа з payer.json
key_bytes = [73, 148, 194, 131, 20, 223, 107, 184, 77, 85, 253, 235, 24, 138, 238, 135, 71, 213, 13, 63, 73, 16, 176, 237, 74, 65, 158, 69, 40, 0, 87, 66, 8, 33, 118, 95, 132, 86, 83, 208, 201, 127, 158, 150, 161, 173, 133, 19, 218, 44, 90, 219, 166, 19, 243, 11, 89, 93, 136, 165, 222, 126, 17, 203]

# Конвертація у Base58
secret_key_base58 = base58.b58encode(bytes(key_bytes)).decode('utf-8')

# Створення JSON у потрібному форматі
import json
key_json = {"secret_key": secret_key_base58}

# Запис у payer.json
with open("payer.json", "w") as f:
    json.dump(key_json, f)

print(f"Новий payer.json створено з secret_key: {secret_key_base58}")

