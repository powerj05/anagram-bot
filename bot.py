import os
import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes
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
    VALID_WORDS = [line.strip().lower() for line in file]
logging.info(f"Read {len(VALID_WORDS)} words.")

def get_anagrams(letters: str):
    from itertools import permutations
    letters = letters.lower()
    length = len(letters)
    valid_by_length = set(word for word in VALID_WORDS if len(word) == len(letters))
    found = set(
        ''.join(p) for p in permutations(letters,length)
        if ''.join(p) in valid_by_length
    )
    
    return sorted(found)

def get_cross(pattern: str):
    valid_by_length = set(word for word in VALID_WORDS if len(word) == len(pattern))
    pattern = pattern.lower().replace("?",".").replace("_",".")
    import re
    regex = re.compile(f"^{pattern}")
    matches = [w for w in valid_by_length if regex.match(w)]
    return matches

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    results = []
    if query.endswith(".") and len(query) <= 10:
        query = query[:-1]

        if(query.startswith("anagram ")):
            words = get_anagrams(query[len: "anagram "])
        elif(query.startswith("cross ")):
            words = get_cross(query[len("cross ")])
        else:
            if("_" in query or "?" in query):
                words = get_cross(query)
            else:
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

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(InlineQueryHandler(inline_query_handler))

    application.run_webhook(
        listen="0.0.0.0",
        port=8444,
        url_path=f"{BOT_TOKEN}",
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()