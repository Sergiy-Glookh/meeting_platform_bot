
import datetime
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types
from button import *
from connect import TOKEN, collection, GROUP_ID
from api import get_info
from gpt import main
storage = MemoryStorage()
cities = {}
bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=storage)
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.dispatcher import FSMContext


class LocationForm(StatesGroup):
    waiting_for_description = State()
    waiting_for_town = State()
    waiting_for_street = State()
    waiting_for_selected_town = State()
    waiting_for_selected_street = State()
    waiting_for_year = State()
    waiting_for_month = State()
    waiting_for_day = State()
    waiting_for_hour = State()
    last_location = State()

def generate_towns_keyboard(info):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)

    for item in info:
        if ' (' in item:
            town, region = item.split(' (')
            region = region.rstrip(')')
            region = f"{region}.обл"
            button_text = f"{town} ({region})"
            keyboard.add(button_text)

    return keyboard


@dp.message_handler(commands=['start'])
async def start_def(message: types.Message):
    await message.answer('Привіт, що хочеш зробити?🤔', reply_markup=kb_client)

# Обробник натискання на кнопку "Активні зустрічі"
@dp.message_handler(text=['Переглянути активні зустрічі👀'])
async def active_meetings(message: types.Message):
    user_id = message.from_user.id

    # Отримати активні зустрічі користувача з бази даних
    active_meetings = collection.find({"user_id": user_id})

    if active_meetings:
        response = "🍻Ваші активні зустрічі:\n"
        for meeting in active_meetings:
            response += f"🥂Зустріч у місті {meeting['city']}, Дата: {meeting['datetime']}\n"
    else:
        response = "😢Наразі у вас немає активних зустрічей."

    await message.answer(response)





# Обробник натискання на кнопку "Створити зустріч"
@dp.message_handler(text=['Створити зустріч'])
async def start_create_meeting(message: types.Message, state: FSMContext):
    await message.answer('🗺️Введи назву населеного пункту де буде зустріч:')
    await state.set_state('waiting_for_town')  # Встановлюємо стан для очікування назви населеного пункту


# Обробник введення назви міста
@dp.message_handler(state='waiting_for_town')
async def process_town_input(message: types.Message, state: FSMContext):
    selected_town = message.text

    async with state.proxy() as data:
        data['selected_town'] = selected_town
        info = get_info(selected_town)  # Отримати інформацію про населені пункти

    if info:
        await state.update_data(info=info)
        towns_info = generate_towns_keyboard(info)
        await message.answer("🔍Виберіть населений пункт:", reply_markup=towns_info)
        await state.set_state('waiting_for_selected_town')
    else:
        await message.answer("Назва населеного пункту некоректна😢. Введіть іншу назву:")



@dp.message_handler(lambda message: message.text, state='waiting_for_selected_town')
async def cmd_choose_city(message: types.Message, state: FSMContext):
    selected_city = message.text

    async with state.proxy() as data:
        selected_region = data.get('selected_region')

    location_info = f'✅Ви обрали "{selected_city}""'

    # Зберігаємо обраний населений пункт та місто у стані
    async with state.proxy() as data:
        data['selected_city'] = selected_city
        data['selected_region'] = selected_region

    # Тепер можна створити клавіатуру з вибором року і відправити користувачу
    years_keyboard = generate_years_keyboard()  # Викликаємо функцію для створення клавіатури
    await message.answer(f'{location_info}\n\n🌍Виберіть рік:', reply_markup=years_keyboard)
    await state.set_state('waiting_for_year')






# Обробник вибору року
@dp.message_handler(lambda message: message.text.isdigit(), state='waiting_for_year')
async def process_year_input(message: types.Message, state: FSMContext):
    selected_year = int(message.text)
    await message.answer('🌙Виберіть місяць:', reply_markup=month_keyboard)
    await state.update_data(year=selected_year)  # Зберігаємо обраний рік у стані
    await state.set_state('waiting_for_month')  # Встановлюємо стан для очікування місяця


# Обробник вибору місяця
@dp.message_handler(lambda message: message.text.isdigit(), state='waiting_for_month')
async def process_month_input(message: types.Message, state: FSMContext):
    selected_month = int(message.text)

    # Отримайте поточну дату і час
    current_datetime = datetime.datetime.now()

    # Отримайте дані зі стану
    async with state.proxy() as data:
        selected_year = data["year"]

    # Перевірка, чи введений місяць є в майбутньому порівняно з поточним місяцем і роком
    if (selected_year < current_datetime.year) or (selected_year == current_datetime.year and selected_month < current_datetime.month):
        await message.answer("Ви не можете вибрати місяць в минулому. Виберіть інший місяць.")
    else:
        await message.answer('🌝Виберіть день:', reply_markup=day_keyboard)
        await state.update_data(month=selected_month)  # Зберігаємо обраний місяць у стані
        await state.set_state('waiting_for_day')  # Встановлюємо стан для очікування дня


# Обробник вибору дня
@dp.message_handler(lambda message: message.text.isdigit(), state='waiting_for_day')
async def process_day_input(message: types.Message, state: FSMContext):
    selected_day = int(message.text)

    # Отримайте поточну дату і час
    current_datetime = datetime.datetime.now()

    # Отримайте дані зі стану
    async with state.proxy() as data:
        selected_year = data["year"]
        selected_month = data["month"]

    # Перевірка, чи введений день є в майбутньому порівняно з поточним роком, місяцем і днем
    if (selected_year < current_datetime.year) or \
       (selected_year == current_datetime.year and selected_month < current_datetime.month) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day < current_datetime.day):
        await message.answer("Ви не можете вибрати день в минулому. Виберіть інший день.")
    else:
        await message.answer('🕛Виберіть годину:', reply_markup=hour_keyboard)
        await state.update_data(day=selected_day)  # Зберігаємо обраний день у стані
        await state.set_state('waiting_for_hour')  # Встановлюємо стан для очікування години


# Обробник вибору години
@dp.message_handler(lambda message: message.text.isdigit(), state='waiting_for_hour')
async def process_hour_input(message: types.Message, state: FSMContext):
    selected_hour = int(message.text)

    # Отримайте поточну дату і час
    current_datetime = datetime.datetime.now()

    # Отримайте дані зі стану
    async with state.proxy() as data:
        selected_year = data["year"]
        selected_month = data["month"]
        selected_day = data["day"]

    # Перевірка, чи введена година є в майбутньому порівняно з поточним часом
    if (selected_year < current_datetime.year) or \
       (selected_year == current_datetime.year and selected_month < current_datetime.month) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day < current_datetime.day) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day == current_datetime.day and selected_hour < current_datetime.hour):
        await message.answer("Ви не можете вибрати годину в минулому. Виберіть іншу годину.")
    else:
        await message.answer('⏱️Виберіть хвилину:', reply_markup=minute_keyboard)
        await state.update_data(hour=selected_hour)  # Зберігаємо обрану годину у стані
        await state.set_state('waiting_for_minute')  # Встановлюємо стан для очікування хвилини


# Обробник вибору хвилини
@dp.message_handler(lambda message: message.text.isdigit(), state='waiting_for_minute')
async def process_minute_input(message: types.Message, state: FSMContext):
    selected_minute = int(message.text)

    # Отримайте поточну дату і час
    current_datetime = datetime.datetime.now()

    # Отримайте дані зі стану
    async with state.proxy() as data:
        selected_year = data["year"]
        selected_month = data["month"]
        selected_day = data["day"]
        selected_hour = data["hour"]

    # Перевірка, чи введена хвилина є в майбутньому порівняно з поточним часом
    if (selected_year < current_datetime.year) or \
       (selected_year == current_datetime.year and selected_month < current_datetime.month) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day < current_datetime.day) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day == current_datetime.day and selected_hour < current_datetime.hour) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day == current_datetime.day and selected_hour == current_datetime.hour and selected_minute < current_datetime.minute):
        await message.answer("Ви не можете вибрати хвилину в минулому. Виберіть іншу хвилину.")
    else:
        async with state.proxy() as data:
            user_id = message.from_user.id
            selected_city = data["selected_city"]
            selected_year = data["year"]
            selected_month = data["month"]
            selected_day = data["day"]
            selected_hour = data["hour"]

        # Збереження інформації про дату та час
        date_time = datetime.datetime(selected_year, selected_month, selected_day, selected_hour, selected_minute)
        formatted_date_time = date_time.strftime('%Y-%m-%d о %H:%M годині')

        # Збереження всієї інформації в базу даних
        user_data = {
            "user_id": user_id,
            "city": selected_city,
            "datetime": formatted_date_time,
            "timestamp": datetime.datetime.now()
        }
        collection.insert_one(user_data)

        # Вивід інформації про зустріч
        response = (
            f"✅Ваша зустріч відбудеться у місті {selected_city}, "
            f" Дата: {formatted_date_time}"
        )
        await message.answer(response)

        # Створення кнопки для додавання ідентифікатора користувача в базу даних
        join_button = types.InlineKeyboardButton("✅Приєднатися", callback_data=user_id)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(join_button)

        # Опублікувати повідомлення у групі з кнопкою
        post_message = f"Нова зустріч: {formatted_date_time} у {selected_city}"
        await bot.send_message(GROUP_ID, post_message, reply_markup=keyboard)

        await state.finish()
        await message.answer('Зустріч створено, вітаю🥳',
                             reply_markup=kb_client)
        await state.finish()


# Обробник натискання на кнопку "Приєднатися"
@dp.callback_query_handler(lambda callback_query: True)
async def join_meeting(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id


    doc = {
        "add_user": user_id
    }
    collection.insert_one(doc)
    await bot.answer_callback_query(callback_query.id, text="Ви приєднались до зустрічі!")



async def on_startup(_):
    print('Бот запущено')



if __name__ == "__main__":
    from aiogram import executor

    executor.start_polling(dp, on_startup=on_startup)
