import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
AUTO_POST = os.getenv('AUTO_POST', 'True').lower() == 'true'

if not TOKEN:
    print("❌ TOKEN .env faylida topilmadi!")
    exit(1)
    
if not CHANNEL_USERNAME:
    print("❌ CHANNEL_USERNAME .env faylida topilmadi!")
    exit(1)

print(f"✅ Token yuklandi: {TOKEN[:10]}...")
print(f"✅ Admin ID: {ADMIN_ID}")
print(f"✅ Kanal username: {CHANNEL_USERNAME}")
print(f"✅ Avtomatik post: {AUTO_POST}")