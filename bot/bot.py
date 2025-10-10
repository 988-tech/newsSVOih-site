import os
import telebot
import pytz
from datetime import datetime
from dotenv import load_dotenv
import subprocess

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL = os.getenv("TELEGRAM_CHANNEL")  # без @

bot = telebot.TeleBot(TOKEN)

def fetch_latest_posts():
    updates = bot.get_updates()
    posts = []
    for update in updates:
        if update.message:
            posts.append(update.message)
    return posts[-10:]  # последние 10 постов

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

def wrap_html(content):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <title>Новости</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1>Последние новости</h1>
  {content}
</body>
</html>"""

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

def git_push():
    subprocess.run(["git", "add", "public/news.html", "public/sitemap.xml"])
    subprocess.run(["git", "commit", "-m", "Update news.html and sitemap.xml with latest Telegram posts"])
    subprocess.run(["git", "pull", "--rebase"])
    subprocess.run(["git", "push"])

def main():
    posts = fetch_latest_posts()
    os.makedirs("public", exist_ok=True)

    generate_sitemap()

    html_content = ""
    if not posts:
        html_content = f"<p>Нет новых постов — {datetime.now()}</p>"
    else:
        for post in reversed(posts):
            html_content += format_post(post)

    with open("public/news.html", "w", encoding="utf-8") as f:
        f.write(wrap_html(html_content))

    git_push()

if __name__ == "__main__":
    main()