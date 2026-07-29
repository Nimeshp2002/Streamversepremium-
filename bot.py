import os
import re
import json
import datetime
import threading
from flask import Flask
import telebot
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Streamverse Bot is Live!", 200

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
    bot.reply_to(message, "👋 **Streamverse Bot Active Hai!**\n\nAap direct message reply karein, forward karein, ya `/add Title | Poster_URL | Download_URL` format me bhejein!", parse_mode="Markdown")

@bot.message_handler(content_types=['text', 'photo'])
def handle_all_posts(message):
    try:
        text = message.caption if message.photo else message.text
        
        if message.reply_to_message:
            replied = message.reply_to_message
            text = (replied.caption if replied.photo else replied.text) or text

        if not text or text.startswith('/start'):
            return

        title = ""
        download_url = ""
        poster_url = ""

        # Extract URLs
        urls = re.findall(r'https?://[^\s]+', text)
        
        # Check explicit Pipe format: Title | Poster | DownloadLink
        if '|' in text:
            parts = text.replace('/add', '').split('|')
            if len(parts) >= 3:
                title = parts[0].strip()
                poster_url = parts[1].strip()
                download_url = parts[2].strip()
            elif len(parts) == 2:
                title = parts[0].strip()
                download_url = parts[1].strip()
        else:
            lines = [line.strip() for line in text.split('\n') if line.strip() and not line.startswith('/')]
            if lines:
                title = lines[0].replace('💚', '').replace('❤️', '').strip()
            if urls:
                download_url = urls[0]

        # Check if text contains direct image URL (.jpg, .png, .jpeg, postimg, etc.)
        for url in urls:
            if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', 'postimg', 'imgur', 'tmdb']):
                poster_url = url
                break

        if not download_url and urls:
            download_url = urls[-1]

        if not title:
            bot.reply_to(message, "⚠️ Title nahi mil saka!")
            return

        if not download_url:
            bot.reply_to(message, "⚠️ Download Link nahi mila!")
            return

        # Fallback poster image
        if not poster_url:
            clean_title = re.sub(r'[^\w\s]', '', title)
            poster_url = f"https://placehold.co/400x600/1e293b/ffffff?text={clean_title.replace(' ', '+')}"

        movie_data = {
            "title": title,
            "poster": poster_url,
            "downloadUrl": download_url,
            "createdAt": datetime.datetime.now(datetime.timezone.utc)
        }

        db.collection("movies").add(movie_data)

        bot.reply_to(
            message, 
            f"✅ **Website Par Live Ho Gayi!**\n\n🎬 **Title:** {title}\n🖼️ **Poster:** {poster_url}\n🔗 **Download Link:** {download_url}", 
            parse_mode="Markdown"
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

def start_bot():
    print("Bot polling started...")
    try:
        bot.remove_webhook()
    except Exception:
        pass
    bot.infinity_polling(skip_pending_updates=True)

threading.Thread(target=start_bot, daemon=True).start()
