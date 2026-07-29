import os
import datetime
import telebot
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Setup (Make sure serviceAccountKey.json is uploaded in GitHub)
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Telegram Bot Token
BOT_TOKEN = "8513466237:AAHROJjIfiRwLyKgwRHLm0XXn-1CEvGsn5Y"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_msg = (
        "👋 **Streamverse Bot me aapka swagat hai!**\n\n"
        "Website par movie add karne ke liye is format me message bhejein:\n\n"
        "`/add Movie Title | Poster Image URL | Download Link`"
    )
    bot.reply_to(message, welcome_msg, parse_mode="Markdown")

@bot.message_handler(commands=['add'])
def add_movie(message):
    try:
        raw_text = message.text.replace('/add', '').strip()
        parts = raw_text.split('|')
        
        if len(parts) < 3:
            bot.reply_to(
                message, 
                "⚠️ **Format Sahi Nahi Hai!**\n\nSahi format ye hai:\n`/add Pushpa 2 | https://link-to-poster.jpg | https://link-to-download.com`", 
                parse_mode="Markdown"
            )
            return

        title = parts[0].strip()
        poster = parts[1].strip()
        download_url = parts[2].strip()

        # Firestore Database me Save karna
        movie_data = {
            "title": title,
            "poster": poster,
            "downloadUrl": download_url,
            "createdAt": datetime.datetime.now(datetime.timezone.utc)
        }

        db.collection("movies").add(movie_data)
        
        bot.reply_to(
            message, 
            f"✅ **Movie Website Par Live Ho Gayi!**\n\n🎬 **Title:** {title}\n🖼️ **Poster:** Added\n🔗 **Link:** Added", 
            parse_mode="Markdown"
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error aayi: {str(e)}")

print("Bot successfully start ho gaya hai...")
bot.infinity_polling()
