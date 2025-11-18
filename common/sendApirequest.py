from sqlite3 import paramstyle
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
import requests
import urllib3

# 禁用SSL证书验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SendApirequests(object):

    def __init__(self):
        self.session = requests.session()

    def request_Obj(self, method, url, params=None, data=None, json=None, files=None, headers=None, verify=True):
        response = requests.request(method=method, url=url, params=params, data=data, json=json, files=files,
                                    headers=headers,verify=False)
        return response
