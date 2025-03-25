import os
import telebot
from groq import Groq
import random
import logging
import time
import threading
from collections import defaultdict, deque
from keep_alive import keep_alive

# Set up logging
logging.basicConfig(level=logging.INFO)

# Retrieve API tokens securely from environment variables
BOT_API_TOKEN = "7597925320:AAFbznwkH2X8RqRoCgPyrsRThS3GAMtm488"
NEW_API_KEY = "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"

if not BOT_API_TOKEN or not NEW_API_KEY:
    logging.error("Missing API keys. Please set BOT_API_TOKEN and NEW_API_KEY in environment variables.")
    exit(1)

# GIFs list for auto-sending
GIF_FILES = [
    'https://t.me/franxxbotsgarage/20',
    'https://t.me/franxxbotsgarage/21',
    'https://t.me/franxxbotsgarage/22',
    'https://t.me/franxxbotsgarage/23',
    'https://t.me/franxxbotsgarage/24'
]

# Main GIF for /startrias command
GIF_FILE_ID = 'https://t.me/franxxbotsgarage/19'

# Group chat ID for sending random GIFs
GROUP_CHAT_ID = -1002262322366  

# Initialize the bot
bot = telebot.TeleBot(BOT_API_TOKEN)

# Set up the AI API
client = Groq(api_key=NEW_API_KEY)

# Define Rias Gremory's random responses
rias_responses = [
    "As the President of the Occult Research Club, I must say, you're quite intriguing.",
    "I value loyalty above all else. Will you stand by my side?",
    "Even in the most dangerous situations, I stay composed and ready to fight.",
    "There's more to me than just my looks. I'm a powerful demon, after all.",
    "Shall we continue this adventure together?"
]

# Dictionary to store chat history per **individual user**
chat_memory = defaultdict(lambda: deque(maxlen=10))  # Each user gets up to 10 past messages stored

# Message limits
MAX_MESSAGES = 5
MAX_CHARACTER_LIMIT = 512  # Increased to allow memory retention

# Function to truncate long messages
def truncate_message(message, max_length=200):
    if len(message['content']) > max_length:
        message['content'] = message['content'][:max_length] + "..."
    return message

# Function to send GIFs randomly every 30-90 minutes
def send_random_gif():
    while True:
        random_gif = random.choice(GIF_FILES)
        try:
            bot.send_animation(GROUP_CHAT_ID, random_gif)
            logging.info(f"Sent random GIF: {random_gif}")
        except Exception as e:
            logging.error(f"Error sending random GIF: {e}")
        
        # Wait for a random time between 30 to 90 minutes
        time.sleep(random.randint(1800, 5400))  

# Start the GIF sender in a separate thread
threading.Thread(target=send_random_gif, daemon=True).start()

# Command handlers
@bot.message_handler(commands=['startrias', 'startgame'])
def send_welcome(message):
    bot.send_animation(message.chat.id, GIF_FILE_ID)
    bot.send_message(message.chat.id, random.choice(rias_responses))

@bot.message_handler(func=lambda message: (
    message.reply_to_message is not None and message.reply_to_message.from_user.id == bot.get_me().id
) or (
    message.entities is not None and any(entity.type == 'mention' and message.text[entity.offset:entity.offset + entity.length] == f"@{bot.get_me().username}" for entity in message.entities)
))
def ai_response(message):
    user_id = message.from_user.id  # Use user ID to keep separate histories for each person

    chat_memory[user_id].append({"role": "user", "content": message.text})
    
    history_to_send = list(chat_memory[user_id])[-MAX_MESSAGES:]  # Keep memory for 5 messages per user
    history_to_send = [truncate_message(msg) for msg in history_to_send]

    messages_to_send = [
        {"role": "system", "content": "You are Rias Gremory, a noble and powerful demon from High School DxD. You are knowledgeable, confident, and protective of those you care about. Try to keep responses short (20-30 words), "},
        *history_to_send
    ]

    total_characters = sum(len(msg['content']) for msg in messages_to_send)
    while total_characters > MAX_CHARACTER_LIMIT:
        messages_to_send.pop(1)
        total_characters = sum(len(msg['content']) for msg in messages_to_send)

    try:
        response = client.chat.completions.create(
            messages=messages_to_send,
            model="llama-3.3-70b-versatile"
        )

        chat_memory[user_id].append({"role": "assistant", "content": response.choices[0].message.content})
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Error while generating AI response: {e}")
        bot.reply_to(message, "Sorry, I couldn't process your request at the moment.")
keep_alive()

# Start polling with error handling
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=60)
    except Exception as e:
        logging.error(f"Polling error: {e}")
        time.sleep(15)  # Retry after a delay
