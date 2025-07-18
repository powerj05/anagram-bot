#!/bin/bash

# --- Setup ---
cd /home/johnp/telegram_bots/telegram_anagram_bot
source venv/bin/activate

# Try to retrieve ngrok public URL from local API
NGROK_URL=""
for i in {1..10}; do
  sleep 1
  NGROK_URL=$(curl -s http://localhost:4040/api/tunnels/anagrambot | jq -r '.public_url')
  if [[ $NGROK_URL == https://* ]]; then
    break
  fi
done

# Check and report status
if [ -z "$NGROK_URL" ]; then
  echo "❌ Failed to get ngrok URL from API"
  curl -s http://localhost:4040/api/tunnels || echo "(API not responding)"
  exit 1
fi

echo "✅ ngrok URL: $NGROK_URL"

# Start the bot
export NGROK_URL
python bot.py