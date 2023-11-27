
from mongoengine import connect, Document
import certifi

class DatabaseManager:
    def __init__(self, db_uri, db_name):
        self.db_uri = db_uri
        self.db_name = db_name
        self.client = None

    def connect(self):
        self.client = connect(db=self.db_name, host=self.db_uri, tlsCAFile=certifi.where())

    def create_user(self, user_data):

        pass

    def update_user(self, user_id, update_data):
        pass
