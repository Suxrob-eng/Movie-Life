import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')

print(f"Token uzunligi: {len(TOKEN) if TOKEN else 'Token yo\'q'}")
print(f"Token: {TOKEN}")

if TOKEN:
    parts = TOKEN.split(':')
    if len(parts) == 2:
        print(f"✅ Token formati to'g'ri")
        print(f"Bot ID: {parts[0]}")
        print(f"Hash: {parts[1][:10]}...")
    else:
        print("❌ Token noto'g'ri formatda!")
else:
    print("❌ TOKEN .env faylida topilmadi!")