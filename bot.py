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
    bot.reply_to(message, "👋 **Streamverse Bot Active Hai!**\n\nAap kisi bhi channel se post forward karein ya `/add Title | Poster | Link` format me bhejein, website par auto-post ho jayega!", parse_mode="Markdown")

@bot.message_handler(content_types=['text', 'photo'])
def handle_incoming_post(message):
    try:
        # Message caption ya text extract karna
        text = message.caption if message.photo else message.text
        if not text:
            return

        # Agar /start command hai toh ignore karein
        if text.startswith('/start'):
            return

        title = ""
        download_url = ""
        poster_url = ""

        # 1. Image Handler (Agar Photo Bheji Hai)
        if message.photo:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            poster_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # 2. Extract Links from Text
        urls = re.findall(r'https?://[^\s]+', text)
        for url in urls:
            if 'http' in url:
                download_url = url
                break

        # 3. Extract Title (Pehli line ko Title maan lete hain)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            title = lines[0].replace('/add', '').replace('❤️', '').strip()

        # Agar Direct /add Pipe Format diya ho: /add Title | Poster | Link
        if '|' in text:
            parts = text.replace('/add', '').split('|')
            if len(parts) >= 3:
                title = parts[0].strip()
                poster_url = parts[1].strip()
                download_url = parts[2].strip()

        # Validation
        if not title:
            bot.reply_to(message, "⚠️ Title nahi mila!")
            return

        if not download_url:
            bot.reply_to(message, "⚠️ Post me Download Link nahi mila!")
            return

        if not poster_url:
            # Placeholder poster agar photo na ho
            poster_url = "https://via.placeholder.com/300x400?text=" + title.replace(' ', '+')

        # Save to Firebase
        movie_data = {
            "title": title,
            "poster": poster_url,
            "downloadUrl": download_url,
            "createdAt": datetime.datetime.now(datetime.timezone.utc)
        }

        db.collection("movies").add(movie_data)

        bot.reply_to(
            message, 
            f"✅ **Website Par Post Ho Gayi!**\n\n🎬 **Title:** {title}\n🖼️ **Poster:** Added\n🔗 **Link:** {download_url}", 
            parse_mode="Markdown"
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

print("Bot runs successfully...")
bot.infinity_polling()
