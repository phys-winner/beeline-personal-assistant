from telegram import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard():
    keyboard = [[KeyboardButton('Хранящиеся данные')],
                [KeyboardButton('Проверить мой номер')],
                [KeyboardButton('Тариф'), KeyboardButton('Услуги'), KeyboardButton('Подписки')],
                [KeyboardButton('Счётчики', )]]
    return ReplyKeyboardMarkup(keyboard, is_persistent=False)


def return_to_main_menu_keyboard():
    keyboard = [[KeyboardButton('🔙 В главное меню')]]
    return ReplyKeyboardMarkup(keyboard)
