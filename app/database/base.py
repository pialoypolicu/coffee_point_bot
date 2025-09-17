import os

from dotenv import load_dotenv
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

url_object = URL.create(
    os.getenv("DRIVER_NAME", "postgresql+asyncpg"),
    username=os.getenv("USERNAME", "postgres"),
    password=os.getenv("PASSWORD", "postgres"),
    host=os.getenv("HOST", "127.0.0.1"),
    database=os.getenv("DATABASE", "postgres"),
)

async_engine = create_async_engine(url_object)
