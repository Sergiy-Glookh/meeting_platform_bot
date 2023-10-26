from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardButton


def generate_towns_keyboard(info):
    keyboard = []

    for item in info:
        if ' (' in item:
            town, region = item.split(' (')
            region = region.rstrip(')')
            region = f"{region}.обл"
            button_text = f"{town} ({region})"

            button = InlineKeyboardButton(text=button_text, callback_data=f'town_{town}')
            keyboard.append([button])

    back_button = InlineKeyboardButton(text="Назад  ↩️️", callback_data="back")
    keyboard.append([back_button])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_back_button():
    return InlineKeyboardButton("Назад ↩️", callback_data="back")


#
def create_keyboard_with_back():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(create_back_button())
    return keyboard


button1 = InlineKeyboardButton(text="Створити зустріч", callback_data="create_meeting")
button2 = InlineKeyboardButton(text="Переглянути активні зустрічі", callback_data="view_meetings")
button3 = InlineKeyboardButton(text="Переглянути завершені зустрічі", callback_data="view_end_meetings")
kb_client = InlineKeyboardMarkup(inline_keyboard=[[button1], [button2], [button3]])

# Створення інлайн клавіатури для вибору року
year_buttons = [InlineKeyboardButton(str(year), callback_data=f"select_year:{year}") for year in range(2023, 2030)]
year_buttons.append(create_back_button())
year_keyboard = InlineKeyboardMarkup(row_width=3).add(*year_buttons)

# Створення інлайн клавіатури для вибору місяця
month_buttons = [InlineKeyboardButton(str(i), callback_data=f"select_month:{i}") for i in range(1, 13)]
month_buttons.append(create_back_button())
month_keyboard = InlineKeyboardMarkup().add(*month_buttons)

# Створення інлайн клавіатури для вибору дня
day_buttons = [InlineKeyboardButton(str(day), callback_data=f"select_day:{day}") for day in range(1, 32)]
day_buttons.append(create_back_button())
day_keyboard = InlineKeyboardMarkup().add(*day_buttons)

# Створення інлайн клавіатури для вибору години
hour_buttons = [InlineKeyboardButton(str(hour), callback_data=f"select_hour:{hour}") for hour in range(0, 24)]
hour_buttons.append(create_back_button())
hour_keyboard = InlineKeyboardMarkup().add(*hour_buttons)

# Створення інлайн клавіатури для вибору хвилини
minute_buttons = [InlineKeyboardButton(str(minute), callback_data=f"select_minute:{minute}") for minute in
                  range(0, 60, 5)]
minute_buttons.append(create_back_button())
minute_keyboard = InlineKeyboardMarkup().add(*minute_buttons)

# Додавання кнопки "Назад" до головного меню
kb_client_with_back = InlineKeyboardMarkup()
kb_client_with_back.add(create_back_button())

keyboard_with_back = InlineKeyboardMarkup(row_width=1)
keyboard_with_back.add(InlineKeyboardButton("Назад ️️ ️️↩️", callback_data="back"))

keyboard_back = InlineKeyboardMarkup().add(InlineKeyboardButton('Назад', callback_data='back_to_meeting_name'))
keyboard_back_to_description = InlineKeyboardMarkup().add(
    InlineKeyboardButton('Назад до опису', callback_data='back_to_description'))