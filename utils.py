from datetime import datetime
from telegram.ext import ContextTypes
from beeline_api import BeelineNumber


class ServiceDescription:
    def __init__(self, soc, name, how_to):
        self.soc = soc
        self.name = name
        self.how_to = how_to

    def __eq__(self, soc: str):
        return self.soc == soc

    def __repr__(self) -> str:
        return f'ServiceDescription: soc={self.soc},' \
               f'name={self.name},how_to={self.how_to}'

    def can_activate(self):
        return not self.how_to.startswith('06')


BAD_SERVICES = ['P2PTOR_NO', 'INFO300GB', 'SPEED_512', 'PRIOR3', 'SPDKCH']
GOOD_SERVICES = [
    ServiceDescription('USSD_BAN', 'Запрет USSD хвостов', '067405541'),
    ServiceDescription('MBCSTOPE', 'Отказ от ММС-рассылок', '06740451'),
    ServiceDescription('PSMSADOFF', 'Отказ от смс-рассылок', '067401231'),
    ServiceDescription('NO_PROMO', 'Запрет промо акций', '06740431'),
    ServiceDescription('AUTOSP_BL', 'Запрет автопродления интернета (необходимо отключить перед подключением Автопродления скорости)', '*115*230#'),
    ServiceDescription('CRMINTBAR', 'Запрет интернета в сетях др. операторов РФ', '*110*9390#'),
    ServiceDescription('ROAMBAR_P', 'Запрет автоматического международного роуминга', '*110*0991#'),
    ServiceDescription('CPA_SAS', 'Отдельный лицевой счёт для оплаты услуг провайдеров (платные подписки не будут тратить денег)', 'https://beeline.ru/customers/products/mobile/services/cutdetails/CPA_SAS/')
]

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
