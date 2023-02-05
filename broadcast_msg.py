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
        logger.info("broadcat: %s" + user)
        await bot.send_message(text='Привет! Мы добавили возможность смотреть '
                                    '<b>🌎 потребление интернета</b> за '
                                    'сегодня, неделю и месяц! Попробуйте, нажав '
                                    'на <b>"📙 Детализация"</b>!\n\n'
                                    'Также теперь при показе основной '
                                    'информации '
                                    'показывается текущий номер телефона, и '
                                    'исправлено отображение баланса, если у '
                                    'вас '
                                    '0 рублей на счету.',
                               reply_markup=main_menu_keyboard(),
                               parse_mode=ParseMode.HTML,
                               chat_id=user)


if __name__ == '__main__':
    application = ApplicationBuilder().token(tg_bot_token).build()

    loop = asyncio.get_event_loop()
    coroutine = broadcast(application.bot)
    loop.run_until_complete(coroutine)
