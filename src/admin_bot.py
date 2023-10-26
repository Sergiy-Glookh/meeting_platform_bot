from datetime import datetime as dt
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types
from connect import TOKEN, collection, GROUP_ID
from api import get_info
import datetime
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.dispatcher import FSMContext
from button import *

waiting_for_street = State()
previous_states = {}
current_datetime = dt.now()
storage = MemoryStorage()
bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=storage)
user_states = {}
waiting_for_description = State()


@dp.callback_query_handler(lambda c: c.data == 'back',
                           state=['waiting_for_month', 'waiting_for_day', 'waiting_for_hour', 'waiting_for_minute',
                                  'waiting_for_year'])
async def process_back_button(callback_query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'waiting_for_minute':
        await state.set_state('waiting_for_hour')
        await bot.send_message(callback_query.message.chat.id, '🕛Виберіть годину:', reply_markup=hour_keyboard)
    elif current_state == 'waiting_for_hour':
        await state.set_state('waiting_for_day')
        await bot.send_message(callback_query.message.chat.id, '🌝Виберіть день:', reply_markup=day_keyboard)
    elif current_state == 'waiting_for_day':
        await state.set_state('waiting_for_month')
        await bot.send_message(callback_query.message.chat.id, '🌝Виберіть місяць:', reply_markup=month_keyboard)
    elif current_state == 'waiting_for_month':
        await state.set_state('waiting_for_year')
        await bot.send_message(callback_query.message.chat.id, '🌍Виберіть рік:', reply_markup=year_keyboard)
    elif current_state == 'waiting_for_year':

        user_id = callback_query.from_user.id
        if user_id in previous_states:
            previous_state = previous_states[user_id]
            await state.set_state(previous_state['state'])
            await state.update_data(previous_state['data'])

            await bot.send_message(callback_query.message.chat.id, previous_state['text'],
                                   reply_markup=previous_state['keyboard'])
        else:
            await state.set_state('waiting_for_selected_town')
            await bot.send_message(callback_query.message.chat.id, '🗺️Введи назву населеного пункту де буде зустріч:')
    else:
        await state.set_state('waiting_for_selected_town')
        await bot.send_message(callback_query.message.chat.id, '🗺️Введи назву населеного пункту де буде зустріч:')


@dp.message_handler(commands=['start'])
async def start_def(message: types.Message):
    await message.answer('Привіт, що хочеш зробити?🤔', reply_markup=kb_client)


@dp.callback_query_handler(lambda c: c.data == 'view_meetings')
async def view_active_meetings(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    active_meetings = collection.find({"user_id": user_id})

    if active_meetings:
        response = "🍻Ваші активні зустрічі:\n"
        for meeting in active_meetings:
            city = meeting['city']
            region = meeting['region']
            datetime = meeting['datetime']
            response += f"🥂Зустріч у місті {city}, {region} Дата: {datetime}\n"
    else:
        response = "😢Наразі у вас немає активних зустрічей."

    await bot.send_message(user_id, response)


@dp.callback_query_handler(lambda c: c.data == 'create_meeting', state='*')
async def start_create_meeting(callback_query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    user_id = callback_query.from_user.id
    if user_id not in user_states:
        user_states[user_id] = []
    user_states[user_id].append(current_state)

    keyboard_with_back = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️Назад', callback_data='back'))

    await bot.send_message(callback_query.message.chat.id, '📝Вкажіть назву для Вашої зустрічі:',
                           reply_markup=keyboard_with_back)
    await state.set_state('waiting_for_meeting_name')


@dp.message_handler(lambda message: len(message.text) >= 2, state='waiting_for_meeting_name')
async def process_meeting_name_input(message: types.Message, state: FSMContext):
    meeting_name = message.text

    async with state.proxy() as data:
        data['meeting_name'] = meeting_name

    keyboard_back = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️Назад', callback_data='back_to_meeting_name'))

    await message.answer('✅ Ви успішно ввели назву зустрічі. Тепер вкажіть опис зустрічі:', reply_markup=keyboard_back)
    await state.set_state('waiting_for_description')


@dp.callback_query_handler(lambda c: c.data == 'back_to_meeting_name', state='waiting_for_description')
async def process_back_button_to_meeting_name(callback_query: CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.message.chat.id, '📝Вкажіть назву для Вашої зустрічі:',
                           reply_markup=keyboard_with_back)
    await state.set_state('waiting_for_meeting_name')


@dp.callback_query_handler(lambda c: c.data == 'back', state=['waiting_for_meeting_name', 'waiting_for_description'])
async def process_back_button_to_previous_state(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id in previous_states:
        previous_state = previous_states[user_id]
        await bot.send_message(callback_query.message.chat.id, previous_state['text'],
                               reply_markup=previous_state['keyboard'])
        await state.set_state(previous_state['state'])

        del previous_states[user_id]
    else:
        await bot.send_message(callback_query.message.chat.id, '🤔 Виберіть опцію:', reply_markup=kb_client)
        await state.finish()


@dp.message_handler(lambda message: len(message.text) >= 5, state='waiting_for_description')
async def process_description_input(message: types.Message, state: FSMContext):
    description = message.text

    async with state.proxy() as data:
        data['description'] = description

        data['previous_message'] = message
        data['previous_keyboard'] = message.reply_markup

    keyboard_back = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️Назад', callback_data='back_to_description'))

    await message.answer(
        '✅ Ви успішно ввели опис зустрічі. Тепер вкажіть назву населеного пункту (міста), де буде зустріч:',
        reply_markup=keyboard_back)
    await state.set_state('waiting_for_town')


@dp.callback_query_handler(lambda c: c.data == 'back_to_description', state='waiting_for_town')
async def process_back_to_description_button(callback_query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        previous_message = data.get('previous_message')
        previous_keyboard = data.get('previous_keyboard')
        if previous_message:
            await bot.send_message(callback_query.message.chat.id, previous_message.text,
                                   reply_markup=previous_keyboard)

    await state.set_state('waiting_for_description')


@dp.message_handler(state='waiting_for_town')
async def process_town_input(message: types.Message, state: FSMContext):
    selected_town = message.text

    async with state.proxy() as data:
        data['selected_town'] = selected_town
        info = get_info(selected_town)

    if info:
        await state.update_data(info=info)
        towns_info = generate_towns_keyboard(info)
        await message.answer("🔍Виберіть населений пункт:", reply_markup=towns_info)
        await state.set_state('waiting_for_selected_town')

        previous_states[message.from_user.id] = {
            'state': 'waiting_for_selected_town',
            'text': '🔍Виберіть населений пункт:',
            'keyboard': towns_info,
            'data': data,
        }
    else:
        await message.answer("Назва населеного пункту некоректна😢. Введіть іншу назву:")


@dp.callback_query_handler(lambda c: c.data == 'back',
                           state=['waiting_for_selected_town', 'waiting_for_selected_street'])
async def process_back_button(callback_query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'waiting_for_selected_street':
        await state.set_state('waiting_for_selected_town')
    else:
        await state.set_state('waiting_for_town')

    await bot.send_message(callback_query.message.chat.id, '🗺️Введи назву населеного пункту де буде зустріч:')


@dp.callback_query_handler(lambda c: c.data.startswith('town_'), state='waiting_for_selected_town')
async def process_selected_town(callback_query: CallbackQuery, state: FSMContext):
    selected_town = callback_query.data.split('_')[1]

    await state.update_data(selected_city=selected_town)

    town_info = get_info(selected_town)

    if town_info:

        city, region = town_info[0].split('(')

        city = city.strip()
        region = region.rstrip(')').strip()

        await state.update_data(selected_region=region)

        location_info = f'✅Ви обрали "{city}" ({region} обл.)'

        years_keyboard = year_keyboard
        await bot.send_message(callback_query.message.chat.id, f'{location_info}\n\n🌍Виберіть рік:',
                               reply_markup=years_keyboard)
        await state.set_state('waiting_for_year')
    else:
        await bot.send_message(callback_query.message.chat.id,
                               "Не вдалося знайти інформацію про це місто. Спробуйте ще раз.")


@dp.callback_query_handler(lambda c: c.data.startswith('select_year:'), state='waiting_for_year')
async def process_year_input(callback_query: CallbackQuery, state: FSMContext):
    selected_year = callback_query.data.split(':')[1]
    selected_year = int(selected_year)

    await bot.send_message(callback_query.message.chat.id, '🌝Виберіть місяць:', reply_markup=month_keyboard)
    await state.update_data(year=selected_year)
    await state.set_state('waiting_for_month')


@dp.callback_query_handler(lambda c: c.data.startswith('select_month:'), state='waiting_for_month')
async def process_month_input(callback_query: CallbackQuery, state: FSMContext):
    selected_month = callback_query.data.split(':')[1]
    selected_month = int(selected_month)

    current_datetime = datetime.datetime.now()

    async with state.proxy() as data:
        selected_year = data["year"]

    if (selected_year < current_datetime.year) or (
            selected_year == current_datetime.year and selected_month < current_datetime.month):
        await bot.send_message(callback_query.message.chat.id,
                               "Ви не можете вибрати місяць в минулому. Виберіть інший місяць.")
    else:
        await bot.send_message(callback_query.message.chat.id, '🌝Виберіть день:', reply_markup=day_keyboard)
        await state.update_data(month=selected_month)
        await state.set_state('waiting_for_day')


@dp.callback_query_handler(lambda c: c.data.startswith('select_day:'), state='waiting_for_day')
async def process_day_input(callback_query: CallbackQuery, state: FSMContext):
    selected_day = callback_query.data.split(':')[1]
    selected_day = int(selected_day)

    current_datetime = datetime.datetime.now()

    async with state.proxy() as data:
        selected_year = data["year"]
        selected_month = data["month"]

    if (selected_year < current_datetime.year) or \
            (selected_year == current_datetime.year and selected_month < current_datetime.month) or \
            (
                    selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day < current_datetime.day):
        await bot.send_message(callback_query.message.chat.id,
                               "Ви не можете вибрати день в минулому. Виберіть інший день.")
    else:
        await bot.send_message(callback_query.message.chat.id, '🕛Виберіть годину:', reply_markup=hour_keyboard)
        await state.update_data(day=selected_day)
        await state.set_state('waiting_for_hour')


@dp.callback_query_handler(lambda c: c.data.startswith('select_hour:'), state='waiting_for_hour')
async def process_hour_input(callback_query: CallbackQuery, state: FSMContext):
    selected_hour = callback_query.data.split(':')[1]
    selected_hour = int(selected_hour)

    current_datetime = datetime.datetime.now()

    async with state.proxy() as data:
        selected_year = data["year"]
        selected_month = data["month"]
        selected_day = data["day"]

    if (selected_year < current_datetime.year) or \
            (selected_year == current_datetime.year and selected_month < current_datetime.month) or \
            (
                    selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day < current_datetime.day) or \
            (
                    selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day == current_datetime.day and selected_hour < current_datetime.hour):
        await bot.send_message(callback_query.message.chat.id,
                               "Ви не можете вибрати годину в минулому. Виберіть іншу годину.")
    else:
        await bot.send_message(callback_query.message.chat.id, '⏱️Виберіть хвилину:', reply_markup=minute_keyboard)
        await state.update_data(hour=selected_hour)
        await state.set_state('waiting_for_minute')


@dp.callback_query_handler(lambda c: c.data.startswith('select_minute:'), state='waiting_for_minute')
async def process_minute_input(callback_query: CallbackQuery, state: FSMContext):
    selected_minute = callback_query.data.split(':')[1]
    selected_minute = int(selected_minute)

    current_datetime = datetime.datetime.now()

    async with state.proxy() as data:
        selected_year = data["year"]
        selected_month = data["month"]
        selected_day = data["day"]
        selected_hour = data["hour"]

    if (selected_year < current_datetime.year) or \
            (selected_year == current_datetime.year and selected_month < current_datetime.month) or \
            (
                    selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day < current_datetime.day) or \
            (
                    selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day == current_datetime.day and selected_hour < current_datetime.hour) or \
            (
                    selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day == current_datetime.day and selected_hour == current_datetime.hour and selected_minute < current_datetime.minute):
        await bot.send_message(callback_query.message.chat.id,
                               "Ви не можете вибрати хвилину в минулому. Виберіть іншу хвилину.")
    else:
        async with state.proxy() as data:
            user_id = callback_query.from_user.id
            description = data["description"]
            meeting_name = data["meeting_name"]
            selected_city = data["selected_city"]
            selected_year = data["year"]
            selected_month = data["month"]
            selected_day = data["day"]
            selected_hour = data["hour"]
            selected_region = data["selected_region"]

        date_time = datetime.datetime(selected_year, selected_month, selected_day, selected_hour, selected_minute)
        formatted_date_time = date_time.strftime('%Y-%m-%d' ' о ' '%H:%M' ' годині')

        user_data = {

            "user_id": user_id,
            "city": selected_city,
            "region": f"{selected_region} обл.",
            "datetime": formatted_date_time,
            "timestamp": datetime.datetime.now(),
            "meeting_name": meeting_name,
            "description": description
        }
        collection.insert_one(user_data)

        response = (
            f"✅Ваша зустріч {meeting_name} відбудеться у місті {selected_city}, {selected_region} обл. "
            f"Дата: {formatted_date_time}"
        )
        await bot.send_message(callback_query.message.chat.id, response)

        join_button = InlineKeyboardButton("✅Приєднатися", callback_data=str(user_id))
        keyboard = InlineKeyboardMarkup()
        keyboard.add(join_button)

        post_message = f"Нова зустріч: {meeting_name} відбудеться {formatted_date_time} у місті {selected_city}, {selected_region} обл."
        await bot.send_message(GROUP_ID, post_message, reply_markup=keyboard)

        await state.finish()


@dp.callback_query_handler(lambda callback_query: True)
async def join_meeting(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    doc = {
        "add_user": user_id
    }
    collection.insert_one(doc)
    await bot.answer_callback_query(callback_query.id, text="Ви приєднались до зустрічі!")


if __name__ == "__main__":
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
