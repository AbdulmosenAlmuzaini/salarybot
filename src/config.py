import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./accounting_bot.db")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment variables")
