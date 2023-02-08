from datetime import datetime
import re

from telegram.ext import ContextTypes

from beeline_api import BeelineNumber

BAD_SERVICES = ['P2PTOR_NO', 'INFO300GB', 'SPEED_512', 'PRIOR3', 'SPDKCH']
GOOD_SERVICES = {
'USSD_BAN': {'entityName': 'Запрет USSD хвостов; отключение рекламы при USSD запросах, например, в *102#', 'how_to': '067405541'},
'MBCSTOPE': {'entityName': 'Отказ от ММС-рассылок', 'how_to': '06740451'},
'PSMSADOFF': {'entityName': 'Отказ от смс-рассылок', 'how_to': '067401231'},
'NO_PROMO': {'entityName': 'Запрет промо акций', 'how_to': '06740431'},
'AUTOSP_BL': {'entityName': 'Запрет автопродления интернета (необходимо отключить перед подключением Автопродления скорости)', 'how_to': '*115*230#'},
'CRMINTBAR': {'entityName': 'Запрет интернета в сетях др. операторов РФ', 'how_to': '*110*9390#'},
'ROAMBAR_P': {'entityName': 'Запрет автоматического международного роуминга', 'how_to': '*110*0991#'},
'CPA_SAS': {'entityName': 'Отдельный лицевой счёт для оплаты услуг провайдеров (платные подписки не будут тратить денег)', 'how_to': 'https://beeline.ru/customers/products/mobile/services/cutdetails/CPA_SAS/'}
}

PLEASE_WAIT_MSG = '⌛ Пожалуйста, подождите...'
AUTH_MSG = 'Для авторизации отправьте \n' \
           '📱<b>номер телефона</b> и  🔒<b>пароль</b> через пробел.'

SELECT_ACC_REGEXP = r'Выбрать (.+) \(\+7([\d*]{10})\)$'
AUTH_REGEXP = r'(\d{10}) (.+)$'

IS_DEMO_MODE = False


def replace_demo_ctn(ctn):
    if IS_DEMO_MODE:
        return '905*******'
    return ctn


def format_bytes(size, unit):
    # 2**10 = 1024
    power = 2**10
    n = 0
    if unit == 'KBYTE':
        n = 1
    power_labels = {0: '', 1: 'К', 2: 'М', 3: 'Г', 4: 'Т'}
    while size > power:
        size /= power
        n += 1
    #return size, power_labels[n] + 'байт'
    return f'{size:.1f} {power_labels[n] + "Б"}'


def str_to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S.%f'):
    # '2023-02-05T00:00:00.000Z'
    # '2023-07-17T00:00:00.000+0300'
    return datetime.strptime(date_str[:23], format)


def get_current_index(context: ContextTypes.DEFAULT_TYPE) -> BeelineNumber:
    return context.user_data['beeline_user'].current_number


def get_current_number(context: ContextTypes.DEFAULT_TYPE) -> BeelineNumber:
    index_number = get_current_index(context)
    return context.user_data['beeline_user'].numbers[index_number]


def update_current_number(context: ContextTypes.DEFAULT_TYPE, new_number: BeelineNumber):
    index_number = get_current_index(context)
    context.user_data['beeline_user'].numbers[index_number] = new_number


def call_func(context: ContextTypes.DEFAULT_TYPE, func, *arg):
    response, new_number = func(get_current_number(context), *arg)
    update_current_number(context, new_number)

    return response
