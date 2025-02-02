import requests
from dotenv import load_dotenv
import os
import time

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") + "/" + BOT_TOKEN

def set_webhook():
    # Проверяем текущий статус webhook
    print("Проверяем текущий статус webhook...")
    response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo")
    webhook_info = response.json()
    print("Текущий статус webhook:", webhook_info)

    # Если webhook уже настроен, удаляем его
    if webhook_info.get("result", {}).get("url"):
        print("Webhook уже настроен. Удаляем старый webhook...")
        delete_response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook")
        if delete_response.status_code == 200:
            print("Старый webhook успешно удален.")
        else:
            print(f"Ошибка при удалении webhook: {delete_response.text}")
        time.sleep(2)  # Добавляем задержку перед настройкой нового webhook

    #
