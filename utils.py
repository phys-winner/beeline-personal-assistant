from datetime import datetime
import re

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


def str_to_datetime(date_str):
    # '2023-02-05T00:00:00.000Z'
    # '2023-07-17T00:00:00.000+0300'
    return datetime.strptime(date_str[:23], '%Y-%m-%dT%H:%M:%S.%f')
