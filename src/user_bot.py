from collections import Counter
import requests
from fuzzywuzzy import fuzz
from db.models import create_profile, edit_profile, get_regions_and_cities, UserState, City, add_location, User
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import types, Bot, Dispatcher
from aiogram.dispatcher import FSMContext
from datetime import datetime

from mongoengine import *
from dotenv import dotenv_values

config = dotenv_values("../.env")  # config = {"USER": "foo", "EMAIL": "foo@example.org"}
DB = config.get("DB")
TOKEN_API = config.get("TOKEN_API")
NOVA_POSHTA_API_KEY = config.get("NOVA_POSHTA_API_KEY")
CITIES_SEARCH_URL = config.get("CITIES_SEARCH_URL")

connect(db='mongo_test', host=DB)

storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)

ALL_REGIONS_AND_CITIES = get_regions_and_cities()
user_states = {}


class ProfileStatesGroup(StatesGroup):
    name = State()
    description = State()
    birth_day = State()
    birth_month = State()
    birth_year = State()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    print(message.from_user.username)
    user_states[user_id] = UserState()
    await create_profile(message.from_user)
    await message.reply("Будь ласка, введіть ваше ім'я:")
    await ProfileStatesGroup.name.set()


# Function to handle region selection
@dp.message_handler(state=ProfileStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["name"] = message.text

    await message.reply("Виберіть день вашого народження:", reply_markup=birth_day_keyboard())
    await ProfileStatesGroup.birth_day.set()


def birth_day_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=10)
    days = list(range(1, 32))
    for i in range(0, len(days), 10):
        row = [InlineKeyboardButton(str(day), callback_data=f"day_{day}") for day in days[i:i + 10]]
        keyboard.add(*row)
    return keyboard


@dp.callback_query_handler(lambda query: query.data.startswith("day_"), state=ProfileStatesGroup.birth_day)
async def select_birth_day(query: types.CallbackQuery, state: FSMContext):
    day = int(query.data.split("_")[1])
    async with state.proxy() as data:
        data["birth_day"] = day

    await state.update_data(birth_day=day)

    await query.message.edit_text(f"Обраний день народження: {day}.\nВиберіть місяць народження:",
                                  reply_markup=birth_month_keyboard())
    await ProfileStatesGroup.birth_month.set()


def birth_month_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=4)
    months = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень",
              "Жовтень", "Листопад", "Грудень"]
    for i in range(0, len(months), 4):
        row = [InlineKeyboardButton(months[j], callback_data=f"month_{j + 1}_{months[j]}") for j in range(i, i + 4)]
        keyboard.add(*row)
    return keyboard


@dp.callback_query_handler(lambda query: query.data.startswith("month_"), state=ProfileStatesGroup.birth_month)
async def select_birth_month(query: types.CallbackQuery, state: FSMContext):
    month = int(query.data.split("_")[1])
    month_name = query.data.split("_")[2]
    async with state.proxy() as data:
        data["birth_month"] = month

    await state.update_data(birth_month=month)

    await query.message.edit_text(f"Обраний місяць народження: {month_name}.\nТепер введіть рік народження:")
    await ProfileStatesGroup.birth_year.set()


@dp.callback_query_handler(lambda query: query.data.startswith("year_"), state=ProfileStatesGroup.birth_year)
async def select_birth_year(query: types.CallbackQuery, state: FSMContext):
    year = int(query.data.split("_")[1])
    async with state.proxy() as data:
        data["birth_year"] = year

    await state.update_data(birth_year=year)
    await state.update_data(birth_month=data["birth_month"])
    await state.update_data(birth_day=data["birth_day"])

    await query.message.edit_text(f"Обраний рік народження: {year}.\nТепер введіть опис про себе:")
    await ProfileStatesGroup.description.set()


@dp.message_handler(state=ProfileStatesGroup.birth_year, content_types=types.ContentType.TEXT)
async def load_birth_year(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["birth_year"] = message.text

    current_year = datetime.now().year

    if not data["birth_year"].isdigit() or int(data["birth_year"]) < (current_year - 80) or int(
            data["birth_year"]) > current_year:
        await message.reply("Рік народження не є дійсним.\nБудь ласка, введіть свій реальний рік народження.")
    else:
        await state.update_data(birth_year=data["birth_year"])
        await message.reply("Відмінно! Тепер розкажіть трохи про себе.")
        await ProfileStatesGroup.description.set()


@dp.message_handler(state=ProfileStatesGroup.description)
async def load_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["description"] = message.text

    await edit_profile(state, user_id=message.from_user.id)
    await state.finish()

    keyboard = InlineKeyboardMarkup()
    for region in ALL_REGIONS_AND_CITIES:
        keyboard.add(InlineKeyboardButton(region, callback_data=region))

    keyboard.add(InlineKeyboardButton("🔸 Моєї області немає", callback_data="unfounded_city"))

    await message.reply(f"Оберіть область/області:", reply_markup=keyboard)


@dp.callback_query_handler(
    lambda query: query.data in ALL_REGIONS_AND_CITIES.keys() or query.data == "back_region")
async def select_region(query: types.CallbackQuery):
    user_id = query.from_user.id
    user_state = user_states[user_id]

    if query.data != "back_region":
        region = query.data

        if region in user_state.selected_regions:
            user_state.selected_regions.remove(region)
        else:
            user_state.selected_regions.append(region)

    keyboard = InlineKeyboardMarkup()
    for region in ALL_REGIONS_AND_CITIES:
        if region in user_state.selected_regions:
            keyboard.add(InlineKeyboardButton(f"✅ {region}", callback_data=region))
        else:
            keyboard.add(InlineKeyboardButton(region, callback_data=region))

    keyboard.add(InlineKeyboardButton("🔸 Моєї області немає", callback_data="unfounded_city"))

    if user_state.selected_regions:
        selected_regions = ', '.join(user_state.selected_regions)
        keyboard.add(InlineKeyboardButton("Перейти до вибору міст ▶️", callback_data="next_city_selection"))
        await query.message.edit_text(text=f"Вибрані області: {selected_regions}\n\nОберіть область/області:",
                                      reply_markup=keyboard)
    else:
        await query.message.edit_text(text="Оберіть область/області:", reply_markup=keyboard)


@dp.callback_query_handler(lambda query: query.data == "unfounded_city")
async def unfounded_city(query: types.CallbackQuery):
    user_id = query.from_user.id
    message_id = query.message.message_id
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Повернутися ↩️", callback_data="back_region"))

    await bot.edit_message_text("Введіть назву міста:", chat_id=user_id, message_id=message_id, reply_markup=keyboard)

    user_state = user_states[user_id]
    user_state.status = "waiting_for_city"


@dp.message_handler(lambda message: user_states[message.from_user.id].status == "waiting_for_city")
async def input_unfounded_city_name(message: types.Message):
    user_id = message.from_user.id
    user_state = user_states[user_id]

    town = message.text

    data = {
        'apiKey': NOVA_POSHTA_API_KEY,
        'modelName': 'Address',
        'calledMethod': 'getCities',
    }

    response = requests.post(CITIES_SEARCH_URL, json=data)

    if response.status_code == 200 and response.json()["success"]:

        cities = response.json()["data"]
        matched_cities = []
        for city in cities:
            if city["SettlementTypeDescription"] == "місто":
                city_name = city["Description"].split('(')[0].strip()

                similarity = fuzz.ratio(town.lower(), city_name.lower())
                if similarity > 70:  # Поріг схожості
                    matched_cities.append(f"{city_name} {city['AreaDescription']}")

        if matched_cities:
            user_state.status = None
            user_state.matched_cities = matched_cities
            keyboard = InlineKeyboardMarkup()
            for city in matched_cities:
                keyboard.add(InlineKeyboardButton(f"м. {city} обл.", callback_data=city))
            keyboard.add(InlineKeyboardButton("Повернутися ↩️", callback_data="back_region"))
            await message.reply("Оберіть місто зі списку:", reply_markup=keyboard)
        else:
            await message.reply("Місто не знайдено. Введіть назву міста ще раз або спробуйте інше місто.")
    else:
        await message.reply("Місто не знайдено. Введіть назву міста ще раз або спробуйте інше місто.")


def generate_selection_keyboard(selected_index, selected_regions, selected_cities, cities):
    keyboard = InlineKeyboardMarkup(row_width=3)

    for city in cities:
        button_text = f"✅ {city}" if city in selected_cities else city
        keyboard.insert(InlineKeyboardButton(button_text, callback_data=city))

    keyboard.row(InlineKeyboardButton("🔸 Мого міста немає", callback_data="unfounded_city"),
                 InlineKeyboardButton("🔹 Обрати усі міста", callback_data="select_all"))

    if len(selected_regions) == 1:
        back_button = InlineKeyboardButton("Повернутися ↩️", callback_data="back_region")
        done_button = InlineKeyboardButton("😺 Готово!", callback_data="done_selected_cities")

        if selected_cities:
            keyboard.row(back_button, done_button)
        else:
            keyboard.add(back_button)
    else:
        is_last_region = selected_index == len(selected_regions) - 1
        prev_region_button = InlineKeyboardButton("⬅️ Попередня область", callback_data="previous_region")
        next_region_button = InlineKeyboardButton("Наступна область ➡️", callback_data="next_region")

        if is_last_region:
            if selected_cities:
                keyboard.row(prev_region_button, InlineKeyboardButton("😺 Готово!", callback_data="done_selected_cities"))
            else:
                keyboard.add(prev_region_button)
        elif selected_index == 0:
            keyboard.row(InlineKeyboardButton("Повернутися ↩️", callback_data="back_region"), next_region_button)
        else:
            keyboard.row(prev_region_button, next_region_button)

    return keyboard


# Function to handle going to next region or previous region
@dp.callback_query_handler(lambda query: query.data == "next_region" or query.data == "previous_region" or
                                         query.data == "next_city_selection" or query.data == "select_all" or
                                         any(query.data in cities_list for cities_list in
                                             ALL_REGIONS_AND_CITIES.values()))
async def go_to_city_selection(query: types.CallbackQuery):
    user_id = query.from_user.id
    user_state = user_states[user_id]

    if query.data == "next_region":

        user_state.index_page += 1
    elif query.data == "previous_region":
        user_state.index_page -= 1
    elif query.data == "next_city_selection":
        user_state.index_page = 0
    elif query.data == "select_all":
        selected_region = user_state.selected_regions[user_state.index_page]
        if selected_region in user_state.selected_cites and Counter(user_state.selected_cites[selected_region]) \
                == Counter(ALL_REGIONS_AND_CITIES[selected_region]):
            user_state.selected_cites[selected_region] = []
        else:
            user_state.selected_cites[selected_region] = ALL_REGIONS_AND_CITIES[selected_region]

    else:
        city = query.data
        selected_region = user_state.selected_regions[user_state.index_page]
        if selected_region in user_state.selected_cites:
            if city in user_state.selected_cites[selected_region]:
                user_state.selected_cites[selected_region].remove(city)
            else:
                user_state.selected_cites[selected_region].append(city)
        else:
            user_state.selected_cites[selected_region] = [city]

    selected_cities = []
    for region in user_state.selected_cites.keys():
        if region in user_state.selected_regions:
            selected_cities.extend(user_state.selected_cites[region])

    selected_region = user_state.selected_regions[user_state.index_page]
    cities = ALL_REGIONS_AND_CITIES[selected_region]

    keyboard = generate_selection_keyboard(user_state.index_page, user_state.selected_regions, selected_cities, cities)

    user_selected_regions = ', '.join(user_state.selected_regions)
    user_selected_cities = ', '.join(selected_cities)
    user_message = f"Вибрані області: {user_selected_regions}\nПоточна область: {selected_region}\n"

    if user_selected_cities:
        user_message += f"Обрані міста: {user_selected_cities}\n"
    user_message += "\nОберіть місто/міста:"

    await query.message.edit_text(text=user_message, reply_markup=keyboard)


# Function to handle finishing selection
@dp.callback_query_handler(
    lambda query: query.data == "done_selected_cities" or query.data in user_states[query.from_user.id].matched_cities)
async def finish_selection(query: types.CallbackQuery):
    user_id = query.from_user.id
    user_state = user_states[user_id]
    if query.data != "done_selected_cities":

        city_name = query.data
        parts = city_name.split()
        city = " ".join(parts[:-1])
        region = parts[-1] + " область"

        # додаємо до бд
        existing_city = City.objects(region=region).first()

        if existing_city:
            if city not in existing_city.cities:
                existing_city.cities.append(city)
                existing_city.save()
        else:
            cities = [city]
            city_obj = City(region=region, cities=cities)
            city_obj.save()

        global ALL_REGIONS_AND_CITIES
        ALL_REGIONS_AND_CITIES = get_regions_and_cities()

        if region not in user_state.selected_regions:
            user_state.selected_regions.append(region)

        if region in user_state.selected_cites:
            if city in user_state.selected_cites[region]:
                user_state.selected_cites[region].remove(city)
            else:
                user_state.selected_cites[region].append(city)
        else:
            user_state.selected_cites[region] = [city]

    selected_regions = user_state.selected_regions
    selected_cities = []
    for region in user_state.selected_cites.keys():
        if region in user_state.selected_regions:
            selected_cities.extend(user_state.selected_cites[region])

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Обрати ще", callback_data="back_region"))
    keyboard.add(InlineKeyboardButton("Готово!", callback_data="end_selected_cities"))
    await query.message.edit_text(
        text=f"Обрані області: {', '.join(selected_regions)}\n\nОбрані міста: {', '.join(selected_cities)}",
        reply_markup=keyboard)


@dp.callback_query_handler(lambda query: query.data == "end_selected_cities")
async def finish_selection_cities(query: types.CallbackQuery):
    user_id = query.from_user.id
    user_state = user_states[user_id]
    selected_cities = []
    locations = {}
    for region in user_state.selected_cites.keys():
        if region in user_state.selected_regions:
            locations[region] = user_state.selected_cites[region]
            selected_cities.extend(user_state.selected_cites[region])
    await add_location(locations, user_id=user_id)
    user = User.objects(user_id=user_id).first()
    if user:
        user_info = f"{user.name}\n"

        selected_cities = ', '.join(selected_cities)

        message_text = f"{user_info}{selected_cities}"
        await query.message.edit_text(text=message_text)

    else:
        await query.message.edit_text(text="Користувача не знайдено в базі даних.")



if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)

