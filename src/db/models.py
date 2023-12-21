from mongoengine import *
from datetime import datetime, date
import json


class UserState:
    def __init__(self):
        self.selected_regions = []
        self.index_page = 0
        self.selected_cites = {}
        self.matched_cities = []

        self.categories_list = []  # список категорій, які для користувача визначив чат-бот
        self.selected_categories = []  # категорії, які обрав користувач
        self.status = None  # статус для очікування відповіді

    def __str__(self):
        return f"{self.selected_regions}\n{self.index_page}\n{self.selected_cites}\n{self.matched_cities}\n\n" \
               f"{self.categories_list}\n{self.selected_categories}\n{self.status}"


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
    birthday = DateTimeField()
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
            "birthday": self.birthday,
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
        data_birthday = date(int(data["birth_year"]), int(data["birth_month"]), int(data["birth_day"]))
        User.objects(user_id=user_id).update(
            set__name=data["name"],
            set__birthday=data_birthday,
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


class Meeting(Document):
    meeting_id = StringField(primary_key=True)
    user_id = IntField(required=True)
    meeting_name = StringField(required=True)
    description = StringField()
    city = StringField(required=True)
    region = StringField(required=True)
    datetime = DateTimeField(required=True)
    participants = ListField()
    timestamp = DateTimeField()
    comment = StringField()
    street = StringField()
    house_number = StringField()

