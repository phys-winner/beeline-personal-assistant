from telegram import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard():
    keyboard = [[KeyboardButton('📱 Основная информация')],
                [KeyboardButton('✅ Проверить номер'), KeyboardButton('📙 Детализация')],
                [KeyboardButton('📖 Тариф'), KeyboardButton('🔎 Услуги')],
                [KeyboardButton('⚙️ Настройки')]]
    return ReplyKeyboardMarkup(keyboard, is_persistent=False, resize_keyboard=True)


def back_menu():
    return ReplyKeyboardMarkup([[KeyboardButton('🔙 Назад')]],
                               is_persistent=True, resize_keyboard=True)

