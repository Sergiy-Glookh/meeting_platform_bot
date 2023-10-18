from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
def generate_years_keyboard():
    years = [str(year) for year in range(2023, 2032)]  # Згенерувати список років
    years_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True)
    years_keyboard.add(*years)  # Додати роки до клавіатури
    return years_keyboard

def generate_back_button():
    # Створіть кнопку "Назад"
    back_button = KeyboardButton("Назад")
    return ReplyKeyboardMarkup(resize_keyboard=True).add(back_button)

button1 = KeyboardButton(text="Створити зустріч")
button2 = KeyboardButton(text="Переглянути активні зустрічі")

# Створення клавіатури з цими кнопками
kb_client = ReplyKeyboardMarkup(keyboard=[[button1, button2]], resize_keyboard=True)



# Кількість кнопок в рядку для років
years_per_row = 4

year_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=years_per_row)

# Створюємо кнопки для клавіатури років
year_buttons = [KeyboardButton(str(year)) for year in range(2023, 2043)]  # Змініть діапазон на потрібний

# Розбиваємо кнопки на рядки
for row in range(0, len(year_buttons), years_per_row):
    year_keyboard.row(*year_buttons[row:row + years_per_row])


# Створення клавіатури для вибору місяця

buttons_per_row = 4

month_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=buttons_per_row)

# Створюємо кнопки для клавіатури
buttons = [KeyboardButton(str(i)) for i in range(1, 13)]

# Розбиваємо кнопки на рядки
for row in range(0, len(buttons), buttons_per_row):
    month_keyboard.row(*buttons[row:row + buttons_per_row])


# Створення клавіатури для вибору дня
days_per_row = 6

day_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=days_per_row)

# Створюємо кнопки для клавіатури днів
day_buttons = [KeyboardButton(str(day)) for day in range(1, 32)]

# Розбиваємо кнопки на рядки
for row in range(0, len(day_buttons), days_per_row):
    day_keyboard.row(*day_buttons[row:row + days_per_row])

# Створення клавіатури для вибору години
# Кількість кнопок в рядку для годин
hours_per_row = 4

hour_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=hours_per_row)

# Створюємо кнопки для клавіатури годин
hour_buttons = [KeyboardButton(str(hour)) for hour in range(0, 24)]

# Розбиваємо кнопки на рядки
for row in range(0, len(hour_buttons), hours_per_row):
    hour_keyboard.row(*hour_buttons[row:row + hours_per_row])
# Кількість кнопок в рядку для хвилин
minutes_per_row = 4

minute_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=minutes_per_row)

# Створюємо кнопки для клавіатури хвилин
minute_buttons = [KeyboardButton(str(minute)) for minute in range(0, 60, 5)]  # Змініть крок на потрібний

# Розбиваємо кнопки на рядки
for row in range(0, len(minute_buttons), minutes_per_row):
    minute_keyboard.row(*minute_buttons[row:row + minutes_per_row])

