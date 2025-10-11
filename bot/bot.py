import os
import time
import telebot
from datetime import datetime
import pytz
from collections import defaultdict

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

    grouped = defaultdict(list)
    for post in posts:
        group_id = getattr(post, 'media_group_id', None)
        key = group_id if group_id else f"single_{post.message_id}"
        grouped[key].append(post)

    return list(grouped.items())[-10:] if grouped else []

def format_post(messages):
    html = "<article class='news-item'>\n"
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
                    html += f"  Ваш браузер не поддерживает видео.\n"
                    html += f"</video>\n"
                    video_shown = True
                except:
                    html += f"<p><a href='https://t.me/{CHANNEL_ID[1:]}/{msg.message_id}' target='_blank'>Смотреть видео в Telegram</a></p>\n"
            else:
                html += f"<p><a href='https://t.me/{CHANNEL_ID[1:]}/{msg.message_id}' target='_blank'>Смотреть видео в Telegram</a></p>\n"

        elif msg.content_type == 'text':
            caption = clean_text(msg.text)

    if caption:
        html += f"<p>{caption}</p>\n"

    timestamp = datetime.fromtimestamp(messages[0].date, pytz.timezone("Europe/Moscow")).strftime("%d.%m.%Y %H:%M")
    html += f"<p class='timestamp'>🕒 {timestamp}</p>\n"
    html += f"<a href='https://t.me/{CHANNEL_ID[1:]}/{messages[0].message_id}' target='_blank'>Читать в Telegram</a>\n"
    html += f"<p class='source'>Источник: {messages[0].chat.title}</p>\n"
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

    old_content = ""
    if os.path.exists("public/news.html"):
        with open("public/news.html", "r", encoding="utf-8") as f:
            old_content = f.read()

    new_content = ""
    for group in reversed(new_groups):  # новые посты сверху
        new_content += format_post(group)

    full_content = new_content + old_content

    with open("public/news.html", "w", encoding="utf-8") as f:
        f.write(full_content)

    save_seen_ids(new_ids)

if __name__ == "__main__":
    main()