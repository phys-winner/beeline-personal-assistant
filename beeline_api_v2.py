import json
from datetime import datetime

import requests
from ratelimiter import RateLimiter

from beeline_api import BeelineNumber
from beeline_api_errors import *

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
             '(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'

# entry point from repo:
# https://github.com/arthurvaverko-kaltura/beeline-usss-mock/
BASE = "https://api.beeline.ru"
API_2 = BASE + "/mobile/api/v2/"
SERVICE = API_2 + 'profile/service'

AUTH = BASE + '/mw/auth/1/auth'


class BeelineAPIv2:
    """Класс неофициального API v2 Beeline.ru"""

    def __init__(self):
        self.auth_headers = {'Client-Type': 'MobbApp2',
                        'User-Agent': 'MyBeeline/4.71.6-3909',
                        'Content-Type': 'application/json'}
        self.headers = {'X-AppVersion': '4.71.6',
                        'X-AndroidVersion': '25',
                        'X-Device': 'TAB',
                        'X-Theme': 'Light',
                        'User-Agent': 'MyBeeline/4.71.6-3909',
                        'Content-Type': 'application/json; charset=UTF-8'}

    def __get_headers__(self, url, beeline_number):
        # если оно не в
        if beeline_number.token_v2 == '' and url != AUTH:
            beeline_number.token_v2 = self.obtain_token(beeline_number)
        if url == AUTH:
            headers = self.auth_headers
        else:
            headers = self.headers
            headers['X-Auth-Token'] = beeline_number.token_v2
            headers['X-CTN'] = beeline_number.ctn
            headers['X-Login'] = beeline_number.ctn
        return headers, beeline_number

    @RateLimiter(max_calls=1, period=2)
    def __get_request__(self, url, params=None, beeline_number=None):
        headers, beeline_number = self.__get_headers__(url, beeline_number)

        r = requests.get(url, params=params,  headers=headers)
        if not r.ok:
            raise InvalidResponse(f'{r.status_code} (GET v2): {url}', r)

        response = json.loads(r.text)
        print("GET v2: %s", r.text)

        if 'meta' in response and response['meta']['status'] == 'ERROR' and \
                'UAPI_UNAUTHORIZED' in response['meta']['message'] \
                and url != AUTH:
            # слетел токен, актуализируем его
            beeline_number.token_v2 = self.obtain_token(beeline_number)
            return self.__get_request__(url, params, beeline_number)

        if 'meta' in response and response['meta']['status'] != 'OK':
            raise StatusNotOK(f'{url} - {r.text}')
        return response, beeline_number

    @RateLimiter(max_calls=1, period=2)
    def __post_request__(self, url, data=None, beeline_number=None):
        headers, beeline_number = self.__get_headers__(url, beeline_number)
        r = requests.post(url, data=data, headers=headers)
        if not r.ok:
            raise InvalidResponse(f'{r.status_code} (POST v2): {url} - {r.text}', r)

        response = json.loads(r.text)
        print("POST v2: %s", r.text)

        if 'meta' in response and response['meta']['status'] == 'ERROR' and \
                'UAPI_UNAUTHORIZED' in response['meta']['message'] \
                and url != AUTH:
            # слетел токен, актуализируем его
            beeline_number.token_v2 = self.obtain_token(beeline_number)
            return self.__post_request__(url, data, beeline_number)

        if 'meta' in response and response['meta']['status'] != 'OK':
            raise StatusNotOK(f'{url} - {r.text}')
        return response, beeline_number

    def obtain_token(self, number: BeelineNumber):
        params = {
            'client_id': 'mybee;d133389d-4323-4592-80db-f7a9eb3c4dce;android_25;4.71.6_3909',
            'login': number.ctn,
            'password': number.password
        }
        response, _ = self.__get_request__(url=AUTH, params=params, beeline_number=number)

        # {"token":"12CD3740D3192CFDE1231AA508E211D4"}
        return response['token']

    def activate_service(self, number: BeelineNumber, soc: str):
        mydata = {'soc': soc}
        response, number = self.__post_request__(
            f'https://api.beeline.ru/mobile/api/v2/profile/service',
            data=json.dumps(mydata), beeline_number=number)

        return response, number
