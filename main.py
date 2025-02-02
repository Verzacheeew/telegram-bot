import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from pytube import YouTube

# Фиктивный HTTP-сервер для Render
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 8000), DummyHandler)
    server.serve_forever()

# Запускаем фиктивный сервер в фоновом потоке
threading.Thread(target=run_dummy_server, daemon=True).start()

# Получаем токен из переменной окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables!")

# URL вашего сервиса на Render
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Например: "https://your-service.onrender.com"

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь мне ссылку на видео с YouTube, и я помогу тебе скачать его.\n"
        "Выбери формат: видео или аудио."
    )

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        try:
            yt = YouTube(url)
            keyboard = [
                [InlineKeyboardButton("Видео", callback_data=f"video|{url}")],
                [InlineKeyboardButton("Аудио", callback_data=f"audio|{url}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"Загружаем: {yt.title}\nВыбери формат:", reply_markup=reply_markup)
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")
    else:
        await update.message.reply_text("Пожалуйста, отправьте корректную ссылку на YouTube.")

# Обработчик кнопок выбора формата
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice, url = query.data.split("|")
    yt = YouTube(url)

    if choice == "video":
        # Предложить выбор качества видео
        resolutions = [stream.resolution for stream in yt.streams.filter(progressive=True)]
        keyboard = [[InlineKeyboardButton(res, callback_data=f"res|{res}|{url}")] for res in resolutions]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выбери качество видео:", reply_markup=reply_markup)

    elif choice == "audio":
        # Предложить выбор битрейта аудио
        audio_streams = yt.streams.filter(only_audio=True)
        bitrates = [stream.abr for stream in audio_streams if stream.abr]
        keyboard = [[InlineKeyboardButton(br, callback_data=f"abr|{br}|{url}")] for br in bitrates]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выбери битрейт аудио:", reply_markup=reply_markup)

# Обработчик выбора качества видео или аудио
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data, value, url = query.data.split("|")
    yt = YouTube(url)

    if data == "res":
        # Скачать видео
        stream = yt.streams.filter(res=value, progressive=True).first()
        file_path = stream.download(output_path="downloads")
        await query.edit_message_text("Видео загружено. Отправляю...")
        await context.bot.send_video(chat_id=query.message.chat_id, video=open(file_path, 'rb'))
        os.remove(file_path)

    elif data == "abr":
        # Скачать аудио
        stream = yt.streams.filter(abr=value, only_audio=True).first()
        file_path = stream.download(output_path="downloads")
        await query.edit_message_text("Аудио загружено. Отправляю...")
        await context.bot.send_audio(chat_id=query.message.chat_id, audio=open(file_path, 'rb'))
        os.remove(file_path)

# Основная функция
def main():
    app = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^(video|audio)\|"))
    app.add_handler(CallbackQueryHandler(download_media, pattern="^(res|abr)\|"))

    # Настройка webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),  # Render предоставляет порт через переменную PORT
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
