import logging
import re
import locale
from beeline_api_errors import *
from keyboards import *
from utils import *

from beeline_api import BeelineAPI, BeelineNumber, BeelineUser
from config_secrets import *
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
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
locale.setlocale(locale.LC_ALL, 'rus')

beelineAPI = BeelineAPI()
use_white_list = len(white_list) > 0
AUTHORIZE, TEST = range(2)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Вы находитесь в главном меню.\n\n'
                                    'Выберите необходимый раздел:',
                                    reply_markup=main_menu_keyboard())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'beeline_user' in context.user_data:
        await show_main_menu(update, context)
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


def call_func(context: ContextTypes.DEFAULT_TYPE, func):
    index_number = context.user_data['beeline_user'].current_number
    response, new_number = func(context.user_data['beeline_user'].numbers[index_number])

    context.user_data['beeline_user'].numbers[index_number] = new_number
    return response


async def get_accumulators(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'beeline_user' not in context.user_data:
        return

    response = call_func(context, beelineAPI.info_accumulators)
    logger.info("get_accumulators: %s: %s", update.message.from_user.first_name, response)

    def format_unit_count(accumulator):
        unit = accumulator['unit']
        rest = accumulator['rest']
        size = None
        if 'size' in accumulator:
            size = accumulator['size']
        if unit == 'KBYTE':
            result = format_bytes(rest, unit)
            if size is not None and size >= rest:
                result += ' из ' + format_bytes(size, unit)
            return result
        elif unit == 'SECONDS':
            result = str(rest // 60)
            if size is not None and size >= rest:
                result += ' из ' + str(size // 60)
            return result + " минут"
        elif unit == 'SMS':
            result = str(rest)
            if size is not None and size >= rest:
                result += ' из ' + str(rest)
            return result + " смс"

        result = str(rest)
        if size is not None and size >= rest:
            result += ' из ' + str(rest)
        return result

    def format_accumulator(accumulator):
        result = ''
        is_inet_unlim = 'soc' in accumulator \
                and accumulator['soc'] == 'SBL4P2_3' \
                and accumulator['unit'] == 'KBYTE'
        if is_inet_unlim:
            result = f'♾️ безлимит'
        elif 'rest' in accumulator:
            result = format_unit_count(accumulator)

        if accumulator['unit'] == 'KBYTE':
            result = f'🌎 Интернет: {result}\n'
        elif accumulator['unit'] == 'SECONDS':
            result = f'📞 Минуты: {result}\n'
        elif accumulator['unit'] == 'SMS':
            result = f'✉️ SMS: {result}\n'
        else:
            result = f'🔢 Осталось: {result}\n'

        if 'dateResetPacket' in accumulator and not is_inet_unlim:
            date_reset = str_to_datetime(accumulator['dateResetPacket'])
            date_str = str(date_reset.strftime('%d %B %Y'))
            result += f'📅 Дата сброса пакета: {date_str.lower()} года\n'
        if 'isSpeedDown' in accumulator and accumulator['isSpeedDown']:
            result += '📉 - счётчик имеет флаг уменьшенной скорости\n'
        if 'isSpeedUp' in accumulator and accumulator['isSpeedUp']:
            result += '📈 - счётчик имеет флаг повышенной скорости\n'
        if 'sdbShare' in accumulator and accumulator['sdbShare']:
            result += '👪 '
        #result += f'Источник: {accumulator["socName"]}\n'
        result += f'Действует: {accumulator["accName"]}'

        return result + f'\n\n'

    # пропускаем 'Условия использования интернета в международном роуминге'
    accumulators = [n for n in response['accumulators'] if n['soc'] != 'ROAMGPRS']

    if len(accumulators) == 0:
        result = 'У вас нет счётчиков для отображения'
    else:
        result = 'Список счётчиков:\n'
        for accumulator in accumulators:
            if 'sdbShare' in accumulator and accumulator['sdbShare']:
                result = 'Обозначение: 👪 - используется в семье\n\n' + result
                break
        for accumulator in accumulators:
            result += format_accumulator(accumulator)

    await update.message.reply_text(
        result
    )


async def get_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'beeline_user' not in context.user_data:
        return

    response = call_func(context, beelineAPI.info_serviceList)
    logger.info("get_services: %s: %s", update.message.from_user.first_name, response)

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
            exp_date = str_to_datetime(service['expDate'])
            date_str = str(exp_date.strftime('%d %B %Y'))
            result += f' (📅 действует до {date_str.lower()} года)'
        if service["entityDesc"] is not None \
                and service["entityDesc"] != service["entityName"]:
            result += f'\n{service["entityDesc"].replace("  ", " ")}\n'
        return result + f'\n'

    visible_services = [n for n in services if n['viewInd'] == 'Y']
    hidden_services = [n for n in services if n['viewInd'] != 'Y']

    if len(visible_services) == 0 and len(hidden_services) == 0:
        result = 'У вас нет подключённых услуг.'
    else:
        result = 'Обозначения:' \
                 '\n🟢 - услугу можно отключить самостоятельно' \
                 '\n🔴 - услугу нельзя отключить самостоятельно\n\n'
        if len(visible_services) == 0:
            result += 'У вас отсутствуют видимые услуги.\n'
        else:
            result += '👀👀 Видимые услуги: 👀👀\n'
            for service in visible_services:
                result += format_service_line(service)

        if len(hidden_services) == 0:
            result += '\nУ вас отсутствуют скрытые услуги.'
        else:
            result += '\n👻👻 Скрытые услуги: 👻👻\n'
            for service in hidden_services:
                result += format_service_line(service)

    await update.message.reply_text(
        result
    )


async def get_pricePlan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'beeline_user' not in context.user_data:
        return

    response = call_func(context, beelineAPI.info_pricePlan)
    logger.info("get_pricePlan: %s: %s", update.message.from_user.first_name, response)

    price_plan = response['pricePlanInfo']
    result = f"""Название: {price_plan['entityName']}
{price_plan['entityDesc']}

"""
    if 'rcRatePeriodText' in price_plan and int(price_plan['rcRate']) > 0:
        result += f"💵 Абонентская плата: {int(price_plan['rcRate'])} {price_plan['rcRatePeriodText']}\n"
    else:
        result += f"🤑 Без абонентской платы\n"
    if price_plan['expDate'] is not None:
        exp_date = str_to_datetime(price_plan['expDate'])
        date_str = str(exp_date.strftime('%d %B %Y'))
        result += f'📅 Действует до {date_str.lower()} года)\n'

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

    application.add_handler(MessageHandler(filters.Regex('^Хранящиеся данные$'), show_data))
    application.add_handler(MessageHandler(filters.Regex('^Услуги$'), get_services))
    application.add_handler(MessageHandler(filters.Regex('^Тариф$'), get_pricePlan))
    application.add_handler(MessageHandler(filters.Regex('^Счётчики$'), get_accumulators))

    application.run_polling()
