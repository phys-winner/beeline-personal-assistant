from datetime import datetime
import re

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


def format_bytes(size, unit):
    # 2**10 = 1024
    power = 2**10
    n = 0
    if unit == 'KBYTE':
        n = 1
    power_labels = {0: '', 1: 'кило', 2: 'мега', 3: 'гига', 4: 'тера'}
    while size > power:
        size /= power
        n += 1
    #return size, power_labels[n] + 'байт'
    return f'{size:.1f} {power_labels[n] + "байт"}'


def str_to_datetime(date_str, format='%Y-%m-%dT%H:%M:%S.%f'):
    # '2023-02-05T00:00:00.000Z'
    # '2023-07-17T00:00:00.000+0300'
    return datetime.strptime(date_str[:23], format)
