import os
import telebot
from fastapi import FastAPI, Request
from memory_rag import NVMemoryAgent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
memory_agent = NVMemoryAgent()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        if "message" not in data:
            return {"status": "ok"}
        
        message = data["message"]
        chat_id = message["chat"]["id"]
        user_text = message.get("text", "")
        
        if not user_text:
            return {"status": "ok"}
        
        print(f"📨 Получено от {chat_id}: {user_text}")
        response_text = memory_agent.generate_response(str(chat_id), user_text)
        print(f"🤖 Ответ: {response_text}")
        
        # Пробуем отправить
        bot.send_message(chat_id, response_text)
        
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"status": "error"}

@app.get("/health")
async def health():
    return {"status": "alive"}