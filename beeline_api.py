import requests
import json


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
             '(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'

# entry point from repo:
# https://github.com/arthurvaverko-kaltura/beeline-usss-mock/
BASE = "https://my.beeline.ru/"
API_1_0 = BASE + "api/1.0/"
AUTH = API_1_0 + 'auth'

INFO = API_1_0 + 'info/'
SERVICELIST = INFO + 'serviceList'

class BeelineUser:
    """Класс с информацией об абоненте"""

    def __init__(self, number):
        self.current_number = 0
        self.numbers = [number]

    def __repr__(self):
        return f'BeelineUser: current_index={self.current_number},' \
               f'numbers=[{";".join([repr(num) for num in self.numbers])}]'


class BeelineNumber:
    """Класс с информацией о номере телефона"""

    def __init__(self, ctn, password, token):
        self.ctn = ctn
        self.password = password
        self.token = token

    def __repr__(self):
        return f'BeelineNumber: ctn={self.ctn},password={self.password},' \
               f'token={self.token}'


class BeelineAPI:
    """Класс неофициального API Beeline.ru"""

    def __init__(self):
        self.headers = {'User-Agent': USER_AGENT}

    def __get_request__(self, url, params=None, number=None):
        cookies = None
        if number is not None:
            cookies = {'token': number.token}
        return requests.get(url,
                            params=params,
                            cookies=cookies,
                            headers=self.headers)

    def obtain_token(self, ctn: str, password: str):
        params = {
            'login': ctn,
            'password': password
        }
        r = self.__get_request__(url=AUTH, params=params)
        if not r.ok:
            return 'ERROR'

        # {"meta":{"status":"OK","code":20000,"message":null},
        # "token":"0574C7963E64F047122256CAEA543538"}
        # {"meta":{"status":"ERROR","code":20002,"message":"AUTH_ERROR"}}
        # {"meta":{"status":"ERROR","code":20002,"message":"AUTH_ERROR (weak
        # password)"}}
        # {"meta":{"status":"ERROR","code":20014,
        # "message":"AUTH_USER_BLOCKED_ERROR"}}
        # {"meta":{"status":"ERROR","code":50000,"message":"SYSTEM_ERROR:
        # null"}}
        return json.loads(r.text)


    def info_serviceList(self, number: BeelineNumber):
        # hiddenService - Индикатор отображения данных по скрытым услугам.
        # Значение по умолчанию - false, скрытые услуги не возвращаются
        params = {'hiddenService': 'true', 'ctn': number.ctn}
        r = self.__get_request__(url=SERVICELIST, params=params, number=number)
        if not r.ok:
            return 'ERROR'

        # {"meta":{"status":"OK","code":20000,"message":null},
        # "token":"0574C7963E64F047122256CAEA543538"}
        # {"meta":{"status":"ERROR","code":20002,"message":"AUTH_ERROR"}}
        # {"meta":{"status":"ERROR","code":20002,"message":"AUTH_ERROR (weak
        # password)"}}
        # {"meta":{"status":"ERROR","code":20014,
        # "message":"AUTH_USER_BLOCKED_ERROR"}}
        # {"meta":{"status":"ERROR","code":50000,"message":"SYSTEM_ERROR:
        # null"}}
        return json.loads(r.text)


