# from mongoengine import Document, StringField, DateTimeField
# from datetime import datetime
#
#
# class Meeting(Document):
#     user_id = StringField(required=True)
#     city = StringField(required=True)
#     region = StringField(required=True)
#     datetime = DateTimeField(required=True)
#     timestamp = DateTimeField(required=True)
#     meeting_name = StringField(required=True)
#     description = StringField(required=True)
#
#     @classmethod
#     def create_meeting(cls, user_id, city, region, date_time, meeting_name, description):
#         timestamp = datetime.now()
#         meeting = cls(
#             user_id=user_id,
#             city=city,
#             region=region,
#             datetime=date_time,
#             timestamp=timestamp,
#             meeting_name=meeting_name,
#             description=description
#         )
#         meeting.save()
#         return meeting
#
#     @staticmethod
#     def get_formatted_datetime(date_time):
#         return date_time.strftime('%Y-%m-%d' ' о ' '%H:%M' ' годині')
#
#
# class JoinedUsers(Document):
#     user_id = StringField(required=True)
#     user_username = StringField(required=True)
#
#     @classmethod
#     def add_joined_user(cls, user_id, user_username):
#         doc = cls(user_id=user_id, user_username=user_username)
#         doc.save()



from datetime import datetime
from connect import client


db = client['my_db']
class Meeting:
    collection = db['meetings']

    @classmethod
    def create_meeting(cls, user_id, user_data):
        user_data['timestamp'] = datetime.now()
        cls.collection.insert_one(user_data)

    @classmethod
    def get_formatted_datetime(cls, date_time):
        return date_time.strftime('%Y-%m-%d' ' о ' '%H:%M' ' годині')

class JoinedUsers:
    collection = db['joined_users']

    @classmethod
    def add_joined_user(cls, user_id, user_username):
        doc = {
            "add_user": {
                "user_id": user_id,
                "user_username": user_username
            }
        }
        cls.collection.insert_one(doc)

