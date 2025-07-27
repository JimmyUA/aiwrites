from fastapi import FastAPI, Request
import feedparser
import requests
from datetime import datetime
import google.generativeai as genai

# === CONFIGURATION ===
import os

from firebase import mark_as_posted, has_been_posted

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = "@aiwrites"
GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# === INIT GEMINI ===
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# === FASTAPI APP ===
app = FastAPI()

# === POST TO TELEGRAM ===
def post_to_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHANNEL,
        "text": message,
        "parse_mode": "HTML"
    }
    return requests.post(url, data=payload).json()

# === GET TOP NEWS FROM RSS ===
def get_ai_news_entries():
    feed = feedparser.parse(GOOGLE_NEWS_RSS)
    return feed.entries[:5]

# === LET GEMINI PICK BEST ===
def select_most_exciting_news(entries):
    formatted_entries = ""
    for i, entry in enumerate(entries):
        formatted_entries += f"{i+1}. {entry.title}\n"

    prompt = f"""
Ось кілька заголовків новин про штучний інтелект:

{formatted_entries}

Оціни ці заголовки як редактор новин. Вибери один — найцікавіший, найвірусніший або той, що викликає емоції. Відповідай лише його номером (наприклад, "3").
"""
    response = model.generate_content(prompt)
    try:
        index = int(response.text.strip()) - 1
        return entries[index]
    except Exception:
        return entries[0]  # fallback if something goes wrong

# === SUMMARIZE SELECTED ===
def summarize_in_ukrainian_full_post(title: str, link: str, published: str) -> str:
    prompt = f"""
Склади повністю готовий пост для Telegram-каналу українською мовою на основі новини про штучний інтелект.

Використай наступну інформацію:
- Заголовок: {title}
- Посилання: {link}
- Час публікації: {published}

Пост має бути емоційним, стислим і цікавим. Форматуй його так:

🧠 <b>Заголовок</b>  
📌 Короткий анонс (2–3 речення, з емодзі, без форматування всередині)  
📎 <a href="...">Читати більше</a>  
🕒 <час публікації>

Відповідай лише самим повідомленням у цьому форматі, нічого більше не додавай.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

# === MAIN LOGIC ===
def get_top_ai_news_message():
    entries = get_ai_news_entries()
    if not entries:
        return None

    fresh_entries = [e for e in entries if not has_been_posted(e.link)]
    if not fresh_entries:
        print("😴 No fresh entries found.")
        return None

    selected = select_most_exciting_news(fresh_entries)
    message = summarize_in_ukrainian_full_post(selected.title, selected.link, selected.published)

    mark_as_posted(selected.link)
    return message

# === ENDPOINT ===
@app.get("/trigger")
async def trigger_news_post(request: Request):
    message = get_top_ai_news_message()
    if message:
        result = post_to_telegram(message)
        return {"status": "sent", "telegram_response": result}
    else:
        return {"status": "no news found"}