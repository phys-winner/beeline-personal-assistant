from telegram import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard():
    keyboard = [[KeyboardButton('Хранящиеся данные')],
                [KeyboardButton('Тариф'), KeyboardButton('Услуги')],
                [KeyboardButton('Счётчики')]]
    return ReplyKeyboardMarkup(keyboard)


def return_to_main_menu_keyboard():
    keyboard = [[KeyboardButton('🔙 В главное меню')]]
    return ReplyKeyboardMarkup(keyboard)
