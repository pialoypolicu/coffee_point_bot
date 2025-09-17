import asyncio
import os
import sys
from logging.config import fileConfig
from os.path import abspath, dirname

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.database.models import Base

# Добавляем путь к проекту в PYTHONPATH
sys.path.insert(0, dirname(dirname(abspath(__file__))))

# Загружаем переменные окружения
load_dotenv()


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Интерполируем переменные окружения в строку подключения
section = config.config_ini_section
config.set_section_option(section, "DB_DRIVER", os.getenv("DRIVER_NAME", "postgresql+asyncpg"))
config.set_section_option(section, "DB_USER", os.getenv("USERNAME", "postgres"))
config.set_section_option(section, "DB_PASSWORD", os.getenv("PASSWORD", "postgres"))
config.set_section_option(section, "DB_HOST", os.getenv("HOST", "127.0.0.1"))
config.set_section_option(section, "DB_NAME", os.getenv("DATABASE", "postgres"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    # Используем ваш существующий URL из base.py
    from app.database.base import url_object

    connectable = create_async_engine(str(url_object))

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    from app.database.base import url_object

    context.configure(
        url=str(url_object),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
