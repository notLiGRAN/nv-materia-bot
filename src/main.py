import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

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
        
        # Простое эхо (без памяти и нейросети)
        response_text = f"Эхо: {user_text}"
        
        print(f"🤖 Ответ: {response_text}")
        
        # Отправляем обратно
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": response_text}, timeout=30)
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return {"status": "error"}

@app.get("/health")
async def health():
    return {"status": "alive", "service": "NV Echo Bot"}