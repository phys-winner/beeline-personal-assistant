import requests
import json
from ratelimiter import RateLimiter
from beeline_api_errors import *
from datetime import datetime

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
             '(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'

# entry point from repo:
# https://github.com/arthurvaverko-kaltura/beeline-usss-mock/
BASE = "https://my.beeline.ru/"
API_1_0 = BASE + "api/1.0/"
AUTH = API_1_0 + 'auth'

INFO = API_1_0 + 'info/'
SERVICELIST = INFO + 'serviceList'
ACCUMULATORS = INFO + 'accumulators'
PRICEPLAN = INFO + 'pricePlan'
SUBSCRIPTIONS = INFO + 'subscriptions'
PROMISED_BALANCE = INFO + 'availablePromisedPayment'
PREPAID_BALANCE = INFO + 'prepaidBalance'
PREPAID_ADD_BALANCE = INFO + 'prepaidAddBalance'
BILL_DETAIL = INFO + 'onlineBillDetail'


class BeelineUser:
    """Класс с информацией об абоненте"""

    def __init__(self, number):
        self.current_number = 0
        self.numbers = [number]

    def __repr__(self) -> str:
        return f'BeelineUser: current_index={self.current_number},' \
               f'numbers=[{";".join([repr(num) for num in self.numbers])}]'

    def __eq__(self, o) -> bool:
        return self.current_number == o.current_number and \
            self.numbers == o.numbers


class BeelineNumber:
    """Класс с информацией о номере телефона"""

    def __init__(self, ctn, password, token, name):
        self.ctn = ctn
        self.password = password
        self.token = token
        self.token_v2 = ''
        self.name = name
        self.rec_services = []
        self.version = 2

    def __eq__(self, o) -> bool:
        return self.version == o.version and \
            self.ctn == o.ctn and \
            self.password == o.password and \
            self.token == o.token and \
            self.token_v2 == o.token_v2 and \
            self.name == o.name and \
            self.rec_services == o.rec_services

    def __repr__(self) -> str:
        return f'BeelineNumber: ctn={self.ctn},password={self.password},' \
               f'token={self.token},token_v2={self.token_v2},name={self.name},' \
               f'rec_services={self.rec_services}'


class BeelineAPI:
    """Класс неофициального API Beeline.ru"""

    def __init__(self):
        self.headers = {'User-Agent': USER_AGENT}

    @RateLimiter(max_calls=5, period=1)
    def __get_request__(self, url, params=None, beeline_number=None):
        cookies = {}
        if beeline_number is not None and url != AUTH:
            cookies['token'] = beeline_number.token
            if params is None:
                params = {'ctn': beeline_number.ctn}
            else:
                params['ctn'] = beeline_number.ctn
        r = requests.get(url,
                            params=params,
                            cookies=cookies,
                            headers=self.headers)
        if not r.ok:
            raise InvalidResponse(f'{r.status_code} (GET): {url}', r)

        response = json.loads(r.text)
        if response['meta']['status'] == 'ERROR' and \
                'TOKEN_' in response['meta']['message'] \
                and url != AUTH:
            # слетел токен, актуализируем его
            beeline_number.token = self.obtain_token(beeline_number.ctn,
                                                     beeline_number.password)
            return self.__get_request__(url, params, beeline_number)

        if response['meta']['status'] != 'OK':
            raise StatusNotOK(f'{url} - {r.text}')
        return response, beeline_number

    def obtain_token(self, ctn: str, password: str):
        params = {
            'login': ctn,
            'password': password
        }
        response, _ = self.__get_request__(url=AUTH, params=params)

        # {"meta":{"status":"OK","code":20000,"message":null},
        # "token":"0574C7963E64F047122256CAEA543538"}
        # {"meta":{"status":"ERROR","code":20002,"message":"AUTH_ERROR"}}
        # {"meta":{"status":"ERROR","code":20002,"message":"AUTH_ERROR (weak
        # password)"}}
        # {"meta":{"status":"ERROR","code":20014,
        # "message":"AUTH_USER_BLOCKED_ERROR"}}
        # {"meta":{"status":"ERROR","code":50000,"message":"SYSTEM_ERROR:
        # null"}}
        return response['token']

    def info_serviceList(self, number: BeelineNumber):
        # hiddenService - Индикатор отображения данных по скрытым услугам.
        # Значение по умолчанию - false, скрытые услуги не возвращаются
        params = {'hiddenService': 'true'}
        response, number = self.__get_request__(url=SERVICELIST, params=params,
                                                beeline_number=number)

        return response, number

    def info_accumulators(self, number: BeelineNumber):
        return self.__get_request__(url=ACCUMULATORS, beeline_number=number)

    def info_pricePlan(self, number: BeelineNumber):
        return self.__get_request__(url=PRICEPLAN, beeline_number=number)

    def info_subscriptions(self, number: BeelineNumber):
        return self.__get_request__(url=SUBSCRIPTIONS, beeline_number=number)

    def info_prepaidBalance(self, number: BeelineNumber):
        return self.__get_request__(url=PREPAID_BALANCE, beeline_number=number)

    def info_prepaidAddBalance(self, number: BeelineNumber):
        return self.__get_request__(url=PREPAID_ADD_BALANCE, beeline_number=number)

    def info_onlineBillDetail(self, number: BeelineNumber,
                              period_start: datetime,
                              period_end: datetime):
        params = {
            'periodStart': period_start.strftime('%Y-%m-%d'),
            'periodEnd': period_end.strftime('%Y-%m-%d')
        }
        response, number = self.__get_request__(url=BILL_DETAIL, params=params,
                                                beeline_number=number)

        return response, number


