from dotenv import dotenv_values

from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from mongoengine import connect
import speech_recognition as sr

from src.db.models import get_regions_and_cities

config = dotenv_values()  # config = {"USER": "foo", "EMAIL": "foo@example.org"}
DB = config.get("DB")
TOKEN_API = config.get("TOKEN_API")
TOKEN_ADMIN_API = config.get("TOKEN_ADMIN_API")
NOVA_POSHTA_API_KEY = config.get("NOVA_POSHTA_API_KEY")
CITIES_SEARCH_URL = config.get("CITIES_SEARCH_URL")

connect(db='meeting-bot', host=DB)

recognizer = sr.Recognizer()
storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)

ALL_REGIONS_AND_CITIES = get_regions_and_cities()
CATEGORIES = [
    'Технології',
    'Мистецтво та Культура',
    'Спорт',
    'Кулінарія',
    'Наука та Дослідження',
    'Спільноти та Благодійність',
    'Мода та Краса',
    'Музика',
    'Подорожі',
    'Бізнес та Підприємництво'
]
