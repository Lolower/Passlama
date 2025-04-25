from solana.keypair import Keypair
import json

# Створити новий Keypair
keypair = Keypair.generate()

# Зберегти його в JSON файл
with open("crypto/payer.json", "w") as f:
    json.dump(list(keypair.secret_key), f)