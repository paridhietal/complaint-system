import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_FAST_MODEL = os.getenv("GROQ_FAST_MODEL", "gemma2-9b-it")
GROQ_REASONING_MODEL = os.getenv("GROQ_REASONING_MODEL", "llama-3.3-70b-versatile")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./complaints.db")
