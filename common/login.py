# 导入获取yaml方法
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
from config.config_loader import get_env_var_value, get_env_now
from common.sendApirequest import SendApirequests
from common.publicFunction import Paramete


def login(user):
    """
    封装登录接口
    :param user: yaml文件里账号密码的用户名称
    :return: 
    """
    # 取出账号密码
    username, password = get_env_var_value(get_env_now(), 'adminname'), get_env_var_value(get_env_now(), 'adminpwd')
    # 赋值给登录接口的入参
    login_data = {
        "name": f"{username}",
        "password": f"{password}",
        "remember_password": 1
    }
    # 执行接口请求
    login_res = SendApirequests().request_Obj("post", get_env_var_value(get_env_now(), 'url') + "/login", json=login_data,verify=False)
    # 返回出参
    
    # 添加响应检查
    try:
        res_json = login_res.json()
        print(f"登录响应: {res_json}")  # 打印完整响应，方便调试
        
        # 检查响应结构
        if 'data' in res_json and 'jwt' in res_json['data']:
            return res_json['data']['jwt']
        else:
            print(f"登录响应结构异常，完整响应: {res_json}")
            raise KeyError(f"响应中缺少必需字段，响应内容: {res_json}")
    except Exception as e:
        print(f"登录请求失败，状态码: {login_res.status_code}, 响应: {login_res.text}")
        raise e

def get_default_authorization():
        """
        获取默认的授权token
        :return: 返回格式化的Bearer token字符串，失败返回None
        """
        try:
            # 尝试从环境变量获取admintoken
            token = getattr(Paramete, 'token', None)
            if token:
                return f"Bearer {token}"
            
            # 如果没有token，尝试登录获取
            token = login('admin')  # 获取管理员token
            setattr(Paramete, 'token', token)
            return f"Bearer {token}"
        except Exception as e:
            print(f"获取默认授权失败: {e}")
            return None

# 测试一下，道友们可以用自己公司系统测试
if __name__ == '__main__':
    response = get_default_authorization()
    print(response)


