import asyncio
import qrcode
import base64
from flask import Flask, Response, render_template_string, request, send_file
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
import uuid
import os

app = Flask(__name__)
DEVNET_URL = "http://localhost:8899"
client = AsyncClient(DEVNET_URL)

# Зберігання тимчасових даних авторизації
session_data = {}

async def get_wallet_balance(pubkey: str):
    print("🔍 Перевірка балансу гаманця...")
    try:
        public_key = Pubkey.from_string(pubkey)
        response = await client.get_balance(public_key)
        balance = response.value / 1e9
        print(f"💰 Баланс гаманця {pubkey}: {balance} SOL")
        return balance
    except Exception as e:
        print(f"❌ Помилка при отриманні балансу: {str(e)}")
        return None

async def request_airdrop(pubkey: str, amount_lamports: int = 1_000_000_000):
    print(f"💧 Запит airdrop {amount_lamports / 1e9} SOL...")
    try:
        public_key = Pubkey.from_string(pubkey)
        response = await client.request_airdrop(public_key, amount_lamports)
        signature = response.value
        print(f"📝 Airdrop signature: {signature}")

        # Додамо більше часу для підтвердження
        import time
        for _ in range(5):  # Спробуємо 5 разів з паузою
            confirm_response = await client.confirm_transaction(signature, commitment="confirmed")
            if confirm_response.value:
                print("✅ Airdrop виконано!")
                return True
            print(f"⏳ Чекаємо підтвердження... Спроба {_ + 1}")
            time.sleep(2)
        print("❌ Airdrop не підтверджено після 5 спроб")
        return False
    except Exception as e:
        print(f"❌ Помилка airdrop: {str(e)}")
        return False

@app.route('/')
def index():
    session_id = str(uuid.uuid4())
    qr_data = f"http://localhost:5000/connect?session={session_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img.save("qr_code.png")

    with open("qr_code.png", "rb") as f:
        qr_image = base64.b64encode(f.read()).decode()
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>QR Login</title></head>
        <body>
            <h1>Scan QR Code to Login with Phantom</h1>
            <img src="data:image/png;base64,{{ qr_image }}" alt="QR Code">
            <p>Скануй код або перейди за <a href="/connect_page">посиланням</a></p>
        </body>
        </html>
    """, qr_image=qr_image)

@app.route('/connect_page')
def connect_page():
    return send_file("index.html")

@app.route('/connect')
def connect():
    session_id = request.args.get('session')
    if not session_id:
        return "Invalid session", 400
    return "Перейди на /connect_page, щоб підключити Phantom Wallet."

@app.route('/check_balance')
async def check_balance():
    try:
        with open("phantom_public_key.txt", "r") as f:
            PUBLIC_KEY = f.read().strip()
            print(f"🔑 Зчитано публічний ключ: {PUBLIC_KEY}")
            balance = await get_wallet_balance(PUBLIC_KEY)
            if balance is None or balance < 0.5:
                await request_airdrop(PUBLIC_KEY)
            return f"Balance: {balance} SOL"
    except FileNotFoundError:
        return "⚠️ Файл phantom_public_key.txt не знайдено. Підключи Phantom через /connect_page.", 400
    except Exception as e:
        return f"❌ Помилка: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
