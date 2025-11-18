import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
import requests
import json
from config.config_loader import get_env_var_value


class SendMsg(object):
    def __init__(self):
        self.corpid = get_env_var_value('wechat', 'corpid')
        self.corpsecret = get_env_var_value('wechat', 'corpsecret')
        self.agentid = get_env_var_value('wechat', 'agentid')


    def getToken(self):
        if self.corpid is None or self.corpsecret is None:
            return False, '企业微信相关信息未配置'
        url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=' + self.corpid + '&corpsecret=' + self.corpsecret
        response = requests.get(url)
        res = response.json()
        self.token = res['access_token']
        return True, '企业微信token获取成功'

    def sendMsg(self, msg):
        _isOK, result = self.getToken()
        if _isOK:
            url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=' + self.token
            jsonmsg = {
                "touser": "@all",
                "msgtype": "text",
                "agentid": self.agentid,
                "text": {
                    "content": msg
                },
                "safe": 0
            }
            data = (bytes(json.dumps(jsonmsg), 'utf-8'))
            requests.post(url, data, verify=False)
        else:
            print(result)

if __name__ == '__main__':
    wechatMsg = SendMsg()
    wechatMsg.sendMsg('API接口从无到有')