from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from mongoengine import *
from db.models import create_profile, edit_profile
from geopy.geocoders import Nominatim
from dotenv import dotenv_values

config = dotenv_values(".env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}
DB = config.get("DB")
TOKEN_API = config.get("TOKEN_API")

connect(db='mongo_test', host=DB)

storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)
geolocator = Nominatim(user_agent="myGeocoder")


class ProfileStatesGroup(StatesGroup):
    photo = State()
    name = State()
    age = State()
    description = State()
    location = State()


def get_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("/create"))
    return kb


def get_cancel_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("/cancel"))
    return kb


@dp.message_handler(commands=["cancel"], state="*")
async def cmd_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.finish()
    await message.reply("Ви перервали створення анкети :(",
                        reply_markup=get_kb())


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message) -> None:
    await message.answer("Вечір добрий!  Щоб створити профіль - введи /create",
                         reply_markup=get_kb())
    await create_profile(message.from_user)


@dp.message_handler(commands=["create"])
async def cmd_create(message: types.Message) -> None:
    await message.reply("Давайте створимо ваш профіль! Щоб розпочати,  відправ мені свою фотографію!",
                        reply_markup=get_cancel_kb())
    await ProfileStatesGroup.photo.set()


@dp.message_handler(lambda message: not message.photo, state=ProfileStatesGroup.photo)
async def check_photo(message: types.Message):
    await message.reply("Це не фотографія")


@dp.message_handler(content_types=["photo"], state=ProfileStatesGroup.photo)
async def load_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["photo"] = message.photo[0].file_id

    await message.reply("Тепер відправ, як до тебе звертатись")
    await ProfileStatesGroup.next()


@dp.message_handler(state=ProfileStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["name"] = message.text

    await message.reply("Скільки тобі років?")
    await ProfileStatesGroup.next()


@dp.message_handler(lambda message: not message.text.isdigit() or float(message.text) < 14 or float(message.text) > 80,
                    state=ProfileStatesGroup.age)
async def check_age(message: types.Message):
    await message.reply("Введіть реальний вік!!!")


@dp.message_handler(state=ProfileStatesGroup.age)
async def load_age(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["age"] = message.text

    await message.reply("А тепер розкажи трохи про себе!")
    await ProfileStatesGroup.next()


@dp.message_handler(state=ProfileStatesGroup.description)
async def load_desc(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["description"] = message.text

    button = KeyboardButton("Відправити геолокацію", request_location=True)
    keyboard = ReplyKeyboardMarkup().add(button)
    await message.reply("Будь ласка, натисність на кнопку щоб відправити ваше місцезнаходження", reply_markup=keyboard)
    await ProfileStatesGroup.next()


@dp.message_handler(state=ProfileStatesGroup.location, content_types=types.ContentTypes.LOCATION)
async def load_location(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        latitude = message.location.latitude
        longitude = message.location.longitude

        # location = geolocator.reverse((latitude, longitude))
        # print(location)
        # # print(location.raw["city"])
        city = "address"

        data["location"] = city
        await bot.send_photo(chat_id=message.from_user.id,
                             photo=data["photo"],
                             caption=f"{data['name']}, {data['age']}, {data['location']}\n{data['description']}")

    await edit_profile(state, user_id=message.from_user.id)
    await message.reply("Ваша анкета успішно створена!!!")
    await state.finish()


if __name__ == "__main__":
    executor.start_polling(dp,
                           skip_updates=True)

