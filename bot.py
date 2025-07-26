import os
import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, InlineQueryHandler, ContextTypes, CommandHandler
import sys
import uuid
from dotenv import load_dotenv
import requests
from nltk.corpus import wordnet as wn
from nltk import download
download("wordnet")

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
    WORDLE_WORDS = set(w for w in VALID_WORDS if len(w)==5)
logging.info(f"Read {len(VALID_WORDS)} words and {len(WORDLE_WORDS)} Wordle words.")

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
    return sorted(matches)

def get_cross(pattern: str):
    logging.info(f"Getting crossword matches for {pattern}")
    valid_by_length = set(w for w in VALID_WORDS if len(w) == len(pattern))
    pattern = pattern.lower().replace("?",".")
    import re
    regex = re.compile(f"^{pattern}")
    matches = [w for w in valid_by_length if regex.match(w)]
    return sorted(matches)

def get_wordle(pattern: str):
    parts = pattern.split()
    green_part = "?????"
    black_letters = set()
    yellow_letters = {}

    logging.info("Parsing Wordle query...")
    for part in parts:
        if "?" in part:
            green_part = part
        elif part.startswith("!"):
            black_letters.update(part[1:].lower())
        elif "!" in part:
            letter,pos = part.split("!")
            if letter not in yellow_letters:
                yellow_letters[letter] = set()
            yellow_letters[letter].add(int(pos)-1)
        else:
            # raise an exception, tell query handler how to deal with that
            break

    logging.info(f"Green: {green_part}")
    logging.info(f"Black: {black_letters}")
    logging.info(f"Yellow: {yellow_letters}")

    matches = []
    logging.info("Finding matches...")
    for word in WORDLE_WORDS:
        if any(g!="?" and w!=g for g,w in zip(green_part,word)):
            continue
        if any(letter in word for letter in black_letters):
            continue
        yellow_fail = False
        for letter,bad_positions in yellow_letters.items():
            if letter not in word:
                yellow_fail = True
                break
            for pos in bad_positions:
                if word[pos] == letter:
                    yellow_fail = True
                    break
            if yellow_fail:
                break
        if not yellow_fail:
            matches.append(word)

    return sorted(matches)

def score_synset(synset):
    score = 0

    # Prefer common lexical categories
    """preferred_lexnames = ['noun.person', 'noun.artifact', 'verb.communication']
    if synset.lexname() in preferred_lexnames:
        score += 2"""

    # Reward short, simple definitions
    if len(synset.definition().split()) < 12:
        score += 1

    # Prefer synsets with examples
    if len(synset.examples()) > 0:
        score += 1

    # Prefer when the queried word is first lemma
    if synset.lemmas()[0].name() == synset.name().split('.')[0]:
        score += 1

    return score

def get_definitions(word, max_defs=3):
    synsets = wn.synsets(word)
    
    if not synsets:
        return "No definitions found","No definitions found"
    
    sorted_synsets = sorted(synsets, key=score_synset, reverse=True)

    definitions = ""
    short_def = sorted_synsets[0].definition()[:100]
    for i, synset in enumerate(sorted_synsets[:max_defs]):
        definition = synset.definition()
        examples = synset.examples()
        
        if examples:
            formatted = f"{i+1}. {definition}\n   _Example:_ {examples[0]}\n\n"
        else:
            formatted = f"{i+1}. {definition}\n\n"
        
        definitions += formatted
    
    return short_def,definitions

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    logging.info(f"Received query {query}")
    results = []
    if query.endswith("."):
        query = query[:-1]

        if(query.startswith("anagram ")):
            words = get_anagrams(query[len("anagram "):])
        elif(query.startswith("cross ")):
            words = get_cross(query[len("cross "):])
        elif(query.startswith("oneaway ")):
            words = get_oneaway(query[len("oneaway "):])
        elif(query.startswith("wordle ")):
            words = get_wordle(query[len("wordle "):])
        else:
            if("?" in query):
                words = get_cross(query)
            else:
                words = get_anagrams(query)
        
        for word in words[:25]:
            short_def,definitions = get_definitions(word)
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=word,
                    input_message_content=InputTextMessageContent(f"*{word}*\n{definitions}", parse_mode='Markdown'),
                    description=short_def
                )
            )
        
        if len(words) > 25:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title = f"{len(words)-25} more results match your query ({len(words)} in total)",
                    description = "Try refining your query.",
                    input_message_content = InputTextMessageContent(f"{len(words)} results found matching query {query}")
                )
            )
    await update.inline_query.answer(results, cache_time=1)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = ("How to use this bot:\n\n"
                 f"'{BOT_USERNAME} anagram aelst.' - All anagrams of letters aelst.\n"
                 f"'{BOT_USERNAME} cross l?a?t.' - All words matching a pattern of letters and blanks, e.g. least, leapt, etc.\n"
                 f"'{BOT_USERNAME} oneaway least.' - All words that differ from 'least' by exactly one letter.\n"
                 f"'{BOT_USERNAME} wordle <info>' - All five-letter words matching information from Wordle guesses. See /wordlehelp for more.\n\n"
                 "Submit query by ending with full stop '.'"
                 )
    await update.message.reply_text(help_text)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Welcome! Use this bot to generate anagrams, match empty crossword patterns, and more! Use /help to learn more."
    await update.message.reply_text(text)

async def help_wordle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = ("To submit a Wordle query, include the following (in no particular order):\n\n"
                 "Green letters: A string of ? and letters showing what letters are at what positions, e.g. ?r??e\n"
                 "Black letters: ! followed by all the letters that are not in the word, e.g. !abcotu\n"
                 "Yellow letters: A series of letter!position strings, indicating that that letter is not at the given position, e.g. n!4 d!1\n\n"
                 f"Example query: {BOT_USERNAME} wordle ?r??e !abcotu n!4 d!1")
    await update.message.reply_text(help_text)

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(InlineQueryHandler(inline_query_handler))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("wordlehelp", help_wordle))


    application.run_webhook(
        listen="0.0.0.0",
        port=8444,
        url_path=f"{BOT_TOKEN}",
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )

if __name__ == '__main__':
    main()