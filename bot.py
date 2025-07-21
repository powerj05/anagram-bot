import os
import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes, CommandHandler
import sys
import uuid
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

load_dotenv()

BOT_USERNAME = os.environ.get("BOT_USERNAME")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
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

def get_oneaway(word: str):
    logging.info(f"Getting words one away from {word}")
    matches = set(w for w in VALID_WORDS if len(w) == len(word) and sum(a!=b for a,b in zip(w,word))==1)
    logging.info(f"Found {len(matches)} one away from {word}")
    return matches


def get_cross(pattern: str):
    valid_by_length = set(word for word in VALID_WORDS if len(word) == len(pattern))
    pattern = pattern.lower().replace("?",".").replace("_",".")
    import re
    regex = re.compile(f"^{pattern}")
    matches = [w for w in valid_by_length if regex.match(w)]
    return matches

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    logging.info(f"Received query {query}")
    results = []
    if query.endswith(".") and len(query) <= 20:
        query = query[:-1]

        if(query.startswith("anagram ")):
            words = get_anagrams(query[len("anagram "):])
        elif(query.startswith("cross ")):
            words = get_cross(query[len("cross "):])
        elif(query.startswith("oneaway ")):
            words = get_oneaway(query[len("oneaway "):])
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = ("How to use this bot:\n\n"
                 f"'{BOT_USERNAME} anagram aelst.' - All anagrams of letters aelst.\n"
                 f"'{BOT_USERNAME} cross l_a_t.' - All words matching that pattern of letters and blanks, e.g. least, leapt, etc.\n"
                 f"'{BOT_USERNAME} oneaway least.' - All words that differ from least by exactly one letter.\n\n"
                 "Submit query by ending with full stop '.'\n"
                 )
    await update.message.reply_text(help_text)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Welcome! Use this bot to generate anagrams, match empty crossword patterns, and more! Use /help to learn more."
    await update.message.reply_text(text)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(InlineQueryHandler(inline_query_handler))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))

    application.run_webhook(
        listen="0.0.0.0",
        port=8444,
        url_path=f"{BOT_TOKEN}",
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()