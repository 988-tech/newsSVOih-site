import os
import time
import telebot
from datetime import datetime
import pytz

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@newsSVOih"
SEEN_IDS_FILE = "seen_ids.txt"

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
    bot.remove_webhook()
    time.sleep(1)
    updates = bot.get_updates()
    posts = [
        u.channel_post
        for u in updates
        if u.channel_post and u.channel_post.chat.username == CHANNEL_ID[1:]
    ]
    return posts[-5:] if posts else []

def format_post(message):
    html = "<article class='news-item'>\n"

    if message.content_type == 'text':
        html += f"<p>{clean_text(message.text)}</p>\n"

    elif message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        caption = clean_text(message.caption or "")
        html += f"<img src='{file_url}' alt='Фото' />\n"
        html += f"<p>{caption}</p>\n"

    elif message.content_type == 'video':
        file_info = bot.get_file(message.video.file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        caption = clean_text(message.caption or "")
        html += f"<video controls width='640'>\n"
        html += f"  <source src='{file_url}' type='video/mp4'>\n"
        html += f"  Ваш браузер не поддерживает видео.\n"
        html += f"</video>\n"
        html += f"<p>{caption}</p>\n"

    moscow_tz = pytz.timezone("Europe/Moscow")
    timestamp = datetime.fromtimestamp(message.date, moscow_tz).strftime("%d.%m.%Y %H:%M")
    html += f"<p class='timestamp'>🕒 {timestamp}</p>\n"
    html += f"<a href='https://t.me/newsSVOih/{message.message_id}' target='_blank'>Читать в Telegram</a>\n"
    html += f"<p class='source'>Источник: {message.chat.title}</p>\n"
    html += "</article>\n"
    return html

def load_seen_ids():
    if not os.path.exists(SEEN_IDS_FILE):
        return set()
    with open(SEEN_IDS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_seen_ids(ids):
    with open(SEEN_IDS_FILE, "a") as f:
        for id in ids:
            f.write(f"{id}\n")

def main():
    posts = fetch_latest_posts()
    seen_ids = load_seen_ids()
    new_posts = [p for p in posts if str(p.message_id) not in seen_ids]

    if not new_posts:
        print("Нет новых постов.")
        return

    os.makedirs("public", exist_ok=True)

    old_content = ""
    if os.path.exists("public/news.html"):
        with open("public/news.html", "r", encoding="utf-8") as f:
            old_content = f.read()

    new_content = ""
    new_ids = []
    for post in reversed(new_posts):  # новые посты сверху
        new_content += format_post(post)
        new_ids.append(str(post.message_id))

    full_content = new_content + old_content

    with open("public/news.html", "w", encoding="utf-8") as f:
        f.write(full_content)

    save_seen_ids(new_ids)

if __name__ == "__main__":
    main()