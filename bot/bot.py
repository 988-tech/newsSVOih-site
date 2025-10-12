import os
import time
import telebot
from datetime import datetime
import pytz
from collections import defaultdict
from telethon.sync import TelegramClient

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@newsSVOih"
SEEN_IDS_FILE = "seen_ids.txt"
BOT_MODE = os.getenv("BOT_MODE", "polling")

bot = telebot.TeleBot(TOKEN)

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

def fetch_latest_posts():
    if BOT_MODE == "generate":
        api_id = int(os.getenv("TG_API_ID"))
        api_hash = os.getenv("TG_API_HASH")
        with TelegramClient('bot/session', api_id, api_hash) as client:
            messages = client.get_messages(CHANNEL_ID, limit=30)
            grouped = defaultdict(list)
            for msg in messages:
                group_id = msg.grouped_id or f"single_{msg.id}"
                grouped[group_id].append(msg)
            return list(grouped.items())
    else:
        bot.remove_webhook()
        time.sleep(1)
        updates = bot.get_updates()
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

        return list(grouped.items())[-30:] if grouped else []

def format_post(messages):
    timestamp = datetime.fromtimestamp(messages[0].date.timestamp(), pytz.timezone("Europe/Moscow"))
    date_str = timestamp.strftime('%Y-%m-%d')
    html = f"<article class='news-item' data-date='{date_str}'>\n"
    caption = ""
    video_shown = False

    for msg in messages:
        if hasattr(msg, 'photo') and msg.photo:
            file_url = f"https://t.me/{CHANNEL_ID[1:]}/{msg.id}"
            html += f"<img src='{file_url}' alt='Фото' />\n"
            if msg.text:
                caption = clean_text(msg.text)

        elif hasattr(msg, 'video') and msg.video:
            if msg.text:
                caption = clean_text(msg.text)
            if not video_shown:
                file_url = f"https://t.me/{CHANNEL_ID[1:]}/{msg.id}"
                html += f"<video controls width='640'>\n"
                html += f"  <source src='{file_url}' type='video/mp4'>\n"
                html += f"  Ваш браузер не поддерживает видео.\n"
                html += f"</video>\n"
                video_shown = True
            else:
                html += f"<p><a href='{file_url}' target='_blank'>Смотреть видео в Telegram</a></p>\n"

        elif msg.text:
            caption = clean_text(msg.text)

    if caption:
        html += f"<p>{caption}</p>\n"

    html += f"<p class='timestamp'>🕒 {timestamp.strftime('%d.%m.%Y %H:%M')}</p>\n"
    html += f"<a href='https://t.me/{CHANNEL_ID[1:]}/{messages[0].id}' target='_blank'>Читать в Telegram</a>\n"
    html += f"<p class='source'>Источник: {CHANNEL_ID}</p>\n"
    html += "</article>\n"
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
    <loc>https://newssvoih.ru/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>"""

    if archive_exists:
        sitemap += f"""
  <url>
    <loc>https://newssvoih.ru/archive.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>"""

    sitemap += "\n</urlset>"

    with open("public/sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)

def save_posts_to_archive(posts):
    seen_ids = load_seen_ids()
    new_html = ""
    new_ids = []

    for group in posts:
        first_msg = group[0]
        if str(first_msg.id) in seen_ids:
            continue
        html, timestamp = format_post(group)
        new_html += html
        new_ids.append(str(first_msg.id))

    if not new_html:
        print("⏳ Нет новых постов")
        return

    archive_path = "public/archive.html"
    if os.path.exists(archive_path):
        with open(archive_path, "r", encoding="utf-8") as f:
            existing = f.read()
    else:
        existing = ""

    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(new_html + existing)

    save_seen_ids(new_ids)
    update_sitemap()
    print(f"✅ Добавлено {len(new_ids)} новых постов")

if __name__ == "__main__":
    if BOT_MODE == "generate":
        print("⚙️ Генерация постов из канала...")
        posts = fetch_latest_posts()
        save_posts_to_archive([group for _, group in posts])
    else:
        print("🤖 Бот запущен в режиме polling")
        bot.infinity_polling()