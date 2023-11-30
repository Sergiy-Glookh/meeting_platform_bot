from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from dotenv import dotenv_values
from mongoengine import connect
import speech_recognition as sr

from src.db.models import get_regions_and_cities


config = dotenv_values("../.env")
DB = config.get("DB")
TOKEN_ADMIN_API = config.get("TOKEN_ADMIN_API")
NOVA_POSHTA_API_KEY = config.get("NOVA_POSHTA_API_KEY")
CITIES_SEARCH_URL = config.get("CITIES_SEARCH_URL")

connect(db='meeting-bot', host=DB)

recognizer = sr.Recognizer()
storage = MemoryStorage()
bot = Bot(TOKEN_ADMIN_API)
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



"""
mongo_user = config.get('DB', 'admin')
mongodb_pass = config.get('DB', 'password')
mong_domain = config.get('DB', 'domain')

client = pymongo.MongoClient(
    f"mongodb+srv://{mongo_user}:{mongodb_pass}@cluster0.{mong_domain}.mongodb.net/?retryWrites=true&w=majority",  tlsCAFile=ca)

my_db = client['meeting-bot']
collection = my_db['admin_collection']
joined = my_db['joined']
canceled_meetings = my_db['canceled_meetings']
TOKEN = config.get('BOT', 'token')
GROUP_ID = config.get('BOT', 'grop_id')
"""
