from mongoengine import *
from datetime import datetime
import json


class UserState:

    def __init__(self):
        self.regions = []
        self.index = 0
        self.select_city = {}
        self.matched_cities = []
        self.status = None

    def __str__(self):
        return f"UserState\n{self.regions}\n{self.index}\n{self.select_city}\n{self.matched_cities}\nEnd\n"


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
    age = IntField()
    description = StringField(max_length=500)
    location = ListField()
    interests = ListField()
    date_created = DateTimeField(default=datetime.utcnow())

    def json(self):
        user_dict = {
            "username": self.username,
            "name": self.name,
            "birthday": self.age,
            "description": self.description,
            "location": self.location,
            "interests": self.interests,
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
        user = User(
            user_id=message.id,
            username=message.username,
            name=message.full_name,
        )
        user.save()


async def edit_profile(state, user_id):
    async with state.proxy() as data:
        User.objects(user_id=user_id).update(
            set__age=data["age"],
            set__description=data["description"],
            set__name=data["name"],
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
