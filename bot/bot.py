import os
import time
import telebot
from datetime import datetime
import pytz
from collections import defaultdict

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@newsSVOih"
SEEN_GROUPS_FILE = "seen_groups.txt"

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

    return list(grouped.items())[-5:] if grouped else []

def format_post(group_key, messages):
    html = "<article class='news-item'>\n"
    caption = ""
    video_count = sum(1 for msg in messages if msg.content_type == 'video')

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
            if video_count == 1:
                try:
                    file_info = bot.get_file(msg.video.file_id)
                    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
                    html += f"<video controls width='640'>\n"
                    html += f"  <source src='{file_url}' type='video/mp4'>\n"
                    html += f"  Ваш браузер не поддерживает видео.\n"
                    html += f"</video>\n"
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

def load_seen_groups():
    if not os.path.exists(SEEN_GROUPS_FILE):
        return set()
    with open(SEEN_GROUPS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_seen_groups(keys):
    with open(SEEN_GROUPS_FILE, "a") as f:
        for key in keys:
            f.write(f"{key}\n")

def main():
    grouped_posts = fetch_latest_posts()
    seen_groups = load_seen_groups()

    new_groups = []
    new_keys = []

    for key, group in grouped_posts:
        if key not in seen_groups:
            new_groups.append((key, group))
            new_keys.append(key)

    if not new_groups:
        print("Нет новых постов.")
        return

    os.makedirs("public", exist_ok=True)

    old_content = ""
    if os.path.exists("public/news.html"):
        with open("public/news.html", "r", encoding="utf-8") as f:
            old_content = f.read()

    new_content = ""
    for key, group in reversed(new_groups):  # новые посты сверху
        new_content += format_post(key, group)

    full_content = new_content + old_content

    with open("public/news.html", "w", encoding="utf-8") as f:
        f.write(full_content)

    save_seen_groups(new_keys)

if __name__ == "__main__":
    main()