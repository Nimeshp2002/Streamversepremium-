import os
import re
import json
import datetime
import telebot
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Setup
firebase_key_str = os.environ.get("FIREBASE_KEY")

if firebase_key_str:
    cred_dict = json.loads(firebase_key_str)
    cred = credentials.Certificate(cred_dict)
else:
    cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8513466237:AAHROJjIfiRwLyKgwRHLm0XXn-1CEvGsn5Y")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 **Streamverse Bot Active Hai!**\n\nAap direct message reply karein, forward karein, ya `/add` likhein — website par post ho jayega!", parse_mode="Markdown")

@bot.message_handler(content_types=['text', 'photo'])
def handle_all_posts(message):
    try:
        # Check text content
        text = message.caption if message.photo else message.text
        
        # Handling reply to message
        if message.reply_to_message:
            replied = message.reply_to_message
            text = (replied.caption if replied.photo else replied.text) or text

        if not text or text.startswith('/start'):
            return

        title = ""
        download_url = ""
        poster_url = ""

        # 1. Image Check
        if message.photo:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            poster_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        elif message.reply_to_message and message.reply_to_message.photo:
            file_id = message.reply_to_message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            poster_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # 2. Extract Links
        urls = re.findall(r'https?://[^\s]+', text)
        if urls:
            download_url = urls[0]

        # 3. Pipe format check: /add Title | Poster | Link
        if '|' in text:
            parts = text.replace('/add', '').split('|')
            if len(parts) >= 3:
                title = parts[0].strip()
                poster_url = parts[1].strip()
                download_url = parts[2].strip()
        else:
            # Extract Title from First non-empty line
            lines = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('/')]
            if lines:
                title = lines[0].replace('❤️', '').replace('💚', '').strip()

        if not title:
            bot.reply_to(message, "⚠️ Title nahi mil saka!")
            return

        if not download_url:
            bot.reply_to(message, "⚠️ Post me Download Link nahi mila!")
            return

        if not poster_url:
            # Default placeholder image agar photo na mile
            poster_url = f"https://via.placeholder.com/400x600/111111/FFFFFF?text={title.replace(' ', '+')}"

        # Save to Firebase Firestore
        movie_data = {
            "title": title,
            "poster": poster_url,
            "downloadUrl": download_url,
            "createdAt": datetime.datetime.now(datetime.timezone.utc)
        }

        db.collection("movies").add(movie_data)

        bot.reply_to(
            message, 
            f"✅ **Website Par Post Ho Gayi!**\n\n🎬 **Title:** {title}\n🔗 **Link:** {download_url}", 
            parse_mode="Markdown"
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

print("Bot is up and running...")
bot.infinity_polling()
