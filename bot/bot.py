import os
import telebot
import pytz
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")

bot = telebot.TeleBot(TOKEN)

def fetch_latest_posts():
    try:
        posts = bot.get_chat_history(CHANNEL, limit=10)
        return posts
    except Exception as e:
        print("Ошибка при получении постов:", e)
        return []

def format_post(post):
    moscow = pytz.timezone("Europe/Moscow")
    timestamp = datetime.fromtimestamp(post.date, tz=moscow).strftime("%d.%m.%Y %H:%M")

    text = post.text or ""
    media = ""

    if post.photo:
        file_id = post.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        media = f'<img src="{file_url}" alt="Фото"><br>'
    elif post.video:
        file_id = post.video.file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        media = f'<video controls src="{file_url}"></video><br>'

    return f"""
    <div class="news-item">
      {media}
      <p>{text}</p>
      <div class="timestamp">Опубликовано: {timestamp}</div>
      <a href="https://t.me/{CHANNEL}/{post.message_id}">Открыть в Telegram</a>
    </div>
    """

def generate_sitemap():
    now = datetime.now().strftime("%Y-%m-%d")
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://newsSVOih.ru/</loc>
    <lastmod>{now}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://newsSVOih.ru/news.html</loc>
    <lastmod>{now}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>
"""
    with open("public/sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)

def main():
    posts = fetch_latest_posts()
    os.makedirs("public", exist_ok=True)

    generate_sitemap()

    with open("public/news.html", "w", encoding="utf-8") as f:
        if not posts:
            f.write(f"<p>Нет новых постов — {datetime.now()}</p>")
        else:
            for post in reversed(posts):
                f.write(format_post(post))

if __name__ == "__main__":
    main()











