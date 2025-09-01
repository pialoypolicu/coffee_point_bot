import ast
import os

from dotenv import load_dotenv

load_dotenv()

ADMIN_IDS = ast.literal_eval(os.getenv("ADMIN_IDS"))  # tg id админа.
