import datetime
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types
from bson import ObjectId
from connect import *
from api import get_info
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.dispatcher import FSMContext
from button import *
waiting_for_street = State()
previous_states = {}
previous_keyboard = None
storage = MemoryStorage()
bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=storage)
user_states = {}
waiting_for_description = State()
current_datetime = datetime.datetime.now()
from datetime import datetime
previous_keyboard = None
from get_street_ref import *
@dp.callback_query_handler(lambda c: c.data == 'back', state=['waiting_for_month', 'waiting_for_day', 'waiting_for_hour', 'waiting_for_minute', 'waiting_for_year'])
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

            await bot.send_message(callback_query.message.chat.id, previous_state['text'], reply_markup=previous_state['keyboard'])
        else:
            await state.set_state('waiting_for_selected_town')
            await bot.send_message(callback_query.message.chat.id, '🗺️Введи назву населеного пункту де буде зустріч:')
    else:
        await state.set_state('waiting_for_selected_town')
        await bot.send_message(callback_query.message.chat.id, '🗺️Введи назву населеного пункту де буде зустріч:')





@dp.message_handler(commands=['start'])
async def start_def(message: types.Message):
    await message.answer('Привіт, що хочеш зробити?🤔', reply_markup=kb_client)

@dp.callback_query_handler(lambda c: c.data.startswith('view_meeting:'))
async def view_meeting_details(callback_query: CallbackQuery):

    meeting_id = callback_query.data.split(':')[1]
    user_id = callback_query.from_user.id


    meeting = collection.find_one({"_id": ObjectId(meeting_id)})

    if meeting:
        meeting_name = meeting['meeting_name']
        city = meeting['city']
        region = meeting['region']
        datetime = meeting['datetime']

        response = f"Деталі про зустріч '{meeting_name}':\n"
        response += f"📅 Дата та час: {datetime}\n"
        response += f"🌍 Місто: {city}, {region}"


        keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️ Назад', callback_data='view_meetings'))


        await bot.send_message(user_id, response, reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")



@dp.callback_query_handler(lambda c: c.data == 'view_meetings')
async def view_active_meetings(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    active_meetings = collection.find({"user_id": user_id})

    if active_meetings:
        response = "🍻Ваші активні зустрічі:\n"
        keyboard = InlineKeyboardMarkup(row_width=3)
        for meeting in active_meetings:
            meeting_name = meeting['meeting_name']
            city = meeting['city']
            region = meeting['region']
            datetime = meeting['datetime']
            meeting_id = str(meeting['_id'])

            text = f"🥂{meeting_name}\n📅{datetime}\n🌍{city}, {region}"
            keyboard.add(InlineKeyboardButton(text, callback_data=f'view_meeting:{meeting_id}'))

            button_row = [
                InlineKeyboardButton(f"🖊️ Редагувати {meeting_name}", callback_data=f'edit_meeting:{meeting_id}'),
                InlineKeyboardButton(f"❌ Скасувати {meeting_name}", callback_data=f'cancel_meeting:{meeting_id}'),
                InlineKeyboardButton(f"🔍 Детальніше", callback_data=f'details_meeting:{meeting_id}')
            ]
            keyboard.add(*button_row)

        keyboard.add(InlineKeyboardButton('↩️ Назад', callback_data='back_to_menu'))
    else:
        response = "😢Наразі у вас немає активних зустрічей."
        keyboard = kb_client

    await bot.send_message(user_id, response, reply_markup=keyboard)







@dp.callback_query_handler(lambda c: c.data == 'back_to_menu')
async def back_to_main_menu(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.send_message(user_id, '🤔Обери опцію.', reply_markup=kb_client)


@dp.callback_query_handler(lambda c: c.data.startswith('details_meeting:'))
async def view_meeting_details(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    meeting = collection.find_one({"_id": ObjectId(meeting_id)})

    if meeting:
        meeting_name = meeting['meeting_name']
        description = meeting['description']
        city = meeting['city']
        region = meeting['region']
        datetime = meeting['datetime']

        response = f"🥂 Назва зустрічі: {meeting_name}\n" \
                   f"📝 Опис: {description}\n" \
                   f"📅 Дата та час: {datetime}\n" \
                   f"🌍 Локація: {city}, {region}"


        keyboard = InlineKeyboardMarkup(row_width=1)


        keyboard.add(InlineKeyboardButton(f"👀 Хто приєднався", callback_data=f'joined_meeting:{meeting_id}'))
        keyboard.add(InlineKeyboardButton(f"🖊️ Редагувати {meeting_name}", callback_data=f'edit_meeting:{meeting_id}'))
        keyboard.add(InlineKeyboardButton(f"❌ Скасувати {meeting_name}", callback_data=f'cancel_meeting:{meeting_id}'))
        keyboard.add(InlineKeyboardButton('↩️ Назад до зустрічей', callback_data='view_meetings'))

        await bot.send_message(user_id, response, reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")

@dp.callback_query_handler(lambda c: c.data.startswith('joined_meeting:'))
async def view_joined_users(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]


    meeting = collection.find_one({"_id": ObjectId(meeting_id)})

    if meeting:

        joined_users = joined.find({"add_user.meeting_id": str(meeting['_id'])})

        user_list = []
        for user in joined_users:
            user_list.append(user['add_user']['user_username'])

        if user_list:
            response = "👥 Користувачі, що приєдналися до зустрічі:\n"
            response += "\n".join([f"- {username}" for username in user_list])

            await bot.send_message(user_id, response)
        else:
            await bot.send_message(user_id, "На жаль, ніхто ще не приєднався до цієї зустрічі.")
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")














@dp.callback_query_handler(lambda c: c.data.startswith('edit_meeting:'))
async def edit_meeting(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]


    meeting = collection.find_one({"_id": ObjectId(meeting_id)})

    if meeting:

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🖊️ Редагувати назву", callback_data=f'edit_name:{meeting_id}'))
        keyboard.add(InlineKeyboardButton("📝 Редагувати опис", callback_data=f'edit_description:{meeting_id}'))
        keyboard.add(InlineKeyboardButton("📅 Редагувати дату", callback_data=f'edit_date:{meeting_id}'))
        keyboard.add(InlineKeyboardButton("🌍 Редагувати локацію", callback_data=f'edit_location:{meeting_id}'))
        keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back'))  # Змініть callback_data на 'back'


        response = "Виберіть параметр, який ви хочете редагувати."
        await bot.send_message(user_id, response, reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")



@dp.callback_query_handler(lambda c: c.data == 'back')
async def back_to_meetings_menu(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    active_meetings = collection.find({"user_id": user_id})

    if active_meetings:
        response = "🍻Ваші активні зустрічі:\n"
        keyboard = InlineKeyboardMarkup(row_width=3)
        for meeting in active_meetings:
            meeting_name = meeting['meeting_name']
            city = meeting['city']
            region = meeting['region']
            datetime = meeting['datetime']
            meeting_id = str(meeting['_id'])

            text = f"🥂{meeting_name}\n📅{datetime}\n🌍{city}, {region}"
            keyboard.add(InlineKeyboardButton(text, callback_data=f'view_meeting:{meeting_id}'))

            button_row = [
                InlineKeyboardButton(f"🖊️ Редагувати {meeting_name}", callback_data=f'edit_meeting:{meeting_id}'),
                InlineKeyboardButton(f"❌ Скасувати {meeting_name}", callback_data=f'cancel_meeting:{meeting_id}'),
                InlineKeyboardButton(f"🔍 Детальніше", callback_data=f'details_meeting:{meeting_id}')
            ]
            keyboard.add(*button_row)

        keyboard.add(InlineKeyboardButton('↩️ Назад', callback_data='back_to_menu'))
    else:
        response = "😢Наразі у вас немає активних зустрічей."
        keyboard = kb_client

    await bot.send_message(user_id, response, reply_markup=keyboard)



@dp.callback_query_handler(lambda c: c.data.startswith('edit_name:'))
async def edit_meeting_name(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]


    meeting = collection.find_one({"_id": ObjectId(meeting_id)})

    if meeting:
        response = "Введіть нову назву для зустрічі:"


        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back'))

        await bot.send_message(user_id, response, reply_markup=keyboard)

        @dp.message_handler(lambda message: message.from_user.id == user_id)
        async def process_new_meeting_name(message: types.Message):
            new_meeting_name = message.text


            collection.update_one({"_id": ObjectId(meeting_id)}, {"$set": {"meeting_name": new_meeting_name}})

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🖊️ Редагувати назву", callback_data=f'edit_name:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("📝 Редагувати опис", callback_data=f'edit_description:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("📅 Редагувати дату", callback_data=f'edit_date:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("🌍 Редагувати локацію", callback_data=f'edit_location:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back'))


            await bot.send_message(user_id, f"Назву зустрічі '{new_meeting_name}' змінено. Що бажаєте редагувати далі?",
                                   reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")

@dp.callback_query_handler(lambda c: c.data.startswith('edit_description:'))
async def edit_meeting_description(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    meeting = collection.find_one({"_id": ObjectId(meeting_id)})

    if meeting:
        response = "Введіть новий опис для зустрічі:"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back'))

        await bot.send_message(user_id, response, reply_markup=keyboard)

        @dp.message_handler(lambda message: message.from_user.id == user_id)
        async def process_new_meeting_description(message: types.Message):
            new_description = message.text

            collection.update_one({"_id": ObjectId(meeting_id)}, {"$set": {"description": new_description}})

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🖊️ Редагувати назву", callback_data=f'edit_name:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("📝 Редагувати опис", callback_data=f'edit_description:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("📅 Редагувати дату", callback_data=f'edit_date:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("🌍 Редагувати локацію", callback_data=f'edit_location:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back'))

            await bot.send_message(user_id, f"Опис зустрічі змінено на '{new_description}'. Що бажаєте редагувати далі?",
                                   reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")









@dp.callback_query_handler(lambda c: c.data.startswith('edit_month:'))
async def edit_month(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    meeting = collection.find_one({"_id": ObjectId(meeting_id)})
    current_month = meeting.get('month') if meeting else 'не визначено'

    await bot.send_message(user_id, f"Поточний місяць для проведення зустрічі: {current_month}. Виберіть новий місяць:", reply_markup=month_keyboard)

    user_states[user_id] = {'action': 'edit_month', 'meeting_id': meeting_id}

@dp.callback_query_handler(lambda c: c.data.startswith('select_month:'))
async def select_month(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    selected_month = callback_query.data.split(":")[1]
    meeting_id = user_states[user_id]['meeting_id']


    collection.update_one({"_id": ObjectId(meeting_id)}, {"$set": {"month": int(selected_month)}})


    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📅 Редагувати рік", callback_data=f'edit_year:{meeting_id}'),
        InlineKeyboardButton("📅 Редагувати місяць", callback_data=f'edit_month:{meeting_id}'),
    )
    keyboard.add(
        InlineKeyboardButton("📅 Редагувати день", callback_data=f'edit_day:{meeting_id}'),
        InlineKeyboardButton("📅 Редагувати годину", callback_data=f'edit_hour:{meeting_id}'),
    )
    keyboard.add(
        InlineKeyboardButton("📅 Редагувати хвилину", callback_data=f'edit_minute:{meeting_id}'),
        InlineKeyboardButton("↩️ Назад", callback_data='back_date_edit')
    )


    await bot.send_message(user_id, f"Місяць змінено на {selected_month}", reply_markup=keyboard)





@dp.callback_query_handler(lambda c: c.data.startswith('select_month:'))
async def select_month(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    selected_month = callback_query.data.split(":")[1]
    meeting_id = callback_query.data.split(":")[2]


    collection.update_one({"_id": ObjectId(meeting_id)}, {"$set": {"month": int(selected_month)}})

    await bot.send_message(user_id, f"Місяць змінено на {selected_month}")

async def create_back_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back_to_meetings'))
    return keyboard

from aiogram import types

@dp.callback_query_handler(lambda c: c.data.startswith('cancel_meeting:'))
async def cancel_meeting(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]


    meeting = collection.find_one({"_id": ObjectId(meeting_id)})

    if meeting:

        canceled_meeting_data = {
            "user_id": meeting["user_id"],
            "meeting_name": meeting["meeting_name"],
            "city": meeting["city"],
            "region": meeting["region"],
            "datetime": meeting["datetime"],
            "cancelled_at": datetime.now(),
        }
        canceled_meetings.insert_one(canceled_meeting_data)


        collection.delete_one({"_id": ObjectId(meeting_id)})


        group_id = GROUP_ID
        if group_id:
            cancellation_message = (
                f"Зустріч '{meeting['meeting_name']}' була скасована. "
                f"Дата та час проведення було заплановано на: {meeting['datetime']}, Місце: {meeting['city']}, {meeting['region']}"
            )
            await bot.send_message(group_id, cancellation_message)


        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back_to_meetings'))

        await bot.send_message(user_id, "Зустріч була скасована.", reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")


@dp.callback_query_handler(lambda c: c.data == 'back_to_meetings')
async def back_to_meetings(callback_query: CallbackQuery):
    await view_active_meetings(callback_query)



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




@dp.message_handler(lambda message: len(message.text), state='waiting_for_meeting_name')
async def process_meeting_name_input(message: types.Message, state: FSMContext):
    meeting_name = message.text

    async with state.proxy() as data:
        data['meeting_name'] = meeting_name

    keyboard_back = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️Назад', callback_data='back_to_meeting_name'))

    await message.answer('✅ Ви успішно ввели назву зустрічі. Тепер вкажіть опис зустрічі:', reply_markup=keyboard_back)
    await state.set_state('waiting_for_description')

@dp.callback_query_handler(lambda c: c.data == 'back_to_meeting_name', state='waiting_for_description')
async def process_back_button_to_meeting_name(callback_query: CallbackQuery, state: FSMContext):
    keyboard_with_back = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️Назад', callback_data='back'))
    await bot.send_message(callback_query.message.chat.id, '📝Вкажіть назву для Вашої зустрічі:', reply_markup=keyboard_with_back)
    await state.set_state('waiting_for_meeting_name')

@dp.callback_query_handler(lambda c: c.data == 'back', state=['waiting_for_meeting_name', 'waiting_for_description'])
async def process_back_button_to_previous_state(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    if user_id in previous_states:
        previous_state = previous_states[user_id]
        await bot.send_message(callback_query.message.chat.id, previous_state['text'], reply_markup=previous_state['keyboard'])
        await state.set_state(previous_state['state'])

        del previous_states[user_id]
    else:
        await bot.send_message(callback_query.message.chat.id, '🤔 Виберіть опцію:', reply_markup=kb_client)
        await state.finish()

@dp.message_handler(lambda message: len(message.text), state='waiting_for_description')
async def process_description_input(message: types.Message, state: FSMContext):
    description = message.text

    async with state.proxy() as data:
        data['description'] = description
        data['previous_state'] = 'waiting_for_description'

    keyboard_back = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️Назад', callback_data='back_to_description'))
    await message.answer('✅ Ви успішно ввели опис зустрічі. Тепер вкажіть назву населеного пункту (міста), де буде зустріч:', reply_markup=keyboard_back)
    await state.set_state('waiting_for_town')
@dp.callback_query_handler(lambda c: c.data == 'back_to_description', state='waiting_for_town')
async def process_back_to_description_button(callback_query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        previous_message = data.get('previous_message')
        previous_keyboard = data.get('previous_keyboard')
        if previous_message:
            await bot.send_message(callback_query.message.chat.id, previous_message.text, reply_markup=previous_keyboard)
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

@dp.callback_query_handler(lambda c: c.data == 'back', state=['waiting_for_selected_town', 'waiting_for_selected_street'])
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


        city_ref = get_city_ref(selected_town)
        if city_ref:
            await state.update_data(city_ref=city_ref)


            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(
                    "Назад",
                    callback_data='back_to_city_selection'
                )
            )

            await bot.send_message(callback_query.message.chat.id, f'{location_info}\n\n🛣️ Введіть назву вулиці:', reply_markup=keyboard)
            await state.set_state('waiting_for_street')
        else:
            await bot.send_message(callback_query.message.chat.id, "Не вдалося отримати референс міста. Спробуйте ще раз.")



@dp.message_handler(state='waiting_for_street')
async def process_street_input(message: types.Message, state: FSMContext):
    selected_street = message.text

    async with state.proxy() as data:
        city_ref = data.get('city_ref')

    street_list = get_street_list(city_ref, selected_street)
    if street_list:
        await state.update_data(street_list=street_list)
        streets_keyboard = generate_streets_keyboard(street_list)  # Припустимо, що ви створите цю функцію
        await bot.send_message(message.chat.id, "🔍Виберіть назву вулиці:", reply_markup=streets_keyboard)
        await state.set_state('waiting_for_selected_street')
    else:
        await bot.send_message(message.chat.id, "Вулиць не знайдено.")

@dp.callback_query_handler(lambda c: c.data.startswith('street_'), state='waiting_for_selected_street')
async def process_selected_street(callback_query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        street_list = data.get('street_list')

    selected_street = callback_query.data

    # Збереження обраної вулиці у стані без префіксу "street_"
    selected_street = selected_street.replace('street_', '')
    await state.update_data(selected_street=selected_street)

    # Запит номеру будинку
    await bot.send_message(callback_query.message.chat.id, "Введіть номер будинку:")
    await state.set_state('waiting_for_house_number')


@dp.message_handler(state='waiting_for_house_number')
async def process_house_number_input(message: types.Message, state: FSMContext):
    house_number = message.text


    await state.update_data(house_number=house_number)


    await bot.send_message(message.chat.id, "Введіть коментар:")
    await state.set_state('waiting_for_comment')


@dp.message_handler(state='waiting_for_comment')
async def process_comment_input(message: types.Message, state: FSMContext):
    comment = message.text


    await state.update_data(comment=comment)


    async with state.proxy() as data:
        selected_street = data.get('selected_street')
        house_number = data.get('house_number')
        comment = data.get('comment')


    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            f"{selected_street} {house_number}, {comment}",
            callback_data='confirm_data'
        )
    )


    keyboard.add(
        InlineKeyboardButton(
            "Назад",
            callback_data='back_to_street_selection'
        )
    )

    await bot.send_message(message.chat.id, "Натисни для підтвердження:", reply_markup=keyboard)

    await state.set_state('waiting_for_year')

@dp.callback_query_handler(lambda c: c.data == 'back_to_street_selection', state='waiting_for_year')
async def back_to_street_selection(callback_query: CallbackQuery, state: FSMContext):
    await bot.send_message(callback_query.message.chat.id, "Введіть назву вулиці:")
    await state.set_state('waiting_for_street')




@dp.callback_query_handler(lambda c: c.data.startswith('confirm_data'), state='waiting_for_year')
async def process_confirm_data(callback_query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        selected_street = data.get('selected_street')
        house_number = data.get('house_number')
        comment = data.get('comment')

    meeting_info = f"Зустріч відбудеться по вулиці {selected_street}, будинок {house_number}. Коментар: {comment}"


    await bot.send_message(callback_query.message.chat.id, meeting_info)
    await bot.send_message(callback_query.message.chat.id, 'Виберіть рік:', reply_markup=year_keyboard)
    await state.set_state('waiting_for_year')


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




    async with state.proxy() as data:
        selected_year = data["year"]


    if (selected_year < current_datetime.year) or (selected_year == current_datetime.year and selected_month < current_datetime.month):
        await bot.send_message(callback_query.message.chat.id, "Ви не можете вибрати місяць в минулому. Виберіть інший місяць.")
    else:
        await bot.send_message(callback_query.message.chat.id, '🌝Виберіть день:', reply_markup=day_keyboard)
        await state.update_data(month=selected_month)
        await state.set_state('waiting_for_day')
@dp.callback_query_handler(lambda c: c.data.startswith('select_day:'), state='waiting_for_day')
async def process_day_input(callback_query: CallbackQuery, state: FSMContext):
    selected_day = callback_query.data.split(':')[1]
    selected_day = int(selected_day)




    async with state.proxy() as data:
        selected_year = data["year"]
        selected_month = data["month"]

    if (selected_year < current_datetime.year) or \
       (selected_year == current_datetime.year and selected_month < current_datetime.month) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day < current_datetime.day):
        await bot.send_message(callback_query.message.chat.id, "Ви не можете вибрати день в минулому. Виберіть інший день.")
    else:
        await bot.send_message(callback_query.message.chat.id, '🕛Виберіть годину:', reply_markup=hour_keyboard)
        await state.update_data(day=selected_day)
        await state.set_state('waiting_for_hour')


@dp.callback_query_handler(lambda c: c.data.startswith('select_hour:'), state='waiting_for_hour')
async def process_hour_input(callback_query: CallbackQuery, state: FSMContext):
    selected_hour = callback_query.data.split(':')[1]
    selected_hour = int(selected_hour)





    async with state.proxy() as data:
        selected_year = data["year"]
        selected_month = data["month"]
        selected_day = data["day"]


    if (selected_year < current_datetime.year) or \
       (selected_year == current_datetime.year and selected_month < current_datetime.month) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day < current_datetime.day) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day == current_datetime.day and selected_hour < current_datetime.hour):
        await bot.send_message(callback_query.message.chat.id, "Ви не можете вибрати годину в минулому. Виберіть іншу годину.")
    else:
        await bot.send_message(callback_query.message.chat.id, '⏱️Виберіть хвилину:', reply_markup=minute_keyboard)
        await state.update_data(hour=selected_hour)
        await state.set_state('waiting_for_minute')


from models import  JoinedUsers

@dp.callback_query_handler(lambda c: c.data.startswith('select_minute:'), state='waiting_for_minute')
async def process_minute_input(callback_query: CallbackQuery, state: FSMContext):
    selected_minute = callback_query.data.split(':')[1]
    selected_minute = int(selected_minute)

    async with state.proxy() as data:
        selected_year = data["year"]
        selected_month = data["month"]
        selected_day = data["day"]
        selected_hour = data["hour"]

    if (selected_year < current_datetime.year) or \
       (selected_year == current_datetime.year and selected_month < current_datetime.month) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day < current_datetime.day) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day == current_datetime.day and selected_hour < current_datetime.hour) or \
       (selected_year == current_datetime.year and selected_month == current_datetime.month and selected_day == current_datetime.day and selected_hour == current_datetime.hour and selected_minute < current_datetime.minute):
        await bot.send_message(callback_query.message.chat.id, "Ви не можете вибрати хвилину в минулому. Виберіть іншу хвилину.")
    else:
        await create_meeting(callback_query, state, selected_minute)


async def create_meeting(callback_query: CallbackQuery, state: FSMContext, selected_minute: int):
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
        selected_street = data.get("selected_street")  # Отримання назви вулиці зі стану
        house_number = data.get("house_number")  # Отримання номеру будинку зі стану
        comment = data.get("comment")  # Отримання коментаря зі стану

    # Отримання дати та часу
    date_time = datetime(selected_year, selected_month, selected_day, selected_hour, selected_minute)
    formatted_date_time = date_time.strftime('%Y-%m-%d %H:%M')

    # Створення об'єкта для збереження в базі даних
    user_data = {
        "user_id": user_id,
        "city": selected_city,
        "region": f"{selected_region} обл.",
        "street": selected_street,  # Збереження вулиці
        "house_number": house_number,  # Збереження номеру будинку
        "comment": comment,  # Збереження коментаря
        "datetime": formatted_date_time,
        "timestamp": datetime.now(),
        "meeting_name": meeting_name,
        "description": description
    }

    # Додавання запису до бази даних
    collection.insert_one(user_data)

    response = (
        f"✅Ваша зустріч {meeting_name} відбудеться у місті {selected_city}, {selected_region} обл. на вулиці {selected_street} {house_number}, {comment} "
        f"Дата: {formatted_date_time}"
    )
    await bot.send_message(callback_query.message.chat.id, response)

    join_button = InlineKeyboardButton("✅Приєднатися", callback_data=str(user_id))
    keyboard = InlineKeyboardMarkup()
    keyboard.add(join_button)

    post_message = f"Нова зустріч: {meeting_name} відбудеться у місті {selected_city}, {selected_region} обл. на вулиці {selected_street} {house_number}, {comment}\n Дата: {formatted_date_time} "
    await bot.send_message(GROUP_ID, post_message, reply_markup=keyboard)

    await state.finish()

    await bot.send_message(callback_query.message.chat.id, "Ваша зустріч була успішно створена.", reply_markup=kb_client)



@dp.callback_query_handler(lambda callback_query: True)
async def join_meeting(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    user_username = callback_query.from_user.username

    JoinedUsers.add_joined_user(user_id, user_username)

    await bot.answer_callback_query(callback_query.id, text="Ви приєднались до зустрічі!")



if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
