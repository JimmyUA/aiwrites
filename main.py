from fastapi import FastAPI, Request
import feedparser
import requests
from datetime import datetime
import google.generativeai as genai

# === CONFIGURATION ===
import os

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
def summarize_in_ukrainian(title: str) -> str:
    prompt = f"""
Заголовок новини: "{title}"

Напиши стислий, емоційний анонс цією новини українською мовою. Стиль — як для Telegram-каналу. 2-3 речення.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

# === MAIN LOGIC ===
def get_top_ai_news_message():
    entries = get_ai_news_entries()
    if not entries:
        return None

    selected = select_most_exciting_news(entries)
    summary = summarize_in_ukrainian(selected.title)

    return f"""🧠 <b>{selected.title}</b>

📌 {summary}

📎 <a href="{selected.link}">Читати більше</a>
🕒 {selected.published}
"""

# === ENDPOINT ===
@app.get("/trigger")
async def trigger_news_post(request: Request):
    message = get_top_ai_news_message()
    if message:
        result = post_to_telegram(message)
        return {"status": "sent", "telegram_response": result}
    else:
        return {"status": "no news found"}