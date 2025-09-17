import ast
import contextvars
import os

from dotenv import load_dotenv

load_dotenv()

ADMIN_IDS = ast.literal_eval(os.getenv("ADMIN_IDS"))  # tg id админа.

# токен для AI чата, общаемся с мозгом через https://openrouter.ai
GPT_TOKEN = os.getenv("GPT_TOKEN")
# урл для отравки заросов в OPENROUTER_URL
OPENROUTER_URL = os.getenv("OPENROUTER_URL")

# Создаем контекстную переменную
current_chat_id = contextvars.ContextVar("current_chat_id", default=None)
