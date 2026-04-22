import os
import hashlib
from datetime import datetime
import chromadb
import requests
from sentence_transformers import SentenceTransformer


class MemoryManager:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
    def save_interaction(self, user_id: str, user_message: str, bot_response: str):
        collection_name = f"user_{user_id}"
        try:
            collection = self.client.get_collection(collection_name)
        except:
            collection = self.client.create_collection(collection_name)
        
        doc_id = hashlib.md5(f"{datetime.now()}{user_message}".encode()).hexdigest()
        collection.add(
            ids=[doc_id],
            documents=[f"USER: {user_message}\nASSISTANT: {bot_response}"],
            metadatas=[{"timestamp": datetime.now().isoformat()}]
        )
    
    def get_context(self, user_id: str, query: str, n_results: int = 3) -> str:
        collection_name = f"user_{user_id}"
        try:
            collection = self.client.get_collection(collection_name)
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            if results and results['documents'] and results['documents'][0]:
                return "\n---\n".join(results['documents'][0])
        except:
            pass
        return ""


class NVMemoryAgent:
    def __init__(self):
        self.memory = MemoryManager()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "mistral"
        
    def generate_response(self, user_id: str, user_message: str) -> str:
        # Получаем контекст из памяти
        context = self.memory.get_context(user_id, user_message)
        
        # Формируем промпт
        system_prompt = """Ты — NV Ассистент, премиальный B2B помощник. 
Ты должен отвечать тепло, профессионально и кратко (2-3 предложения).
Используй историю диалогов, чтобы персонализировать ответ."""
        
        prompt = f"{system_prompt}\n\n"
        if context:
            prompt += f"История диалогов:\n{context}\n\n"
        prompt += f"Клиент: {user_message}\nАссистент:"
        
        # Запрос к Ollama
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7}
                },
                timeout=60
            )
            
            if response.status_code == 200:
                response_text = response.json().get("response", "").strip()
            else:
                response_text = "Извините, сервер временно недоступен."
        except Exception as e:
            print(f"Ollama ошибка: {e}")
            response_text = "Извините, произошла ошибка. Попробуйте позже."
        
        # Сохраняем в память
        self.memory.save_interaction(user_id, user_message, response_text)
        
        return response_text