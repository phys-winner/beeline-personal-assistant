from telegram import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard():
    keyboard = [[KeyboardButton('📱 Основная информация')],
                [KeyboardButton('✅ Проверить мой номер')],
                [KeyboardButton('📖 Тариф'), KeyboardButton('🔎 Услуги')]]
    return ReplyKeyboardMarkup(keyboard, is_persistent=False)


def return_to_main_menu_keyboard():
    keyboard = [[KeyboardButton('🔙 В главное меню')]]
    return ReplyKeyboardMarkup(keyboard)
