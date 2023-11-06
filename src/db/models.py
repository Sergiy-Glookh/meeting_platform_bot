from mongoengine import *
from datetime import datetime
import json


class UserState:

    def __init__(self):
        self.selected_regions = []
        self.index_page = 0
        self.selected_cites = {}
        self.matched_cities = []

        # self.birth_day = None
        # self.birth_month = None
        # self.birth_year = None

        self.categories_list = []  # список категорій, які для користувача визначив чат-бот
        self.selected_categories = []  # категорії, які обрав користувач
        self.status = None  # статус для очікування відповіді


class City(Document):
    region = StringField(unique=True, required=True)
    cities = ListField()

    def json(self):
        user_dict = {
            "region": self.region,
            "cities": self.cities,
        }

        return json.dumps(user_dict)


class User(Document):
    user_id = IntField(primary_key=True)
    username = StringField(unique=True, required=True)
    name = StringField(required=True)
    photo = StringField()
    description = StringField(max_length=500)
    location = ListField()
    interests = ListField()
    date_created = DateTimeField(default=datetime.utcnow())
    birth_day = IntField()
    birth_month = IntField()
    birth_year = IntField()

    def json(self):
        user_dict = {
            "username": self.username,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "interests": self.interests,
            "birth_day": self.birth_day,
            "birth_month": self.birth_month,
            "birth_year": self.birth_year,
        }

        return json.dumps(user_dict)

    meta = {
        "indexes": ["username"],
        "ordering": ["-date_created"]
    }


async def create_profile(message):
    try:
        user = User.objects(user_id=message.id).get()

    except DoesNotExist:
        if message.username:
            user = User(
                user_id=message.id,
                username=message.username,
                name=message.full_name,
            )
        else:
            user = User(
                user_id=message.id,
                name=message.full_name,
            )
        user.save()


async def edit_profile(state, user_id):
    async with state.proxy() as data:
        User.objects(user_id=user_id).update(
            set__name=data["name"],
            set__birth_day=data["birth_day"],
            set__birth_month=data["birth_month"],
            set__birth_year=data["birth_year"],
        )


async def add_interests(interests, user_id):
    User.objects(user_id=user_id).update(
        set__interests=interests,
    )


async def add_location(location, user_id):
    User.objects(user_id=user_id).update(
        set__location=location,
    )


def get_regions_and_cities():
    regions_and_cities = {}
    try:
        regions = City.objects()
        for region in regions:
            regions_and_cities[region.region] = region.cities
    except DoesNotExist:
        print("Regions not found")
    return regions_and_cities
