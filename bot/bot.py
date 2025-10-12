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

bot.set_my_commands([
    types.BotCommand("start", "Запустить бота"),
    types.BotCommand("addnews", "Добавить новость вручную"),
    types.BotCommand("help", "Помощь и инструкция"),
])

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

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот для новостей. Используй /addnews чтобы добавить новость.")

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, "Команды:\n/addnews — добавить новость вручную\n/start — приветствие\n/help — помощь")

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
    now = datetime.now(pytz.timezone("Europe/Moscow"))
    date_str = now.strftime('%Y-%m-%d')
    html = f"<article class='news-item' data-date='{date_str}'>\n"
    if data.get("photo"):
        html += f"<img src='{data['photo']}' alt='Фото' />\n"
    if data.get("video"):
        html += f"<video controls width='640'>\n"
        html += f"  <source src='{data['video']}' type='video/mp4'>\n"
        html += f"  Ваш браузер не поддерживает видео.\n</video>\n"
    if data.get("text"):
        html += f"<p>{data['text']}</p>\n"
    html += f"<p class='timestamp'>🕒 {now.strftime('%d.%m.%Y %H:%M')}</p>\n"
    html += f"<p class='source'>Источник: добавлено вручную</p>\n</article>\n"

    os.makedirs("public", exist_ok=True)
    with open(MANUAL_FILE, "a", encoding="utf-8") as f:
        f.write(html)

    bot.send_message(message.chat.id, "✅ Новость добавлена!", reply_markup=types.ReplyKeyboardRemove())
    bot.delete_state(message.from_user.id)

@bot.message_handler(func=lambda m: m.text == "❌ Отмена", state=AddNewsStates.confirm)
def cancel_news(message):
    user_data.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "❌ Добавление отменено.", reply_markup=types.ReplyKeyboardRemove())
    bot.delete_state(message.from_user.id)
def fetch_latest_posts():
    bot.remove_webhook()
    time.sleep(1)
    updates = bot.get_updates(limit=30, timeout=5)
    posts = [
        u.channel_post
        for u in updates
        if u.channel_post and u.channel_post.chat.username == CHANNEL_ID[1:]
    ]
    grouped = defaultdict(list)
    for post in posts:
        group_id = getattr(post, 'media_group_id', None)
        key = group_id if group_id else f"single_{post.message_id}"
        grouped[key].append(post)
    return list(grouped.items())

def format_post(messages):
    timestamp = datetime.fromtimestamp(messages[0].date, pytz.timezone("Europe/Moscow"))
    date_str = timestamp.strftime('%Y-%m-%d')
    html = f"<article class='news-item' data-date='{date_str}'>\n"
    caption = ""
    video_shown = False
    for msg in messages:
        if msg.content_type == 'photo':
            try:
                file_info = bot.get_file(msg.photo[-1].file_id)
                file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
                html += f"<img src='{file_url}' alt='Фото' />\n"
            except:
                html += f"<p>📷 Фото недоступно</p>\n"
            if msg.caption:
                caption = clean_text(msg.caption)
        elif msg.content_type == 'video':
            if msg.caption:
                caption = clean_text(msg.caption)
            if not video_shown:
                try:
                    file_info = bot.get_file(msg.video.file_id)
                    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
                    html += f"<video controls width='640'>\n"
                    html += f"  <source src='{file_url}' type='video/mp4'>\n"
                    html += f"  Ваш браузер не поддерживает видео.\n</video>\n"
                    video_shown = True
                except:
                    html += f"<p><a href='https://t.me/{CHANNEL_ID[1:]}/{msg.message_id}' target='_blank'>Смотреть видео в Telegram</a></p>\n"
            else:
                html += f"<p><a href='https://t.me/{CHANNEL_ID[1:]}/{msg.message_id}' target='_blank'>Смотреть видео в Telegram</a></p>\n"
        elif msg.content_type == 'text':
            caption = clean_text(msg.text)
    if caption:
        html += f"<p>{caption}</p>\n"
    html += f"<p class='timestamp'>🕒 {timestamp.strftime('%d.%m.%Y %H:%M')}</p>\n"
    html += f"<a href='https://t.me/{CHANNEL_ID[1:]}/{messages[0].message_id}' target='_blank'>Читать в Telegram</a>\n"
    html += f"<p class='source'>Источник: {messages[0].chat.title}</p>\n</article>\n"
    return html, timestamp

def load_seen_ids():
    if not os.path.exists(SEEN_IDS_FILE):
        return set()
    with open(SEEN_IDS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_seen_ids(ids):
    with open(SEEN_IDS_FILE, "a") as f:
        for id in ids:
            f.write(f"{id}\n")

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
    print("⚙️ Запуск main()")
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
        print("ℹ️ Нет новых постов.")
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
    print("✅ main() завершён")

if __name__ == "__main__":
    mode = os.getenv("BOT_MODE", "polling")
    print("🟡 Запуск bot.py — режим:", mode)
    if mode == "polling":
        print("📲 Запускаем Telegram-бот")
        bot.polling(none_stop=True)
    elif mode == "generate":
        main()