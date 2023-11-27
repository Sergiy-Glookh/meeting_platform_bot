import configparser
import certifi
from db_manager import DatabaseManager
from aiogram import Bot, Dispatcher

ca = certifi.where()

config = configparser.ConfigParser()
config.read('config.ini')
TOKEN = config.get('BOT', 'token')

mongo_user = config.get('DB', 'admin')
mongodb_pass = config.get('DB', 'password')
mong_domain = config.get('DB', 'domain')
DB_URI = f"mongodb+srv://{mongo_user}:{mongodb_pass}@{mong_domain}.mongodb.net/?retryWrites=true&w=majority"


db_manager = DatabaseManager(db_uri=DB_URI, db_name="admin_db")
db_manager.connect()

bot = Bot(TOKEN)
dp = Dispatcher(bot)



