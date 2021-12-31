import logging
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
storage = MemoryStorage()
token = "токен бота"
bot = Bot(token=token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)
