import requests
import json


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' \
             '(KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'

# entry point from repo:
# https://github.com/arthurvaverko-kaltura/beeline-usss-mock/
BASE = "https://my.beeline.ru/"
API_1_0 = BASE + "api/1.0/"

AUTH = API_1_0 + 'auth'


class BeelineAPI:
    """Класс неофициального API Beeline.ru"""

    def __init__(self):
        self.headers = {'User-Agent': USER_AGENT}

    def __get_request__(self, url, params):
        return requests.get(url, params=params, headers=self.headers)

    def obtain_token(self, cnt: str, password: str):
        params = {
            'login': cnt,
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


