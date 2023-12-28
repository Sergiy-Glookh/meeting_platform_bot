from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types
from aiogram.dispatcher import FSMContext
from .api import get_info, get_street_list, get_city_ref
from src.db.admin_connect import *
from src.db.models import Meeting
from .button import *
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
import uuid
from datetime import datetime as dt


class MeetingCreation(StatesGroup):
    waiting_for_meeting_name = State()
    waiting_for_description = State()
    waiting_for_town = State()
    waiting_for_selected_town = State()
    waiting_for_street = State()
    waiting_for_selected_street = State()
    waiting_for_house_number = State()


class MeetingEditing(StatesGroup):
    waiting_for_meeting_to_edit = State()
    waiting_for_street_editing = State()
    waiting_for_selected_street_editing = State()
    waiting_for_house_number_editing = State()


waiting_for_street = State()
previous_states = {}
previous_keyboard = None
user_states = {}
waiting_for_description = State()
current_datetime = dt.now()
cancel_requests = {}


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


def is_valid_uuid(s):
    try:
        uuid.UUID(str(s), version=4)
        return True
    except ValueError:
        return False


@dp.message_handler(commands=['start'])
async def start_def(message: types.Message):
    await bot.send_message(chat_id=message.from_user.id, text='Привіт, що хочеш зробити?🤔', reply_markup=kb_client)


@dp.callback_query_handler(lambda c: c.data.startswith('view_meeting:'))
async def view_meeting_details(callback_query: CallbackQuery):
    meeting_id = callback_query.data.split(':')[1]
    user_id = callback_query.from_user.id

    if is_valid_uuid(meeting_id):

        meeting = Meeting.objects(meeting_id=meeting_id).first()

        if meeting:

            meeting_name = meeting['meeting_name']
            city = meeting['city']
            region = meeting['region']
            meeting_datetime = meeting['datetime']

            response = f"Деталі про зустріч '{meeting_name}':\n"
            response += f"📅 Дата та час: {meeting_datetime}\n"
            response += f"🌍 Місто: {city}, {region}"

            keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton('↩️ Назад', callback_data='view_meetings'))

            await bot.send_message(user_id, response, reply_markup=keyboard)
        else:
            await bot.send_message(user_id, "Зустріч не знайдена.")
    else:
        await bot.send_message(user_id, "Недійсний ідентифікатор зустрічі.")


def is_meeting_active(meeting_datetime):
    """Повертає True, якщо зустріч ще не відбулася."""
    return dt.now() < meeting_datetime


@dp.callback_query_handler(lambda c: c.data == 'view_meetings')
async def view_active_meetings(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    active_meetings = Meeting.objects(user_id=user_id)

    response = "🍻Ваші активні зустрічі:\n"
    keyboard = InlineKeyboardMarkup(row_width=3)

    for meeting in active_meetings:
        meeting_datetime = meeting['datetime']
        if is_meeting_active(meeting_datetime):
            meeting_name = meeting['meeting_name']
            city = meeting['city']
            region = meeting['region']
            meeting_id = str(meeting['meeting_id'])

            text = f"🥂{meeting_name}\n 📅 {meeting_datetime}\n🌍 {city}"
            keyboard.add(InlineKeyboardButton(text, callback_data=f'view_meeting:{meeting_id}'))

            keyboard.add(
                InlineKeyboardButton(f"🖊️ Редагувати", callback_data=f'edit_meeting:{meeting_id}'),
                InlineKeyboardButton(f"❌ Скасувати", callback_data=f'cancel_meeting:{meeting_id}'),
                InlineKeyboardButton(f"🔍 Детальніше", callback_data=f'details_meeting:{meeting_id}')
            )

    if len(keyboard.inline_keyboard) == 0:
        response = "😢Наразі у вас немає активних зустрічей."
        keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back_to_menu'))
    else:
        keyboard.add(InlineKeyboardButton('↩️ Назад', callback_data='back_to_menu'))

    await bot.send_message(user_id, response, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'view_end_meetings')
async def view_completed_meetings(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    current_time = dt.now()

    completed_meetings = Meeting.objects(user_id=user_id, datetime__lt=current_time)

    if completed_meetings:
        response = "👋 Ваші завершені зустрічі:\n"
        for meeting in completed_meetings:
            meeting_name = meeting['meeting_name']
            datetime_str = meeting['datetime'].strftime('%Y-%m-%d %H:%M')
            response += f"\n🥂 {meeting_name} (Дата: {datetime_str})"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton('↩️ Назад', callback_data='back_to_menu'))
    else:
        response = "😌 Наразі у вас немає завершених зустрічей."
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

    meeting = Meeting.objects(meeting_id=meeting_id).first()

    if meeting:
        meeting_name = meeting['meeting_name']
        description = meeting['description']
        city = meeting['city']
        region = meeting['region']
        datetime = meeting['datetime']

        response = f"🥂 Назва зустрічі: {meeting_name}\n" \
                   f"📝 Опис: {description}\n" \
                   f"📅 Дата та час: {datetime}\n" \
                   f"🌍 Локація: {city}"

        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(InlineKeyboardButton(f"👀 Хто приєднався", callback_data=f'joined_meeting:{meeting_id}'))

        await bot.send_message(user_id, response, reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")


@dp.callback_query_handler(lambda c: c.data == 'back_to_list')
async def back_to_list(callback_query: CallbackQuery):
    data = await dp.current_state().get_data()
    prev_message_id = data.get('prev_message_id')

    try:
        await bot.delete_message(callback_query.from_user.id, prev_message_id)
    except MessageToDeleteNotFound:
        pass

    try:
        await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    except MessageToDeleteNotFound:
        pass


#EDIT
@dp.callback_query_handler(lambda c: c.data.startswith('edit_meeting:'))
async def edit_meeting(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    meeting = Meeting.objects(meeting_id=meeting_id).first()

    if meeting:

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🖊️ Редагувати назву", callback_data=f'edit_name:{meeting_id}'))
        keyboard.add(InlineKeyboardButton("📝 Редагувати опис", callback_data=f'edit_description:{meeting_id}'))
        keyboard.add(InlineKeyboardButton("📅 Редагувати дату", callback_data=f'edit_date:{meeting_id}'))
        keyboard.add(InlineKeyboardButton("🌍 Редагувати локацію", callback_data=f'edit_location:{meeting_id}'))
        keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back'))

        response = "Виберіть параметр, який ви хочете редагувати."
        await bot.send_message(user_id, response, reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")


@dp.callback_query_handler(lambda c: c.data == 'back')
async def back_to_meetings_menu(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    active_meetings = Meeting.objects(user_id=user_id)

    if active_meetings:
        response = "🍻Ваші активні зустрічі:\n"
        keyboard = InlineKeyboardMarkup(row_width=3)
        for meeting in active_meetings:
            meeting_name = meeting['meeting_name']
            city = meeting['city']
            region = meeting['region']
            datetime = meeting['datetime']
            meeting_id = str(meeting['meeting_id'])

            text = f"🥂{meeting_name}\n 📅{datetime}\n 🌍 {city}, {region}"
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

    meeting = Meeting.objects(meeting_id=meeting_id).first()

    if meeting:
        response = "Введіть нову назву для зустрічі:"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back'))

        await bot.send_message(user_id, response, reply_markup=keyboard)

        @dp.message_handler(lambda message: message.from_user.id == user_id)
        async def process_new_meeting_name(message: types.Message):
            new_meeting_name = message.text

            Meeting.objects(meeting_id=meeting_id).update_one(set__meeting_name=new_meeting_name)

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🖊️ Редагувати назву", callback_data=f'edit_name:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("📝 Редагувати опис", callback_data=f'edit_description:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("📅 Редагувати дату", callback_data=f'edit_date:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("🌍 Редагувати локацію", callback_data=f'edit_location:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back_to_active_meetings'))

            await bot.send_message(user_id, f"Назву зустрічі '{new_meeting_name}' змінено. Що бажаєте редагувати далі?",
                                   reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")


@dp.callback_query_handler(lambda c: c.data.startswith('edit_description:'))
async def edit_meeting_description(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    meeting = Meeting.objects(meeting_id=meeting_id).first()

    if meeting:
        response = "Введіть новий опис для зустрічі:"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back'))

        await bot.send_message(user_id, response, reply_markup=keyboard)

        @dp.message_handler(lambda message: message.from_user.id == user_id)
        async def process_new_meeting_description(message: types.Message):
            new_description = message.text

            Meeting.objects(meeting_id=meeting_id).update_one(set__description=new_description)

            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("🖊️ Редагувати назву", callback_data=f'edit_name:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("📝 Редагувати опис", callback_data=f'edit_description:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("📅 Редагувати дату", callback_data=f'edit_date:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("🌍 Редагувати локацію", callback_data=f'edit_location:{meeting_id}'))
            keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back_to_active_meetings'))

            await bot.send_message(user_id,
                                   f"Опис зустрічі змінено на '{new_description}'. Що бажаєте редагувати далі?",
                                   reply_markup=keyboard)
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")


@dp.callback_query_handler(lambda c: c.data.startswith('edit_month:'))
async def edit_month(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    meeting = Meeting.objects(meeting_id=meeting_id).first()
    current_month = meeting.datetime.month if meeting else 'не визначено'

    keyboard = InlineKeyboardMarkup(row_width=3)
    for month in range(1, 13):
        keyboard.add(InlineKeyboardButton(str(month), callback_data=f'select_month:{meeting_id}:{month}'))

    await bot.send_message(user_id, f"Поточний місяць для проведення зустрічі: {current_month}. Виберіть новий місяць:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('select_month:'))
async def select_month(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data_parts = callback_query.data.split(":")
    print(f"data_parts: {data_parts}")
    selected_month = int(data_parts[2])
    meeting_id = data_parts[1]

    meeting = Meeting.objects(meeting_id=meeting_id).first()

    if meeting:
        current_datetime = meeting.datetime
        updated_datetime = current_datetime.replace(month=selected_month)

        Meeting.objects(meeting_id=meeting_id).update_one(set__datetime=updated_datetime)

        await bot.send_message(user_id, f"Місяць зустрічі змінено на {selected_month}.")
    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")

    await show_edit_menu(user_id, meeting_id)
    await state.finish()



@dp.callback_query_handler(lambda c: c.data.startswith('edit_date:'))
async def edit_date(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    meeting = Meeting.objects(meeting_id=meeting_id).first()
    if meeting:
        current_datetime = meeting['datetime']

        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("📅 Редагувати рік", callback_data=f'edit_year:{meeting_id}'),
            InlineKeyboardButton("📅 Редагувати місяць", callback_data=f'edit_month:{meeting_id}')
        )
        keyboard.row(
            InlineKeyboardButton("📅 Редагувати день", callback_data=f'edit_day:{meeting_id}'),
            InlineKeyboardButton("🕒 Редагувати час", callback_data=f'edit_time:{meeting_id}')
        )
        keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back_to_edit_menu'))

        await bot.send_message(user_id, "Оберіть, що ви хочете змінити:", reply_markup=keyboard)

    else:
        await bot.send_message(user_id, "Зустріч не знайдена.")


@dp.callback_query_handler(lambda c: c.data.startswith('edit_year:'))
async def edit_year(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    keyboard = InlineKeyboardMarkup(row_width=3)
    # Припустимо, що користувач може вибрати рік від поточного до +5 років у майбутньому
    for year in range(dt.now().year, dt.now().year + 6):
        keyboard.add(InlineKeyboardButton(str(year), callback_data=f'select_year:{meeting_id}:{year}'))

    await bot.send_message(user_id, "Оберіть рік:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('select_year:'))
async def select_year(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data_parts = callback_query.data.split(":")
    selected_year = int(data_parts[2])
    meeting_id = data_parts[1]

    await state.update_data(selected_year=selected_year)

    try:
        meeting = Meeting.objects(meeting_id=meeting_id).first()
        if meeting:
            new_datetime = meeting['datetime'].replace(year=selected_year)
            Meeting.objects(meeting_id=meeting_id).update_one(set__datetime=new_datetime)
            await bot.send_message(user_id, f"Рік зустрічі оновлено на {selected_year}.")
        else:
            await bot.send_message(user_id, "Зустріч не знайдена.")
    except Exception as e:
        await bot.send_message(user_id, f"Помилка при оновленні року: {e}")

    await show_edit_menu(user_id, meeting_id)
    await state.finish()


@dp.callback_query_handler(lambda c: c.data.startswith('edit_month:'))
async def edit_month(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    keyboard = InlineKeyboardMarkup(row_width=3)
    for month in range(1, 13):
        keyboard.add(InlineKeyboardButton(str(month), callback_data=f'select_month:{meeting_id}:{month}'))

    await bot.send_message(user_id, "Оберіть місяць:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('edit_day:'))
async def edit_day(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    keyboard = InlineKeyboardMarkup(row_width=7)
    for day in range(1, 32):
        keyboard.add(InlineKeyboardButton(str(day), callback_data=f'select_day:{meeting_id}:{day}'))

    await bot.send_message(user_id, "Оберіть день:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('select_day:'))
async def select_day(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    data_parts = callback_query.data.split(":")
    selected_day = int(data_parts[2])
    meeting_id = data_parts[1]

    await state.update_data(selected_day=selected_day)

    try:
        meeting = Meeting.objects(meeting_id=meeting_id).first()
        if meeting:
            new_datetime = meeting['datetime'].replace(day=selected_day)
            Meeting.objects(meeting_id=meeting_id).update_one(set__datetime=new_datetime)
            await bot.send_message(user_id, f"День зустрічі оновлено на {selected_day}.")
        else:
            await bot.send_message(user_id, "Зустріч не знайдена.")
    except Exception as e:
        await bot.send_message(user_id, f"Помилка при оновленні дня: {e}")

    await show_edit_menu(user_id, meeting_id)
    await state.finish()


user_editing_info = {}

@dp.callback_query_handler(lambda c: c.data.startswith('edit_time:'))
async def edit_time(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    user_editing_info[user_id] = {'meeting_id': meeting_id}

    await bot.send_message(user_id, "Оберіть годину:", reply_markup=hour_keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('select_hour:'))
async def select_hour(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    selected_hour = int(callback_query.data.split(':')[1])

    user_editing_info[user_id]['selected_hour'] = selected_hour

    await bot.send_message(user_id, "Оберіть хвилину:", reply_markup=minute_keyboard)

@dp.callback_query_handler(lambda c: c.data.startswith('select_minute:'))
async def select_minute(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    selected_minute = int(callback_query.data.split(':')[1])

    editing_info = user_editing_info.get(user_id, {})
    meeting_id = editing_info.get('meeting_id')
    selected_hour = editing_info.get('selected_hour')

    if meeting_id is None or selected_hour is None:
        await bot.send_message(user_id, "Сталася помилка. Спробуйте ще раз.")
        return

    try:
        current_datetime = Meeting.objects(meeting_id=meeting_id).first().datetime
        new_datetime = current_datetime.replace(hour=selected_hour, minute=selected_minute)
        Meeting.objects(meeting_id=meeting_id).update_one(set__datetime=new_datetime)
        await bot.send_message(user_id, f"Час зустрічі оновлено на {new_datetime.strftime('%Y-%m-%d %H:%M')}.")
    except Exception as e:
        await bot.send_message(user_id, f"Сталася помилка при оновленні часу: {e}")

    if user_id in user_editing_info:
        del user_editing_info[user_id]

    await show_edit_menu(user_id, meeting_id)


@dp.callback_query_handler(lambda c: c.data.startswith('edit_location:'))
async def edit_location(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    await state.update_data(editing_meeting_id=meeting_id)

    keyboard = create_keyboard_with_back()
    await bot.send_message(user_id, "Введіть назву міста для зустрічі:", reply_markup=keyboard)

    await state.set_state('waiting_for_selected_town_edited')


@dp.message_handler(state='waiting_for_selected_town_edited')
async def process_town_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    town_name = message.text

    info = get_info(town_name)
    if info:
        towns_keyboard = generate_towns_keyboard(info)
        await bot.send_message(user_id, "Оберіть населений пункт:", reply_markup=towns_keyboard)
    else:
        await bot.send_message(user_id, "Місто не знайдено. Спробуйте ще раз.")


@dp.callback_query_handler(lambda c: c.data.startswith('town_'), state='waiting_for_selected_town_edited')
async def process_selected_town(callback_query: CallbackQuery, state: FSMContext):
    selected_town = callback_query.data.split('_')[1]
    await state.update_data(selected_city=selected_town)
    city_ref = get_city_ref(selected_town)
    await state.update_data(city_ref=city_ref)
    await bot.send_message(callback_query.from_user.id, "Введіть назву вулиці:")
    await state.set_state('waiting_for_street_edited')


@dp.message_handler(state='waiting_for_street_edited')
async def process_street_input(message: types.Message, state: FSMContext):
    selected_street = message.text
    city_ref = (await state.get_data()).get('city_ref')

    street_list = get_street_list(city_ref, selected_street)

    if street_list.get('success') and street_list['data'][0]['TotalCount'] > 0:
        streets_keyboard = generate_streets_keyboard(street_list['data'][0]['Addresses'])
        await bot.send_message(message.chat.id, "Оберіть вулицю:", reply_markup=streets_keyboard)
        await state.set_state('waiting_for_selected_street_edited')
    else:
        await bot.send_message(message.chat.id, "Вулицю не знайдено, спробуйте ще раз.")


@dp.callback_query_handler(lambda c: c.data.startswith('street_'), state='waiting_for_selected_street_edited')
async def process_selected_street(callback_query: CallbackQuery, state: FSMContext):
    selected_street = callback_query.data.split('_')[1]
    await state.update_data(selected_street=selected_street)

    await bot.send_message(callback_query.from_user.id, "Введіть номер будинку:")
    await state.set_state('waiting_for_house_number_edited')



@dp.message_handler(state='waiting_for_house_number_edited')
async def process_house_number_input(message: types.Message, state: FSMContext):
    house_number = message.text
    await state.update_data(house_number=house_number)

    data = await state.get_data()
    selected_city = data['selected_city']
    selected_street = data['selected_street']

    meeting_id = data['editing_meeting_id']
    new_location = f"{selected_city}, {selected_street}, {house_number}"
    meeting_obj: Meeting = Meeting.objects(meeting_id=meeting_id).first()
    meeting_obj.city = selected_city
    meeting_obj.street = selected_street
    meeting_obj.house_number = house_number
    meeting_obj.save()

    await bot.send_message(message.chat.id, "Локацію зустрічі оновлено на " + new_location)
    await state.finish()

    await show_edit_menu(message.chat.id, meeting_id)


async def create_back_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("↩️ Назад", callback_data='back_to_meetings'))
    return keyboard


@dp.message_handler(lambda message: message.text and message.from_user.id in cancel_requests)
async def handle_cancel_reason(message: Message):
    user_id = message.from_user.id
    cancel_reason = message.text
    meeting_info = cancel_requests[user_id]
    meeting_id = meeting_info['meeting_id']

    Meeting.objects(meeting_id=meeting_id).delete()

    del cancel_requests[user_id]

    await bot.send_message(user_id, f"Зустріч скасовано. Причина: {cancel_reason}")


@dp.callback_query_handler(lambda c: c.data.startswith('cancel_meeting:'))
async def cancel_meeting(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    meeting_id = callback_query.data.split(':')[1]

    if is_valid_uuid(meeting_id):
        meeting = Meeting.objects(meeting_id=meeting_id).first()

        if meeting:
            try:
                confirmation_keyboard = create_confirmation_keyboard()
                await bot.send_message(user_id, "Ви впевнені, що хочете скасувати зустріч?", reply_markup=confirmation_keyboard)
                cancel_requests[user_id] = {'meeting_id': meeting_id, 'meeting_data': meeting}
            except Exception as e:
                print(f"Помилка при скасуванні зустрічі: {e}")
                await bot.send_message(user_id, "Помилка при скасуванні зустрічі.")
        else:
            await bot.send_message(user_id, "Зустріч не знайдена.")
    else:
        await bot.send_message(user_id, "Недійсний ідентифікатор зустрічі.")


@dp.callback_query_handler(lambda c: c.data == 'confirm_cancel')
async def confirm_cancel(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id in cancel_requests:
        meeting_info = cancel_requests[user_id]
        meeting_id = meeting_info['meeting_id']

        Meeting.objects(meeting_id=meeting_id).delete()

        del cancel_requests[user_id]

        await bot.send_message(user_id, f"Зустріч скасовано.")

        await view_active_meetings(callback_query)


@dp.callback_query_handler(lambda c: c.data == 'deny_cancel')
async def deny_cancel(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    if user_id in cancel_requests:
        del cancel_requests[user_id]

    await view_active_meetings(callback_query)


@dp.callback_query_handler(lambda c: c.data == 'back_to_meetings')
async def back_to_meetings(callback_query: CallbackQuery):
    await view_active_meetings(callback_query)


@dp.callback_query_handler(lambda c: c.data == 'back_to_active_meetings')
async def back_to_active_meetings(callback_query: CallbackQuery):
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


@dp.message_handler(lambda message: len(message.text), state='waiting_for_description')
async def process_description_input(message: types.Message, state: FSMContext):
    description = message.text

    async with state.proxy() as data:
        data['description'] = description
        data['previous_state'] = 'waiting_for_description'

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
        await message.answer("Назва населеного пункту не корректна😢. Введіть іншу назву:")


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

            await bot.send_message(callback_query.message.chat.id, f'{location_info}\n\n🛣️ Введіть назву вулиці:',
                                   reply_markup=keyboard)
            await state.set_state('waiting_for_street')
        else:
            await bot.send_message(callback_query.message.chat.id,
                                   "Не вдалося отримати референс міста. Спробуйте ще раз.")


@dp.message_handler(state='waiting_for_street')
async def process_street_input(message: types.Message, state: FSMContext):
    selected_street = message.text
    await state.update_data(selected_street=selected_street)

    city_ref = (await state.get_data()).get('city_ref')
    street_list = get_street_list(city_ref, selected_street)

    if street_list.get('success') and street_list['data'][0]['TotalCount'] > 0:
        street_list = street_list['data'][0]['Addresses']
        await state.update_data(street_list=street_list)
        streets_keyboard = generate_streets_keyboard(street_list)
        await bot.send_message(message.chat.id, "🔍Виберіть назву вулиці:", reply_markup=streets_keyboard)
        await state.set_state('waiting_for_selected_street')
    else:
        keyboard_back = InlineKeyboardMarkup().add(
            InlineKeyboardButton('↩️Назад', callback_data='back_to_city_selection'))
        await bot.send_message(message.chat.id,
                               "Вулицю не знайдено. Будь ласка, введіть іншу назву вулиці або натисніть кнопку 'Назад'.",
                               reply_markup=keyboard_back)
        await state.set_state('waiting_for_street')


@dp.callback_query_handler(lambda c: c.data.startswith('street_'), state='waiting_for_selected_street')
async def process_selected_street(callback_query: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        street_list = data.get('street_list')

    selected_street = callback_query.data

    selected_street = selected_street.replace('street_', '')
    await state.update_data(selected_street=selected_street)

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
        await create_meeting(callback_query, state, selected_minute)


meetings_participants = {}


async def create_meeting(callback_query: CallbackQuery, state: FSMContext, selected_minute: int):
    meeting_id = str(uuid.uuid4())
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
        selected_street = data.get("selected_street")
        house_number = data.get("house_number")
        comment = data.get("comment")

    date_time = dt(selected_year, selected_month, selected_day, selected_hour, selected_minute)
    formatted_date_time = date_time.strftime('%Y-%m-%d %H:%M')

    user_data = {
        "meeting_id": meeting_id,
        "user_id": user_id,
        "city": selected_city,
        "region": f"{selected_region} обл.",
        "street": selected_street,
        "house_number": house_number,
        "comment": comment,
        "datetime": formatted_date_time,
        "timestamp": dt.now(),
        "meeting_name": meeting_name,
        "description": description,
        "participants": []
    }

    user_name = callback_query.from_user.username or callback_query.from_user.first_name

    new_meeting = Meeting(**user_data)
    new_meeting.save()

    if formatted_date_time not in meetings_participants:
        meetings_participants[formatted_date_time] = [{"user_id": user_id, "username": user_name}]
    else:
        meetings_participants[formatted_date_time].append({"user_id": user_id, "username": user_name})
    if formatted_date_time not in meetings_participants:
        meetings_participants[formatted_date_time] = [user_id]
    else:
        meetings_participants[formatted_date_time].append(user_id)
    response = (
        f"✅Ваша зустріч {meeting_name} відбудеться у місті {selected_city}, {selected_region} обл. на вулиці {selected_street} {house_number}, {comment} "
        f"Дата: {formatted_date_time}"
    )
    await bot.send_message(callback_query.message.chat.id, response)

    join_button_text = "✅Приєднатися"
    join_button_callback = f"join_{meeting_id}"

    join_button = InlineKeyboardButton(join_button_text, callback_data=join_button_callback)
    keyboard = InlineKeyboardMarkup()
    keyboard.add(join_button)
    post_message = f"Нова зустріч: {meeting_name} відбудеться у місті {selected_city}, {selected_region} обл. на вулиці {selected_street} {house_number}, {comment}\n Дата: {formatted_date_time} "
    print(GROUP_ID)

    await bot.send_message(GROUP_ID, post_message, reply_markup=keyboard)

    await state.finish()

    await bot.send_message(callback_query.message.chat.id, "Ваша зустріч була успішно створена.",
                           reply_markup=kb_client)


@dp.callback_query_handler(lambda c: c.data.startswith('join_'))
async def join_meeting(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_name = callback_query.from_user.username or callback_query.from_user.first_name
    meeting_id = callback_query.data.split('_')[1] if '_' in callback_query.data else None

    if meeting_id:
        Meeting.objects(meeting_id=meeting_id).update_one(
            add_to_set__participants={"user_id": user_id, "username": user_name})
        await bot.answer_callback_query(callback_query.id, text="Ви приєднались до зустрічі!")
    else:
        await bot.answer_callback_query(callback_query.id, text="Помилка: Не знайдено ідентифікатора зустрічі")


@dp.callback_query_handler(lambda c: c.data.startswith('joined_meeting:'))
async def show_joined_users(callback_query: CallbackQuery):
    meeting_id = callback_query.data.split(':')[1]

    meeting = Meeting.objects(meeting_id=meeting_id).first()

    keyboard = None

    if meeting and 'participants' in meeting:
        participants = meeting['participants']
        if participants:
            buttons = []

            for participant in participants:
                username = participant.get('username', 'No username')
                button = InlineKeyboardButton(username, url=f"https://t.me/{username}")
                buttons.append([button])

            keyboard = InlineKeyboardMarkup(row_width=1, inline_keyboard=buttons)
            keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_list"))

            response = "Список учасників зустрічі:"
        else:
            response = "До цієї зустрічі ще ніхто не приєднався."
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_list"))
    else:
        response = "Інформація про учасників не доступна для цієї зустрічі."

    message = await bot.send_message(callback_query.from_user.id, response, reply_markup=keyboard)

    await dp.current_state().update_data(prev_message_id=message.message_id)


def main():
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)

