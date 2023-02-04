import logging
import re
from beeline_api_errors import *

from beeline_api import BeelineAPI, BeelineNumber, BeelineUser
from config_secrets import *
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

beelineAPI = BeelineAPI()
use_white_list = len(white_list) > 0
AUTHORIZE, TEST = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'beeline_user' in context.user_data:
        await get_services(update, context)
        return
    user = update.message.from_user
    logger.info("start: %s: %s", user.first_name, update.message.text)
    if use_white_list and update.effective_chat.id not in white_list:
        return
    await update.message.reply_text(
        "Привет\! Это неофициальный личный кабинет Билайна с расширенными возможностями\.  "
        "\n  "
        "\n"
        "Чтобы начать его использовать, пришлите мне  \n"
        "📱*номер телефона* и  🔒*пароль* через пробел\.",
        parse_mode=ParseMode.MARKDOWN_V2
    )

    return AUTHORIZE


async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ctn, password = re.findall(r'(\d{10}) (.+)$', update.message.text)[0]
    if 'beeline_user' in context.user_data:
        await update.message.reply_text("Вы уже авторизованы!")
        await get_services(update, context)
        return

    logger.info("login: %s", update.message.text)
    try:
        token = beelineAPI.obtain_token(ctn, password)
    except InvalidResponse as e:
        await update.message.reply_text("Произошла проблема при авторизации, попробуйте ещё раз.\n\n" + e.value)
        return AUTHORIZE
    except StatusNotOK as e:
        await update.message.reply_text("Неверный номер телефона или пароль, попробуйте ещё раз.")
        return AUTHORIZE

    new_number = BeelineNumber(ctn, password, token, "Основной")
    if 'beeline_user' not in context.user_data:
        new_user = BeelineUser(new_number)
        context.user_data['beeline_user'] = new_user
    await get_services(update, context)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("cancel")

    return ConversationHandler.END


async def get_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'beeline_user' not in context.user_data:
        return

    index_number = context.user_data['beeline_user'].current_number

    response, new_number = beelineAPI.info_serviceList(context.user_data['beeline_user'].numbers[index_number])
    logger.info("services: %s: %s", update.message.from_user.first_name, response)

    context.user_data['beeline_user'].numbers[index_number] = new_number

    def sort_by_name(service):
        return service['entityName']

    services = sorted(response['services'], key=sort_by_name)

    def format_service_line(service):
        result = ''
        if service['removeInd'] == 'Y':
            result += '🟢'
        else:
            result += '🔴'
        result += f' {service["entityName"].replace("  ", " ")}'
        if service['expDate'] is not None:
            result += f' (действует до {service["expDate"]})'
        result += f'\n'
        if service["entityDesc"] is not None:
            result += service["entityDesc"] + f'\n'
        return result + f'\n'

    result = 'Видимые услуги:\n'
    for service in [n for n in services if n['viewInd'] == 'Y']:
        result += format_service_line(service)

    result += '\nСкрытые услуги:\n'
    for service in [n for n in services if n['viewInd'] != 'Y']:
        result += format_service_line(service)

    await update.message.reply_text(
        result
    )


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        repr(context.user_data['beeline_user'])
    )

if __name__ == '__main__':
    persistence = PicklePersistence(filepath="beeline_data.pickle", update_interval=5)
    application = ApplicationBuilder().token(tg_bot_token).persistence(persistence).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AUTHORIZE: [MessageHandler(
                filters.Regex(r'(\d{10}) (.+)$'), authorize)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="main_conversation",
        persistent=True
    )

    application.add_handler(conv_handler)

    show_data_handler = CommandHandler("show_data", show_data)
    application.add_handler(show_data_handler)

    get_services_handler = CommandHandler("get_services", get_services)
    application.add_handler(get_services_handler)

    application.run_polling()
