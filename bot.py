import os
import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes, MessageHandler, filters
import sys
import uuid

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

logging.info("Reading word list...")
with open('words_alpha.txt') as file:
    VALID_WORDS = file.read().splitlines()
logging.info(f"Read {len(VALID_WORDS)} words.")

def get_anagrams(letters: str):
    from itertools import permutations
    letters = letters.lower()
    words = [word for word in VALID_WORDS if len(word) == len(letters)]
    found = set()
    
    for p in permutations(letters, len(letters)):
        word = ''.join(p)
        if word in words:
            found.add(word)
    return sorted(found)

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    results = []
    if query and len(query) <= 10 and "." in query:
        words = get_anagrams(query)
        for word in words:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=word,
                    input_message_content=InputTextMessageContent(word),
                )
            )
    await update.inline_query.answer(results[:50], cache_time=1)

def handle_response(text: str) -> str:
    return(f"Thanks. We received {text}.\nhrngh\nsoup")

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

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(InlineQueryHandler(inline_query_handler))

    application.run_webhook(
        listen="0.0.0.0",
        port=8444,
        url_path=f"{BOT_TOKEN}",
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()