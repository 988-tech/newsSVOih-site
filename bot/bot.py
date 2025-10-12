import os
import time
import telebot
from datetime import datetime, timedelta
import pytz
from collections import defaultdict

from telebot import types
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@newsSVOih"
SEEN_IDS_FILE = "seen_ids.txt"
MANUAL_FILE = "public/manual_news.html"

bot = telebot.TeleBot(TOKEN, state_storage=StateMemoryStorage())

class AddNewsStates(StatesGroup):
    waiting_text = State()
    waiting_photo = State()
    waiting_video = State()
    confirm = State()

user_data = {}

def clean_text(text):
    if not text:
        return ""
    text = text.replace("https://t.me/newsSVOih", "").strip()
    unwanted_phrases = [
        "💪Подписаться на новости для своих🇷🇺",
        "Подписаться на новости для своих🇷🇷",
        "Подписаться на канал",
        "Читайте нас в Telegram",
    ]
    for phrase in unwanted_phrases:
        text = text.replace(phrase, "")
    return text.strip()

@bot.message_handler(commands=['addnews'])
def start_add_news(message):
    user_data[message.chat.id] = {"text": "", "photo": "", "video": ""}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Текст", "📎 Фото", "🎥 Видео")
    markup.add("✅ Сохранить", "❌ Отмена")
    bot.send_message(message.chat.id, "Что хочешь добавить?", reply_markup=markup)
    bot.set_state(message.from_user.id, AddNewsStates.confirm)

@bot.message_handler(func=lambda m: m.text == "📝 Текст", state=AddNewsStates.confirm)
def ask_text(message):
    bot.send_message(message.chat.id, "Введи текст новости:")
    bot.set_state(message.from_user.id, AddNewsStates.waiting_text)

@bot.message_handler(state=AddNewsStates.waiting_text)
def receive_text(message):
    user_data[message.chat.id]["text"] = message.text
    bot.send_message(message.chat.id, "Текст сохранён.")
    bot.set_state(message.from_user.id, AddNewsStates.confirm)

@bot.message_handler(func=lambda m: m.text == "📎 Фото", state=AddNewsStates.confirm)
def ask_photo(message):
    bot.send_message(message.chat.id, "Пришли фото.")
    bot.set_state(message.from_user.id, AddNewsStates.waiting_photo)

@bot.message_handler(content_types=['photo'], state=AddNewsStates.waiting_photo)
def receive_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
    user_data[message.chat.id]["photo"] = file_url
    bot.send_message(message.chat.id, "Фото сохранено.")
    bot.set_state(message.from_user.id, AddNewsStates.confirm)

@bot.message_handler(func=lambda m: m.text == "🎥 Видео", state=AddNewsStates.confirm)
def ask_video(message):
    bot.send_message(message.chat.id, "Пришли видео.")
    bot.set_state(message.from_user.id, AddNewsStates.waiting_video)

@bot.message_handler(content_types=['video'], state=AddNewsStates.waiting_video)
def receive_video(message):
    file_info = bot.get_file(message.video.file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
    user_data[message.chat.id]["video"] = file_url
    bot.send_message(message.chat.id, "Видео сохранено.")
    bot.set_state(message.from_user.id, AddNewsStates.confirm)

@bot.message_handler(func=lambda m: m.text == "✅ Сохранить", state=AddNewsStates.confirm)
def save_news(message):
    data = user_data.get(message.chat.id, {})
def update_sitemap():
    today = datetime.now().strftime("%Y-%m-%d")
    archive_exists = os.path.exists("public/archive.html")

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://newsSVOih.ru/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://newsSVOih.ru/news.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>0.9</priority>
  </url>"""

    if archive_exists:
        sitemap += f"""
  <url>
    <loc>https://newsSVOih.ru/archive.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.5</priority>
  </url>"""

    sitemap += "\n</urlset>"

    with open("public/sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)

def main():
    grouped_posts = fetch_latest_posts()
    seen_ids = load_seen_ids()

    new_groups = []
    new_ids = []

    for _, group in grouped_posts:
        group_ids = [str(msg.message_id) for msg in group]
        if any(gid in seen_ids for gid in group_ids):
            continue
        new_groups.append(group)
        new_ids.extend(group_ids)

    if not new_groups:
        print("Нет новых постов.")
        return

    os.makedirs("public", exist_ok=True)

    cutoff = datetime.now(pytz.timezone("Europe/Moscow")) - timedelta(days=5)

    old_news = ""
    if os.path.exists("public/news.html"):
        with open("public/news.html", "r", encoding="utf-8") as f:
            old_news = f.read()

    old_archive = ""
    if os.path.exists("public/archive.html"):
        with open("public/archive.html", "r", encoding="utf-8") as f:
            old_archive = f.read()

    manual_news = ""
    if os.path.exists("public/manual_news.html"):
        with open("public/manual_news.html", "r", encoding="utf-8") as f:
            manual_news = f.read()

    new_news = ""
    new_archive = ""

    for group in reversed(new_groups):
        html, ts = format_post(group)
        if ts < cutoff:
            new_archive += html
        else:
            new_news += html

    with open("public/news.html", "w", encoding="utf-8") as f:
        f.write(manual_news + new_news + old_news)

    with open("public/archive.html", "w", encoding="utf-8") as f:
        f.write(new_archive + old_archive)

    save_seen_ids(new_ids)
    update_sitemap()

if __name__ == "__main__":
    main()