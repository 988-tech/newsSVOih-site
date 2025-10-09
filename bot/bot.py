import os
import telebot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = "@newsSVOih"

bot = telebot.TeleBot(TOKEN)

def clean_text(text):
    return text.replace("https://t.me/newsSVOih", "").strip()

@bot.channel_post_handler(content_types=['text', 'photo'])
def handle_post(message):
    html = "<article class='news-item'>\n"

    if message.content_type == 'text':
        html += f"<p>{clean_text(message.text)}</p>\n"

    elif message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        caption = clean_text(message.caption or "")
        html += f"<img src='{file_url}' alt='Фото' />\n"
        html += f"<p>{caption}</p>\n"

    html += f"<a href='https://t.me/newsSVOih/{message.message_id}' target='_blank'>Читать в Telegram</a>\n"
    html += "</article>\n"

    with open("public/news.html", "a", encoding="utf-8") as f:
        f.write(html)

bot.polling()