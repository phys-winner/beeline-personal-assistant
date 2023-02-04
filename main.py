import logging
import re

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


cnt = ''
password = ''
token = ''

AUTHORIZE, TEST = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    cnt, password = re.findall(r'(\d{10}) (.+)$', update.message.text)[0]
    if 'beeline_user' in context.user_data:
        await update.message.reply_text("Вы уже авторизованы!")
        return

    logger.info("login: %s", update.message.text)
    response = beelineAPI.obtain_token(cnt, password)
    if response == 'ERROR' or response['meta']['status'] != 'OK':
        await update.message.reply_text("Неправильный номер телефона "
                                        "или пароль, попробуйте ещё раз:")
        return AUTHORIZE

    token = response['token']
    new_number = BeelineNumber(cnt, password, token)
    if 'beeline_user' not in context.user_data:
        new_user = BeelineUser(new_number)
        context.user_data['beeline_user'] = new_user
    await update.message.reply_text("Вы успешно авторизовались: " + token)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("cancel")

    return ConversationHandler.END


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

    application.run_polling()
