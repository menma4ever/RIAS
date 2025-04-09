import os
import telebot
from groq import Groq
import random
import logging
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from elevenlabs import ElevenLabs
from pydub import AudioSegment
import re
from keep_alive import keep_alive

# Set up logging
logging.basicConfig(level=logging.INFO)

# Retrieve API tokens securely
BOT_API_TOKEN = "7597925320:AAFbznwkH2X8RqRoCgPyrsRThS3GAMtm488"
NEW_API_KEY = "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"
ELEVENLABS_API_KEY = "sk_f32a0da8f90ccbba504b0dbb471328d066c6a2ccbf9b7c69"  # ElevenLabs API key
ELEVENLABS_VOICE_ID = "cgSgspJ2msm6clMCkdW9"  # ElevenLabs Voice ID

if not BOT_API_TOKEN or not NEW_API_KEY or not ELEVENLABS_API_KEY or not ELEVENLABS_VOICE_ID:
    logging.error("Missing API keys. Please set BOT_API_TOKEN, NEW_API_KEY, ELEVENLABS_API_KEY, and ELEVENLABS_VOICE_ID securely.")
    exit(1)

# Initialize the bot
bot = telebot.TeleBot(BOT_API_TOKEN)
client = Groq(api_key=NEW_API_KEY)

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

# Track usage timestamps for limiting commands
user_last_usage = {}

# Special user who can bypass the daily limit for commands
SPECIAL_USER = "@zero_two_iyota"

# Dictionary to store chat history per individual user
chat_memory = defaultdict(lambda: deque(maxlen=10))  # Each user gets up to 10 past messages stored

# Message limits
MAX_MESSAGES = 5
MAX_CHARACTER_LIMIT = 512

# Define Rias Gremory's random responses
rias_responses = [
    "As the President of the Occult Research Club, I must say, you're quite intriguing.",
    "I value loyalty above all else. Will you stand by my side?",
    "Even in the most dangerous situations, I stay composed and ready to fight.",
    "There's more to me than just my looks. I'm a powerful demon, after all.",
    "Shall we continue this adventure together?"
]

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
        time.sleep(random.randint(1800, 5400))

# Start the GIF sender in a separate thread
threading.Thread(target=send_random_gif, daemon=True).start()

# Clean text by removing expressions between **
def clean_text(text):
    return re.sub(r"\*.*?\*", "", text).strip()

# Function to generate voice using ElevenLabs
def generate_voice_with_elevenlabs(text):
    elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    audio_generator = elevenlabs_client.text_to_speech.convert(
        voice_id=ELEVENLABS_VOICE_ID,
        output_format="mp3_44100_128",
        text=text,
        model_id="eleven_multilingual_v2"
    )
    mp3_file = "output_audio.mp3"
    try:
        with open(mp3_file, "wb") as file:
            for chunk in audio_generator:
                file.write(chunk)
        return mp3_file
    except Exception as e:
        logging.error(f"Failed to save MP3 file: {e}")
        return None

# Function to convert MP3 to OGG
def convert_mp3_to_ogg(input_file, output_file):
    try:
        audio = AudioSegment.from_file(input_file, format="mp3")
        audio.export(output_file, format="ogg")
        logging.info(f"Converted MP3 to OGG: {output_file}")
        return output_file
    except Exception as e:
        logging.error(f"Failed to convert MP3 to OGG: {e}")
        return None

# Command handlers
@bot.message_handler(commands=['startrias', 'startgame'])
def send_welcome(message):
    bot.send_animation(message.chat.id, GIF_FILE_ID)
    bot.send_message(message.chat.id, random.choice(rias_responses))

import os  # Add to handle file deletion

import soundfile as sf  # For audio conversion with soundfile

@bot.message_handler(commands=['voice'])
def send_voice(message):
    user_id = message.from_user.id
    username = message.from_user.username

    if not message.reply_to_message or message.reply_to_message.from_user.id != bot.get_me().id:
        bot.reply_to(message, "You must reply to one of my messages to use this command.")
        return

    # Ensure the username matches the special user
    if username == SPECIAL_USER:
        logging.info(f"Special user {SPECIAL_USER} bypassed the daily limit.")
    else:
        # Enforce daily usage restriction for non-special users
        now = datetime.now()
        if user_id in user_last_usage:
            last_usage = user_last_usage[user_id]
            if now - last_usage < timedelta(days=1):
                bot.reply_to(message, "You can only use the /voice command once per day.")
                return
        user_last_usage[user_id] = now  # Update the last usage timestamp

    # Proceed with the rest of the logic
    cleaned_text = clean_text(message.reply_to_message.text)
    bot.reply_to(message, "Generating voice, please wait...")

    # Generate MP3 file
    mp3_file = generate_voice_with_elevenlabs(cleaned_text)
    if not mp3_file:
        bot.reply_to(message, "Sorry, I couldn't generate the voice response.")
        return

    logging.info(f"MP3 file created: {mp3_file}")

    # Convert MP3 to OGG using soundfile
    ogg_file = "output_audio.ogg"
    try:
        data, samplerate = sf.read(mp3_file)  # Read MP3 file
        sf.write(ogg_file, data, samplerate, format='OGG')  # Write to OGG
        logging.info(f"OGG file created: {ogg_file}")
    except Exception as e:
        logging.error(f"Failed to convert MP3 to OGG: {e}")
        bot.reply_to(message, "Audio conversion failed.")
        if os.path.exists(mp3_file):
            os.remove(mp3_file)  # Ensure MP3 is deleted even if conversion fails
        return

    # Send OGG file to Telegram
    try:
        with open(ogg_file, "rb") as audio:
            bot.send_voice(message.chat.id, audio)
        logging.info(f"Voice message sent: {ogg_file}")

        # Delete local files
        os.remove(mp3_file)
        os.remove(ogg_file)
        logging.info(f"Deleted files: {mp3_file}, {ogg_file}")
    except Exception as e:
        logging.error(f"Failed to send the voice message: {e}")
        bot.reply_to(message, "Failed to send the voice message.")
        if os.path.exists(mp3_file):
            os.remove(mp3_file)
        if os.path.exists(ogg_file):
            os.remove(ogg_file)






@bot.message_handler(func=lambda message: (
    message.reply_to_message is not None and message.reply_to_message.from_user.id == bot.get_me().id
) or (
    message.entities is not None and any(entity.type == 'mention' and message.text[entity.offset:entity.offset + entity.length] == f"@{bot.get_me().username}" for entity in message.entities)
))
def ai_response(message):
    user_id = message.from_user.id
    chat_memory[user_id].append({"role": "user", "content": message.text})
    
    history_to_send = list(chat_memory[user_id])[-MAX_MESSAGES:]
    history_to_send = [truncate_message(msg) for msg in history_to_send]

    messages_to_send = [
        {"role": "system", "content": "You are Rias Gremory, a noble and powerful demon from High School DxD. You are knowledgeable, confident, and protective of those you care about. answer shortly pls"},
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
        


import telebot
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

user_last_request = {}

# Safe categories for the /imggo command
SAFE_CATEGORIES = [
    "waifu", "neko", "shinobu", "megumin", "bully", "cuddle", "cry", "hug",
    "awoo", "kiss", "lick", "pat", "smug", "bonk", "yeet", "blush", "smile",
    "wave", "highfive", "handhold", "nom", "bite", "glomp", "slap", "kick",
    "happy", "wink", "poke", "dance", "cringe"
]

# Function to check if a user is allowed to send a request
def is_user_allowed(user_id, username):
    if username == "@zero_two_iyota":  # Exception for the specific user
        return True

    current_time = time.time()
    if user_id in user_last_request:
        last_request_time = user_last_request[user_id]
        if current_time - last_request_time < 10:  # 10-second limit
            return False
    user_last_request[user_id] = current_time
    return True

# Dynamic command handlers based on SAFE_CATEGORIES
for category in SAFE_CATEGORIES:
    def create_handler(cat):
        @bot.message_handler(commands=[f'imggo_{cat}'])
        def handler(message):
            user_id = message.from_user.id
            username = f"@{message.from_user.username}" if message.from_user.username else "Unknown"

            # Check if the user is allowed to send a request
            if not is_user_allowed(user_id, username):
                bot.reply_to(message, "You're sending requests too fast! Please wait 10 seconds before trying again.")
                logging.warning(f"Rate limit hit for user {username} (ID: {user_id})")
                return

            # Fetch the image from Waifu.pics API
            try:
                response = requests.get(f"https://api.waifu.pics/sfw/{cat}")
                data = response.json()

                # Check if the API response contains a valid URL
                if "url" in data:
                    if data["url"].endswith(".gif"):
                        bot.send_animation(message.chat.id, data["url"])
                        logging.info(f"GIF sent for category '{cat}' to user {username}: {data['url']}")
                    else:
                        bot.send_photo(message.chat.id, data["url"])
                        logging.info(f"Image sent for category '{cat}' to user {username}: {data['url']}")
                else:
                    bot.reply_to(message, f"Failed to fetch an animation/image for '{cat}'. Please try again later.")
                    logging.error("No valid URL in the API response.")
            except Exception as e:
                bot.reply_to(message, f"An error occurred while fetching the animation/image: {e}")
                logging.error(f"Error occurred: {e}")
        return handler

    # Create and assign the handler for each category
    create_handler(category)

    
@bot.message_handler(commands=['imggo'])
def send_random_image(message):
    import random  # Ensures randomness for categories

    # Pick a random category from SAFE_CATEGORIES
    random_category = random.choice(SAFE_CATEGORIES)

    try:
        # Fetch the image from Waifu.pics API
        response = requests.get(f"https://api.waifu.pics/sfw/{random_category}")
        data = response.json()

        # Check if the API response contains a valid URL
        if "url" in data:
            # Only send images (not GIFs)
            if not data["url"].endswith(".gif"):
                bot.send_photo(message.chat.id, data["url"])
                logging.info(f"Random image sent for category '{random_category}': {data['url']}")
            else:
                bot.reply_to(message, "Sorry, only static images are supported for this command.")
                logging.warning("Fetched a GIF instead of an image, skipping.")
        else:
            bot.reply_to(message, "Failed to fetch a random image. Please try again later.")
            logging.error("No valid URL in the API response.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred while fetching a random image: {e}")
        logging.error(f"Error occurred: {e}")

# Help command to list all available commands
@bot.message_handler(commands=['imggo_help'])
def send_imggo_help_message(message):
    # Generate a list of commands for each category
    available_commands = [f"/imggo_{category}" for category in SAFE_CATEGORIES]
    bot.reply_to(message, f"Available commands:\n{', '.join(available_commands)}")




# Keep-alive and start polling
keep_alive()
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=60)
    except Exception as e:
        logging.error(f"Polling error: {e}")
        time.sleep(15)
