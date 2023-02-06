import logging
import locale
from beeline_api_errors import *
from keyboards import *
from utils import *
from datetime import datetime, timedelta

from account_menu import *
from beeline_api import BeelineAPI, BeelineNumber, BeelineUser
from config_secrets import *
from telegram import Update, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
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
locale.setlocale(locale.LC_ALL, 'rus')

beelineAPI = BeelineAPI()
use_white_list = len(white_list) > 0

ADD_ACCOUNT, RENAME_ACCOUNT = range(2)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    number = get_current_number(context)
    await update.message.reply_text('Вы находитесь в главном меню.\n'
                                    f'Текущий аккаунт: {number.name} (+7{number.ctn})\n\n'
                                    'Выберите интересующий раздел:',
                                    reply_markup=main_menu_keyboard())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if use_white_list and update.effective_chat.id not in white_list:
        return ConversationHandler.END
    if 'beeline_user' in context.user_data:
        await show_main_menu(update, context)
        return ConversationHandler.END
    user = update.message.from_user
    logger.info("start: %s: %s", user.first_name, update.message.text)
    await update.message.reply_text(
        "Привет! Это неофициальный личный кабинет билайна с расширенными возможностями."
        f"\n\n{AUTH_MSG}",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove()
    )
    return ADD_ACCOUNT


async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if use_white_list and update.effective_chat.id not in white_list:
        return ConversationHandler.END

    ctn, password = re.findall(AUTH_REGEXP, update.message.text)[0]
    if 'beeline_user' in context.user_data:
        for i, number in enumerate(context.user_data['beeline_user'].numbers):
            if ctn == number.ctn:
                await update.message.reply_text(f'✔️ У вас уже есть этот аккаунт.')
                await account_menu(update, context)
                return ConversationHandler.END

    logger.info("login: %s", update.message.text)
    try:
        token = beelineAPI.obtain_token(ctn, password)
    except InvalidResponse as e:
        await update.message.reply_text("Произошла проблема при авторизации, попробуйте ещё раз.\n\n" + e.value)
        return ADD_ACCOUNT
    except StatusNotOK as e:
        await update.message.reply_text("Неверный номер телефона или пароль, попробуйте ещё раз.")
        return ADD_ACCOUNT

    if 'beeline_user' in context.user_data:
        new_number = BeelineNumber(ctn, password, token, '')
        new_index = len(context.user_data['beeline_user'].numbers)
        context.user_data['beeline_user'].numbers.append(new_number)
        context.user_data['beeline_user'].current_number = new_index

        # именуем номера как тарифы
        response = call_func(context, beelineAPI.info_pricePlan)
        logger.info("get_pricePlan: %s: %s", update.message.from_user.first_name, response)
        plan = response['pricePlanInfo']

        context.user_data['beeline_user'].numbers[new_index].name = plan['entityName']
    else:
        new_number = BeelineNumber(ctn, password, token, "Основной")
        new_user = BeelineUser(new_number)
        context.user_data['beeline_user'] = new_user
    await show_main_menu(update, context)
    return ConversationHandler.END


async def show_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'beeline_user' not in context.user_data:
        return await start(update, context)

    wait_msg = await update.message.reply_text(PLEASE_WAIT_MSG)
    response = call_func(context, beelineAPI.info_prepaidBalance)
    logger.info("info_prepaidBalance: %s: %s", update.message.from_user.first_name, response)

    index_number = context.user_data['beeline_user'].current_number
    current_ctn = context.user_data['beeline_user'].numbers[index_number].ctn

    billing_date_str = ''
    result = f'📱 Номер телефона: +7{current_ctn}\n'
    result += f'💵 Текущий баланс: {"{0:.2f}".format(response["balance"]).rstrip("0").rstrip(".")} рублей\n'
    if 'nextBillingDate' in response \
            and response['nextBillingDate'] is not None:
        date_reset = str_to_datetime(response["nextBillingDate"], "%Y-%m-%d")
        billing_date_str = str(date_reset.strftime('%d %B %Y'))
        result += f'Дата следующего списания: {billing_date_str.lower()} года\n'
    result += '\n'

    response = call_func(context, beelineAPI.info_accumulators)
    logger.info("info_accumulators: %s: %s", update.message.from_user.first_name, response)

    # пропускаем 'Условия использования интернета в международном роуминге'
    accumulators = [n for n in response['accumulators'] if n['soc'] != 'ROAMGPRS']

    response = call_func(context, beelineAPI.info_prepaidAddBalance)
    logger.info("info_prepaidAddBalance: %s: %s", update.message.from_user.first_name, response)

    balances = []
    if 'balanceTime' in response and response['balanceTime'] is not None:
        balances.extend([n for n in response['balanceTime']])
    if 'balanceSMS' in response and response['balanceSMS'] is not None:
        balances.extend([n for n in response['balanceSMS']])

    def format_unit_count(counter):
        unit = counter['unit']
        #
        rest = None
        if 'value' in counter:
            rest = counter['value']
        else:
            rest = counter['rest']

        size = None
        if 'size' in counter:
            size = counter['size']
        if unit == 'KBYTE':
            result = format_bytes(rest, unit)
            if size is not None and size >= rest:
                result += ' из ' + format_bytes(size, unit)
            return result
        elif unit == 'SECONDS':
            result = str(int(rest // 60))
            if size is not None and size >= rest:
                result += ' из ' + str(size // 60)
            return result + " минут"
        elif unit == 'SMS':
            result = str(int(rest))
            if size is not None and size >= rest:
                result += ' из ' + str(rest)
            return result + " смс"

        result = str(rest)
        if size is not None and size >= rest:
            result += ' из ' + str(rest)
        return result

    def format_counter(counter):
        result = ''
        is_inet_unlim = 'soc' in counter \
                        and counter['soc'] == 'SBL4P2_3' \
                        and counter['unit'] == 'KBYTE'
        if is_inet_unlim:
            result = f'♾️ безлимит'
        elif 'rest' in counter or 'value' in counter:
            result = format_unit_count(counter)

        if counter['unit'] == 'KBYTE':
            result = f'🌎 Интернет: {result}\n'
        elif counter['unit'] == 'SECONDS':
            result = f'📞 Минуты: {result}\n'
        elif counter['unit'] == 'SMS':
            result = f'✉️ SMS: {result}\n'
        else:
            result = f'🔢 Осталось: {result}\n'

        if 'isSpeedDown' in counter and counter['isSpeedDown']:
            result = '📉 ' + result
        if 'isSpeedUp' in counter and counter['isSpeedUp']:
            result = '📈 ' + result
        if 'dateResetPacket' in counter and not is_inet_unlim:
            date_reset = str_to_datetime(counter['dateResetPacket'])
            date_str = str(date_reset.strftime('%d %B %Y'))
            if date_str != billing_date_str:
                result += f'Дата сброса пакета: {date_str.lower()} года\n'
        #if 'sdbShare' in accumulator and accumulator['sdbShare']:
            #result += '👪 '
        #result += f'Источник: {accumulator["socName"]}\n'
        #result += f'Действует: {accumulator["accName"]}'

        return result

    if len(accumulators) > 0 or len(balances) > 0:
        result += '📜 Остатки пакетов:\n'
    for accumulator in accumulators:
        result += format_counter(accumulator)
    for balance in balances:
        result += format_counter(balance)

    await wait_msg.edit_text(result)


async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'beeline_user' not in context.user_data:
        await start(update, context)
        return

    wait_msg = await update.message.reply_text(PLEASE_WAIT_MSG)
    response = call_func(context, beelineAPI.info_serviceList)
    logger.info("info_serviceList: %s: %s", update.message.from_user.first_name, response)

    def sort_by_name(service):
        return service['entityName']

    services = sorted(response['services'], key=sort_by_name)

    def format_service_line(service):
        if service['removeInd'] == 'Y':
            result = '🟢'
        else:
            result = '🔴'

        if 'rcRate' in service and service['rcRate'] > 0:
            result += f'💸️ за {service["rcRate"]} рублей'
            if 'rcRatePeriodText' in service and service['rcRatePeriodText'] is not None:
                result += f' {service["rcRatePeriodText"]}'
            result += '\n'

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

    await wait_msg.edit_text(result)


async def check_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'beeline_user' not in context.user_data:
        return await start(update, context)

    # услуги - наличие 'плохих' и платных, совет по подключению полезных
    wait_msg = await update.message.reply_text(PLEASE_WAIT_MSG)
    response = call_func(context, beelineAPI.info_serviceList)
    logger.info("info_serviceList: %s: %s", update.message.from_user.first_name, response)
    result = ''

    services = {}
    for i in response['services']:
        services[i['name']] = {
            'entityName': i['entityName']
        }
        if 'rcRate' in i:
            services[i['name']]['rcRate'] = int(i['rcRate'])
        else:
            services[i['name']]['rcRate'] = 0
        if 'rcRatePeriodText' in i:
            services[i['name']]['rcRatePeriodText'] = i['rcRatePeriodText']

    for soc, description in services.items():
        if soc in BAD_SERVICES:
            result += f'❌👎️ Вредная услуга: {description["entityName"]}\n'
        if description["rcRate"] > 0:
            result += f'❌💸️ Платная услуга: {description["entityName"]} ' \
                      f'за <u>{description["rcRate"]} рублей'
            if description['rcRatePeriodText'] is not None:
                result += f' {description["rcRatePeriodText"]}'
            result += f'</u>\n'

    if result == '':
        result = '✅️ Вредных или платных услуг не обнаружено!\n'

    test_services = GOOD_SERVICES.copy()
    for soc, description in services.items():
        if soc in test_services.keys():
            del test_services[soc]

    if len(test_services) > 0:
        result += '💡 Советую подключить данные услуги:\n'
        for service in test_services.values():
            result += '⚬  ' + service['entityName']
            if 'http' in service['how_to']:
                result += f'\n🌎 <a href="{service["how_to"]}">Страница услуги в билайне</a>'
            else:
                result += f'\n📞 <code>{service["how_to"]}</code>'
            result += '\n\n'

    # подписки - наличие
    response = call_func(context, beelineAPI.info_subscriptions)
    logger.info("info_subscriptions: %s: %s", update.message.from_user.first_name, response)

    subscriptions = response['subscriptions']
    if len(subscriptions) == 0:
        result += '✅️ Подписки не найдены!\n'
    else:
        result += '❌️ Обнаружены подписки:\n'
        for subscription in subscriptions:
            result += subscription['name'] + '\n'

    # счётчики - наличие флага замедления
    response = call_func(context, beelineAPI.info_accumulators)
    logger.info("get_accumulators: %s: %s", update.message.from_user.first_name, response)

    accumulators = [n for n in response['accumulators'] if n['soc'] != 'ROAMGPRS']
    is_slowed = False
    for accumulator in accumulators:
        if 'isSpeedDown' in accumulator and accumulator['isSpeedDown']:
            if accumulator['unit'] == 'KBYTE':
                result += '❌️ Счётчик интернета с уменьшенной скоростью\n'
            else:
                result += '❌️ Имеется счётчик с уменьшенной скоростью\n'

    if not is_slowed:
        result += '✅️ Замедленные счётчики не найдены!\n'

    await wait_msg.edit_text(result, parse_mode=ParseMode.HTML)


async def get_bill_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'beeline_user' not in context.user_data:
        return await start(update, context)

    wait_msg = await update.message.reply_text(PLEASE_WAIT_MSG)

    period_end = datetime.now()
    period_start = period_end - timedelta(hours=30*24)

    response = call_func(context, beelineAPI.info_onlineBillDetail, period_start, period_end)
    logger.info("info_onlineBillDetail: %s: %s", update.message.from_user.first_name, response)

    call_details = response['callDetails']
    today = period_end.replace(hour=0, minute=0, second=0, microsecond=0)
    current_week = period_end - timedelta(weeks=1)
    today_details = {}
    week_details = {}
    month_details = {}

    def add_value(date_dict, detail):
        bill_name = 'Интернет'
        if 'number' in detail and detail['number'] != '':
            bill_name += f' на +{detail["number"]}'
        if bill_name in date_dict.keys():
            date_dict[bill_name] += detail['trafficVolume']
        else:
            date_dict[bill_name] = detail['trafficVolume']

    for detail in call_details:
        if 'trafficUnit' not in detail or detail['trafficUnit'] != 'KBYTE':
            continue
        if 'dateTime' not in detail or 'trafficVolume' not in detail:
            continue
        date = str_to_datetime(detail['dateTime'])
        add_value(month_details, detail)
        if date >= today:
            add_value(today_details, detail)
        if date >= current_week:
            add_value(week_details, detail)

    def append_details(date_dict):
        result = ''
        if len(date_dict) == 1:
            for name, traffic in date_dict.items():
                if name == 'Интернет':
                    result += f'<b>{format_bytes(traffic, "KBYTE")}</b>'
                else:
                    result += f'<b>{format_bytes(traffic, "KBYTE")}</b> ({name.lower()})'
        else:
            for name, traffic in date_dict.items():
                result += f'\n⚬  {name}: <b>{format_bytes(traffic, "KBYTE")}</b>'
            result += '\n'
        return result + '\n'

    period_start_str = str(period_start.strftime('%d %B %Y')).lower()
    period_end_str = str(period_end.strftime('%d %B %Y')).lower()
    result = f'🌎 <b>Потребление интернета</b>\n' \
             f'Период: c {period_start_str} г. по {period_end_str} г.\n\n'

    if len(today_details) == 0:
        result += '<u>сегодня с 00:00</u> интернет не был использован\n'
    else:
        result += f'За сегодня (с 00:00): {append_details(today_details)}'

    if len(week_details) == 0:
        result += '<u>за неделю</u> интернет не был использован\n'
    else:
        result += f'За неделю: {append_details(week_details)}'

    if len(month_details) == 0:
        result += '<u>за месяц</u> интернет не был использован\n'
    else:
        result += f'За месяц: {append_details(month_details)}'
        sum_traffic = sum(month_details.values())
        result += f'<b>Всего было потрачено {format_bytes(sum_traffic, "KBYTE")}</b>.'

    await wait_msg.edit_text(result, parse_mode=ParseMode.HTML)


async def get_price_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'beeline_user' not in context.user_data:
        return await start(update, context)

    wait_msg = await update.message.reply_text(PLEASE_WAIT_MSG)
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

    await wait_msg.edit_text(result)


if __name__ == '__main__':
    persistence = PicklePersistence(filepath="beeline_data.pickle", update_interval=5)
    application = ApplicationBuilder().token(tg_bot_token).persistence(persistence).build()

    auth_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("➕ Добавить новый аккаунт"), show_add_account),
            MessageHandler(filters.Regex("❌ Удалить"), delete_account)
        ],
        states={
            ADD_ACCOUNT: [MessageHandler(filters.Regex(AUTH_REGEXP), authorize)],
        },
        fallbacks=[
            MessageHandler(filters.Regex("🔙 Назад"), account_menu),
            MessageHandler(filters.TEXT & ~filters.COMMAND, start)
        ],
    )

    rename_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("🖊️ Переименовать"), show_rename_account)
        ],
        states={
            RENAME_ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_rename_account)],
        },
        fallbacks=[MessageHandler(filters.Regex("🔙 Назад"), account_menu)],
    )

    application.add_handler(auth_handler)
    application.add_handler(rename_handler)

    application.add_handler(MessageHandler(filters.Regex('📱 Основная информация'), show_info))
    application.add_handler(MessageHandler(filters.Regex('✅ Проверить номер'), check_number))

    application.add_handler(MessageHandler(filters.Regex('📖 Тариф'), get_price_plan))
    application.add_handler(MessageHandler(filters.Regex('🔎 Услуги'), show_services))
    application.add_handler(MessageHandler(filters.Regex('📙 Детализация'), get_bill_detail))

    application.add_handler(MessageHandler(filters.Regex('⚙️ Настройки'), account_menu))

    application.add_handler(MessageHandler(filters.Regex(SELECT_ACC_REGEXP), select_account))

    application.add_handler(MessageHandler(filters.Regex('🔙 В главное меню'), show_main_menu))
    application.run_polling()
