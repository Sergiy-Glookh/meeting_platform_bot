import pymongo
import configparser
import certifi
ca = certifi.where()

config = configparser.ConfigParser()
config.read('config.ini')

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

