import logging
import re

from beeline_api import BeelineAPI
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

    logger.info("login: %s", update.message.text)
    responce = beelineAPI.obtain_token(cnt, password)
    if responce == 'ERROR' or responce['meta']['status'] != 'OK':
        await update.message.reply_text("Неправильный номер телефона "
                                        "или пароль, попробуйте ещё раз:")
        return AUTHORIZE

    await update.message.reply_text("Вы успешно авторизовались: " + responce['token'])

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("cancel")

    return ConversationHandler.END

if __name__ == '__main__':
    application = ApplicationBuilder().token(tg_bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AUTHORIZE: [MessageHandler(
                filters.Regex(r'(\d{10}) (.+)$'), authorize)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()
