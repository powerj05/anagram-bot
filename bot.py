import os
import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import json
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

BOT_USERNAME = "@jpaddy2_bot"
BOT_TOKEN = '7803980786:AAHxP7t-YQgIOl5aiHau3ICciy8De3ol6Kg'
WEBHOOK_URL = os.environ.get("NGROK_URL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"Received /start from user {update.effective_user.id}")
    await update.message.reply_text("New bot!")

# hrngh. soup

def handle_response(text: str) -> str:
    return(f"Thanks. We received {text}. Not up to much yet.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    logging.info(f"User {update.message.chat.id} in {message_type}: {text}")

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    
    logging.info(f"Bot: {response}")
    await update.message.reply_text(response)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_webhook(
        listen="0.0.0.0",
        port=8444,
        url_path=f"{BOT_TOKEN}",
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()