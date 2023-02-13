import asyncio
import logging
from keyboards import *

from config_secrets import *
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def broadcast(bot):
    for user in white_list:
        logger.info("broadcast: " + str(user))
        await bot.send_message(text='Привет! Добавлена возможность автоматически подключить некоторые полезные услуги!'
                                    'Используйте кнопку "✅ Проверить номер", затем - "⚙️ Подключить услуги".',
                               reply_markup=main_menu_keyboard(),
                               parse_mode=ParseMode.HTML,
                               chat_id=user,
                               disable_notification=True)


if __name__ == '__main__':
    application = ApplicationBuilder().token(tg_bot_token).build()

    loop = asyncio.get_event_loop()
    coroutine = broadcast(application.bot)
    loop.run_until_complete(coroutine)
