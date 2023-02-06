from keyboards import *
from utils import *
from main import ADD_ACCOUNT, RENAME_ACCOUNT, start

from telegram import Update, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    ConversationHandler
)


async def check_rename_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_name = update.message.text
    if len(new_name) == 0:
        await show_rename_account(update, context)
        return RENAME_ACCOUNT
    else:
        number = get_current_number(context)
        await update.message.reply_text(f'✔️ Вы успешно переименовали номер '
                                        f'<b>+7{number.ctn}</b>.',
            parse_mode=ParseMode.HTML
        )
        index_number = context.user_data['beeline_user'].current_number
        context.user_data['beeline_user'].numbers[index_number].name = new_name

        await account_menu(update, context)
        return ConversationHandler.END


async def select_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target_ctn = re.findall(SELECT_ACC_REGEXP, update.message.text)[0]
    for i, number in enumerate(context.user_data['beeline_user'].numbers):
        if target_ctn == number.ctn:
            context.user_data['beeline_user'].current_number = i
            return await account_menu(update, context)


async def show_rename_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    number = get_current_number(context)
    await update.message.reply_text(f'Введите новое название для номера '
                                    f'<b>+7{number.ctn}</b> вместо текущего '
                                    f'<b>"{number.name}"</b>',
        parse_mode=ParseMode.HTML,
        reply_markup=back_menu()
    )
    return RENAME_ACCOUNT


async def show_add_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_markup = back_menu()
    if 'beeline_user' not in context.user_data or \
            len(context.user_data['beeline_user'].numbers) == 0:
        reply_markup = ReplyKeyboardRemove()

    await update.message.reply_text(AUTH_MSG,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )
    return ADD_ACCOUNT


async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    index_number = context.user_data['beeline_user'].current_number
    old_num = context.user_data['beeline_user'].numbers[index_number]

    count = len(context.user_data['beeline_user'].numbers) - 1
    if count == 0:
        await update.message.reply_text('✔️ Вы успешно удалили последний аккаунт.')
        del context.user_data['beeline_user']
        return await show_add_account(update, context)
    else:
        new_num = context.user_data['beeline_user'].numbers[count - 1]

        context.user_data['beeline_user'].current_number = count - 1
        await update.message.reply_text(f'✔️ Вы успешно удалили аккаунт '
                                        f'\"{old_num.name}\" (+7{old_num.ctn}).',
            parse_mode=ParseMode.HTML
        )
        del context.user_data['beeline_user'].numbers[index_number]
        await account_menu(update, context)
        return ConversationHandler.END


async def account_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'beeline_user' not in context.user_data:
        return await start(update, context)
    number = get_current_number(context)
    text = f'Текущий аккаунт: {number.name} (+7{number.ctn})\n\n' \
           f'Выберите нужное действие:'

    keyboard = [[KeyboardButton('➕ Добавить новый аккаунт')],
                [KeyboardButton('🖊️ Переименовать'), KeyboardButton('❌ Удалить')],
                [KeyboardButton('🔙 В главное меню')]]

    for check_num in context.user_data['beeline_user'].numbers[::-1]:
        if check_num == number:
            continue
        keyboard.insert(0, [KeyboardButton(f'☎️ ️ Выбрать {check_num.name} (+7{check_num.ctn})')])

    keyboard = ReplyKeyboardMarkup(keyboard, is_persistent=False, resize_keyboard=True)

    await update.message.reply_text(text, reply_markup=keyboard)

