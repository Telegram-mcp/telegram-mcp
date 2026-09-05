import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()
api_id_str = os.environ.get("TELEGRAM_API_ID")
api_hash = os.environ.get("TELEGRAM_API_HASH", "")

if not api_id_str or not api_hash:
    print("❌ TELEGRAM_API_ID or TELEGRAM_API_HASH missing in .env")
    exit(1)

api_id = int(api_id_str)

async def main():
    print("\n==================================================")
    print("      Telethon Login Helper (Interactive)        ")
    print("==================================================\n")
    
    choice = input("Select Environment:\n  [1] Production Server (Live Telegram Network)\n  [2] Test Server (DC 2 Sandbox / Beta)\nChoice [1/2, default 2]: ").strip()
    is_test = choice != "1"
    
    session = StringSession()
    client = TelegramClient(session, api_id, api_hash)
    
    if is_test:
        print("\nConfiguring for Test Server DC 2 (149.154.167.40)...")
        client.session.set_dc(2, "149.154.167.40", 443)
    else:
        print("\nConfiguring for Production Server...")

    auth_choice = input("\nSelect Authentication Method:\n  [1] Phone Number & Code\n  [2] QR Code (Scan with Telegram mobile app)\nChoice [1/2, default 1]: ").strip()
    if auth_choice == "2":
        await client.connect()
        qr_login = await client.qr_login()
        print("\n📱 Open Telegram > Settings > Devices > Link Desktop Device\n")
        try:
            import qrcode
            qr = qrcode.QRCode()
            qr.add_data(qr_login.url)
            qr.print_ascii(invert=True)
        except ImportError:
            print(f"Scan or open the login URL: {qr_login.url}")
        print("\n⏳ Waiting for QR code scan in Telegram mobile app...")
        await qr_login.wait()
    else:
        await client.start()

    
    me = await client.get_me()
    print(f"\n🎉 Successfully logged in as: {me.first_name} (ID: {me.id})")
    
    saved_session = client.session.save()
    
    # Save to .env
    env_path = os.path.join(os.getcwd(), ".env")
    content = ""
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
    
    lines = content.splitlines()
    new_lines = []
    found_session = False
    found_test = False
    
    for line in lines:
        if line.startswith("TELEGRAM_SESSION="):
            new_lines.append(f"TELEGRAM_SESSION={saved_session}")
            found_session = True
        elif line.startswith("TELEGRAM_TEST_MODE="):
            new_lines.append(f"TELEGRAM_TEST_MODE={'true' if is_test else 'false'}")
            found_test = True
        else:
            new_lines.append(line)
            
    if not found_session:
        new_lines.append(f"TELEGRAM_SESSION={saved_session}")
    if not found_test:
        new_lines.append(f"TELEGRAM_TEST_MODE={'true' if is_test else 'false'}")
        
    with open(env_path, "w") as f:
        f.write("\n".join(new_lines) + "\n")
        
    print("✅ Saved TELEGRAM_SESSION to .env successfully!")
    print("🚀 You can now start the MCP server!\n")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
