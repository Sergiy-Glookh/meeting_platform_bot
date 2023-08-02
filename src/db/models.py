<<<<<<< Updated upstream
=======
from mongoengine import *
from datetime import datetime
import json


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
            set__photo=data["photo"],
            set__age=data["age"],
            set__description=data["description"],
            set__name=data["name"],
            set__location=data["location"],
        )
>>>>>>> Stashed changes
