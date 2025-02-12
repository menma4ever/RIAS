import os
import telebot
from groq import Groq
import random
import logging
import time
from collections import defaultdict
from keep_alive import keep_alive
# Set up logging
logging.basicConfig(level=logging.INFO)

# Retrieve bot token and API key from environment variables (replace with your own environment variable handling mechanism)
BOT_API_TOKEN = os.getenv("BOT_API_TOKEN", "7597925320:AAFbznwkH2X8RqRoCgPyrsRThS3GAMtm488")  # Replace with your token securely
NEW_API_KEY = os.getenv("NEW_API_KEY", "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")  # Replace with your API key securely

# GIF to be sent
GIF_FILE_ID = 'https://t.me/franxxbotsgarage/19'

# Initialize the bot
bot = telebot.TeleBot(BOT_API_TOKEN)

# Set up the new AI API
client = Groq(
    api_key=NEW_API_KEY  # Use your Groq API key directly
)

# Define Rias Gremory's random responses
rias_responses = [
    "As the President of the Occult Research Club, I must say, you're quite intriguing.",
    "I value loyalty above all else. Will you stand by my side?",
    "Even in the most dangerous situations, I stay composed and ready to fight.",
    "There's more to me than just my looks. I'm a powerful demon, after all.",
    "Shall we continue this adventure together?"
]

# Initialize a dictionary to store chat history
chat_history = defaultdict(list)

# Maximum number of previous messages to send (to avoid going over the limit)
MAX_MESSAGES = 5
MAX_CHARACTER_LIMIT = 256  # Free-tier character limit

# Function to truncate message content to avoid exceeding character limits
def truncate_message(message, max_length=100):
    """Truncate message content to a specific length if it's too long."""
    if len(message['content']) > max_length:
        message['content'] = message['content'][:max_length] + "..."  # Add ellipsis to indicate truncation
    return message

# Handlers
@bot.message_handler(commands=['startrias', 'startgame'])
def send_welcome(message):
    bot.send_animation(message.chat.id, GIF_FILE_ID)
    bot.send_message(message.chat.id, random.choice(rias_responses))

@bot.message_handler(func=lambda message: message.reply_to_message is not None or 
                                    (message.entities is not None and any(entity.type == 'mention' for entity in message.entities)))
def ai_response(message):
    user_id = message.chat.id
    
    # Add user's message to the chat history
    chat_history[user_id].append({"role": "user", "content": message.text})
    
    # Limit the number of messages in the history to avoid exceeding the API's limits
    history_to_send = chat_history[user_id][-MAX_MESSAGES:]

    # Truncate messages to ensure we stay within the character limit
    history_to_send = [truncate_message(msg) for msg in history_to_send]

    # Prepare the full list of messages to send to the API
    messages_to_send = [
        {
            "role": "system",
            "content": "You are Rias Gremory, a noble and powerful demon from High School DxD. You are knowledgeable, confident, and protective of those you care about. try to give shorter responses around 20-30 words"
        },
        *history_to_send  # Add the most recent messages
    ]

    # Ensure the total character count does not exceed the limit
    total_characters = sum(len(msg['content']) for msg in messages_to_send)
    
    while total_characters > MAX_CHARACTER_LIMIT:
        # Trim the oldest messages until we are under the character limit
        messages_to_send.pop(1)  # Remove the oldest message
        total_characters = sum(len(msg['content']) for msg in messages_to_send)

    try:
        # Groq API request for chat completion
        response = client.chat.completions.create(
            messages=messages_to_send,  # Messages to send to the model
            model="llama-3.3-70b-versatile",  # The model you're using
        )

        # Add AI's response to the chat history
        chat_history[user_id].append({"role": "assistant", "content": response.choices[0].message.content})
        
        # Send the AI response to the user
        bot.reply_to(message, response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Error while generating AI response: {e}")
        bot.reply_to(message, "Sorry, I couldn't process your request at the moment.")
keep_alive()
# Start polling with increased timeout and error handling
while True:
    try:
        bot.polling(none_stop=True, interval=0, timeout=60)
    except Exception as e:
        logging.error(f"Polling error: {e}")
        time.sleep(15)  # Wait before retrying
