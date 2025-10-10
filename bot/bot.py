import os
import time
import telebot
from datetime import datetime
import pytz  # ⏰ добавляем поддержку часовых поясов

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@newsSVOih"

bot = telebot.TeleBot(TOKEN)

def clean_text(text):
    return text.replace("https://t.me/newsSVOih", "").strip()

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

    # 🕒 Добавляем московское время
    moscow_tz = pytz.timezone("Europe/Moscow")
    timestamp = datetime.fromtimestamp(message.date, moscow_tz).strftime("%d.%m.%Y %H:%M")
    html += f"<p class='timestamp'>🕒 {timestamp}</p>\n"

    html += f"<a href='https://t.me/newsSVOih/{message.message_id}' target='_blank'>Читать в Telegram</a>\n"
    html += f"<p class='source'>Источник: {message.chat.title}</p>\n"
    html += "</article>\n"
    return html

def main():
    posts = fetch_latest_posts()
    os.makedirs("public", exist_ok=True)
    with open("public/news.html", "w", encoding="utf-8") as f:
        if not posts:
            f.write(f"<p>Нет новых постов — {datetime.now()}</p>")
        else:
            for post in reversed(posts):
    f.write(format_post(post))

if __name__ == "__main__":
    main()










