import requests
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") + "/" + BOT_TOKEN

response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={WEBHOOK_URL}")

if response.status_code == 200:
    print("Webhook успешно настроен!")
else:
    print(f"Ошибка при настройке webhook: {response.text}")
