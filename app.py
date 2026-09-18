import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

# Настройка логирования (чтобы видеть ошибки в логах Render)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

# Flask приложение
app = Flask(name)

# Инициализация Telegram-бота
TOKEN = os.environ.get("TELEGRAM_TOKEN")
application = ApplicationBuilder().token(TOKEN).build()

# Твои триггеры и ответ
BASE_TRIGGERS = [
    "когда абьюз",
    "когда арбуз",
    "когда админ абьюз",
    "когда будет абьюз",
    "когда будет админ абьюз",
    "когда админ арбуз",
    "когда будет админ арбуз",
    "во сколько абьюз",
    "во сколько админ абьюз",
    "во сколько админ арбуз",
    "во сколько арбуз",
]

ANSWER = "В 18:00 каждую сб по Москве"

def normalize(text: str) -> str:
    text = text.lower()
    for ch in "?!.,;:-—()\"'":
        text = text.replace(ch, " ")
    return " ".join(text.split())

# Логика обработки сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = normalize(update.message.text)

    for trigger in BASE_TRIGGERS:
        if trigger in text:
            await update.message.reply_text(ANSWER)
            return

# Регистрируем обработчик
application.add_handler(
    import('telegram.ext', fromlist=['MessageHandler']).MessageHandler(
        import('telegram.ext', fromlist=['filters']).filters.TEXT & ~import('telegram.ext', fromlist=['filters']).filters.COMMAND,
        handle_message
    )
)

# === Вебхук-эндпоинты ===
@app.route("/webhook", methods=["POST"])
def webhook():
    """Telegram шлёт сообщения сюда."""
    try:
        # Получаем JSON от Telegram
        update = Update.de_json(request.get_json(force=True), application.bot)
        # Передаём в обработчик (синхронно, через asyncio)
        import asyncio
        asyncio.run(application.process_update(update))
        return "OK", 200
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route("/health", methods=["GET"])
def health():
    """Проверка, что сервис жив (для UptimeRobot)."""
    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "Bot is running", 200

if name == "main":
    # Устанавливаем вебхук при старте (один раз)
    # Render даст URL вида https://твоё-имя.onrender.com
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
    if WEBHOOK_URL:
        import requests
        requests.get(
            f"https://api.telegram.org/bot{TOKEN}/setWebhook",
            params={"url": f"{WEBHOOK_URL}/webhook"}
        )
        logger.info(f"Webhook set to {WEBHOOK_URL}/webhook")

    # Flask слушает порт, который даёт Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)