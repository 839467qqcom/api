# -*- coding: utf-8 -*-
import datetime
import time
import json
import random
import jsonpath
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
from config.config_loader import get_env_var_value
from common.operatorDB import OpeartorDB
from common.publicFunction import Paramete, analyzing_param, contains_http, replace_data
from common.sendApirequest import SendApirequests
from common.sendEmail import SendMail
from common.sendMsg import SendMsg
from common.login import get_default_authorization

class CommKeyword(object):
    def __init__(self):
        self.operatordb = OpeartorDB()
        self.sendApi = SendApirequests()
        self.sendMail = SendMail()
        self.sedMsg = SendMsg()


    def get_current_casefile_name(self, **kwargs):
        """
        获取执行用例文件名称
        :return: 返回用例文件名称
        """
        try:
            fileName = get_env_var_value('case', 'testcase')
        except Exception as e:
            return False, '参数中未设置用例文件名称，请检查配置文件'
        return True, fileName


    def send_api(self, **kwargs):
        """
        发送用例请求 post, get
        :param kwargs:  请求的参数 ，有url,headers,data等
        :return:  bl, cases 一参数返回成功与否，二参数请求结果或失败原因
        """
        try:
            url = replace_data(kwargs['url'])
            method = kwargs['method']
            check = contains_http(url)
            if not check:
                response = f"用例[{kwargs['case_id']}]地址输入不合法: {url}"
                return False, response
            
            # 处理headers
            if kwargs['headers'] is None:
                headers = {}
            else:
                _isOk, result = self.format_headers(headers=replace_data(kwargs['headers']).strip())
                if _isOk:
                    headers = result
                else:
                    return _isOk, result
            
            # 检查并添加默认授权 - 支持大小写兼容
            # has_auth = any(key.lower() == 'authorization' for key in headers.keys())
            # if not has_auth:
            #     default_auth = get_default_authorization()
            #     if default_auth:
            #         headers['authorization'] = default_auth
            # 处理请求体数据
            data = None
            jsondata = None
            
            if kwargs.get('data'):
                replaced_data = replace_data(kwargs['data'])
                if method.lower() in ('post', 'delete', 'put'):
                    # 非GET请求：尝试解析为JSON
                    try:
                        jsondata = json.loads(replaced_data)
                    except (json.JSONDecodeError, ValueError) as e:
                        return False, f'JSON数据格式错误: {str(e)}'
                
                elif method.lower() == 'get':
                    # GET请求：作为URL查询参数
                    url = url + ('&' if '?' in url else '?') + replaced_data
            if kwargs.get('other'):
                s = kwargs.get('other')
                parts = s.split('|')
                type = parts[0]
                file = parts[1]
                if type == 'file':
                    # 文件上传逻辑
                    files = {'file': open(file, 'rb')}
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = self.sendApi.request_Obj(method=method, url=url, json=jsondata, data=data,
                                                        headers=headers)
            else:
                response = self.sendApi.request_Obj(method=method, url=url, json=jsondata, data=data, headers=headers,verify=False)
                # 去掉响应文本前后的空白字符（包括换行符 \n）
                setattr(Paramete, 'response', response.text.strip())
               
            
        except Exception as e:
            return False, '发送请求失败' + str(e)
        return True, response


    def set_common_param(self, key, value):
        """
        :param key:  公共变量名
        :param value: 参数
        :return:
        """
        setattr(Paramete, key, value)

    def get_commom_param(self, key):
        """
        :param key: 公共变量名
        :return: 取变量值
        """
        return getattr(Paramete, key)

    def get_current_sheet_name(self):
        """
        :return: 返回当前执行用例的sheet页名称
        """
        sheet_name = None
        sh_index = self.get_commom_param('sheetindex')
        sh_dict = self.get_commom_param('sheetdict')
        for sh in sh_dict:
            if sh.title().find(str(sh_index)) != -1:
                sheet_name = sh_dict[sh.title().lower()]
        return sheet_name

    def get_json_value_as_key(self, **kwargs):
        """
        得到json中key对应的value,存变量param
        默认传的参数为：
        result:用来接收结果的变量
        method:调用的方法 ，带不带${    } 都行
        param_x:参数，数量不限。格式可为${    }会替换为已存在的数据
        """
        result = None
        try:
            param = kwargs['result']
            jsonstr = kwargs['param_1']
            key = kwargs['param_2']
        except KeyError:
            return False, '方法缺少参数，执行失败'
        param = analyzing_param(param)
        jsonstr = replace_data(jsonstr)
        key = replace_data(key)
        if param is None or jsonstr is None or key is None:
            return False, '传入的参数为空，执行失败'
        escaped_str = jsonstr.replace("\n", "#$#")  #处理json字符串中带有“\n“换行符无法转换
        try:
            result = json.loads(escaped_str, strict=False)  #指定在解析 JSON 数据时允许一些非严格的解析模式
        except json.JSONDecodeError as e:
            print(f"JSON解析错误：{e}")
        key = '$..' + key
        try:
            value1 = str(jsonpath.jsonpath(result, key)[0])
            value = value1.replace("#$#", "\\n")
            value = value.replace("'", '"')
        except Exception:
            return False, '字典中[' + jsonstr + ']没有键[' + key + '], 执行失败'
        setattr(Paramete, param, value)
        return True, ' 已经取得[' + value + ']==>[${' + param + '}]'

    def format_headers(self, **kwargs):
        """
        格式化请求头
        :param param:excel里读出出来的header，是从浏览器f12里直接copy的
        :return:
        """
        param = kwargs['headers']
        if param is None:
            return False, 'Headers为空'
        list_header = param.split('\n')
        headers = {}
        for li in list_header:
            buff = li.split(':')
            try:
                headers[buff[0]] = buff[1]
            except IndexError:
                return False, 'Headers格式不对'
        return True, headers

    def set_variable(self, **kwargs):
        """
        设置变量
        :param kwargs:
        :return:
        """
        try:
            var = kwargs['result']
            func = kwargs['param_2']
        except KeyError:
            print(var,func)
            return False, '方法缺少参数，执行失败'
        if func == 1:
            param = replace_data(kwargs['param_1'])
        else:
            param = eval(replace_data(kwargs['param_1']))
        if var is None or param is None:
            return False, '传入的参数为空，执行失败'

        setattr(Paramete, var, param)
        param_str = str(param)
        return True, ' 已经设置变量[' + param_str + ']==>[${' + var + '}]'

    def force_wait(self, **kwargs):
        """
        强制等待指定时间
        :param seconds: 等待的秒数
        """
        try:
            s = kwargs['param_1']
        except KeyError:
            return False, '方法缺少参数，执行失败'
        time.sleep(s)
        return True, ' 已强制等待[' + str(s) + ']秒'

    def execut_sql(self, **kwargs):
        """
        执行SQL
        :param kwargs:
        :return:
        """
        try:
            sql = replace_data(kwargs['param_1'])
            table_name = kwargs['param_5']
        except KeyError:
            return False, '方法缺少参数，执行失败'
        try:
            var = kwargs['param_2']
            par = kwargs['param_3']
        except Exception:
            var = None
            par = None
        isOK, result = self.operatordb.excetSql(sql, table_name)
        if isOK and var is not None:
            data = result[par]
            setattr(Paramete, var, data)
            return True, '执行SQL:[' + sql + ']成功，取得' + par + '的数据[' + str(data) + ']==>[${' + var + '}]'
        elif isOK and var is None:
            return True, '执行SQL:[' + sql + ']成功'
        elif isOK is False:
            return isOK, result

    def assert_database(self, **kwargs):
        """
        数据库断言函数
        :param sql: SQL语句
        :param table_name: 表名
        :param expr: 预期值
        :param par: 返回结果中需要断言的字段名
        :return: 断言结果
        """
        try:
            sql_param = json.loads(kwargs['param_5'])  
        except Exception:
            _reason = f"数据库断言格式错误：{kwargs['param_5']}"
            return False, _reason
        ["SELECT * FROM users", "users", "name", "结果等于", "张三"]
        # 处理多条数据的情况
        if isinstance(sql_param, list) and len(sql_param) > 0:
            # 如果是多条数据，取第一条进行断言
            if isinstance(sql_param[0], list) and len(sql_param[0]) >= 5:
                sql, table_name, par, rules, expr = sql_param[0][:5]
            elif len(sql_param) >= 5:
                sql, table_name, par, rules, expr = sql_param[:5]
            else:
                return False, f"数据库断言参数不足，需要5个参数，实际获得{len(sql_param)}个"
        else:
            return False, "数据库断言参数格式错误，应为包含参数的列表"
        sql = replace_data(sql)
        table_name = replace_data(table_name)
        par = replace_data(par)
        rules = replace_data(rules)
        expr = replace_data(expr)
        if not all([sql, table_name, par, rules, expr]):
            return False, '方法缺少参数，执行失败'
        isOK, result = self.operatordb.excetSql(sql, table_name)
        if isOK:
            data = result[par]
            field_names = par
            if rules == '结果包含':
                if expr in data:
                    return True, f'表【{table_name}】中【{field_names}】字段的值【{data}】包含校验值: 【{expr}】'
                else:
                    return False, f'表【{table_name}】中【{field_names}】字段的值【{data}】不包含校验值: 【{expr}】'
            elif rules == '结果等于':
                if expr == data:
                    return True, f'表【{table_name}】中【{field_names}】字段的值【{data}】等于校验值: 【{expr}】'
                else:
                    return False, f'表【{table_name}】中【{field_names}】字段的值【{data}】不等于校验值: 【{expr}】'
            else:
                return True, f'执行SQL: [{sql}]成功'
        else:
            return False, f'执行SQL: [{sql}]失败'

    def send_email(self, **kwargs):
        """
        发送邮件
        :return:
        """
        return self.sendMail.send_email()

    def send_msg(self, **kwargs):
        """
        发送消息
        :param kwargs:
        :return:
        """
        title = kwargs['title']
        url = kwargs['url']
        code = kwargs['code']
        result = kwargs['result'].decode('unicode_escape')
        nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
        msg = nowTime + '\n用例名称：' + title + '\n请求：' + url + '\n响应码：' + code + '\n响应信息：' + result
        self.sedMsg.sendMsg(msg)

    def new_random_str(self, **kwargs):
        """
        生成随机字符串
        :param kwargs: 一个字典，包含以下元素
            - init_str: 字符串的初始值，用于生成随机字符串
            - length: 随机字符串的长度
            - var_name: 生成的随机字符串的变量名，用于保存到测试用例的变量池中
        :return: 一个元组，包含两个元素，第一个元素是生成的随机字符串，第二个元素是操作结果说明
        """
        try:
            init_str = kwargs['param_1']
            length = kwargs['param_2']
            var_name = kwargs['param_3']
        except KeyError as e:
            return False, f'缺少必要的输入参数[{e}].'

        if not isinstance(init_str, str):
            return False, '初始字符串应该是一个字符串类型'
        if not isinstance(length, int):
            return False, '随机字符串的长度应该是整数类型'

        random_str = ''.join([random.choice(init_str) for i in range(length)])
        setattr(Paramete, var_name, random_str)

        return random_str, f'随机字符串[{random_str}]已保存到测试用例的变量池[{var_name}]中。'

    def replace(self, **kwargs):
        """
        替换传入数据中的指定数据
        :param data: 待处理数据
        :param old_value: 要替换的旧值
        :param new_value: 替换成的新值

        :return: 替换后的数据
        """

        try:
            data = replace_data(kwargs['param_1'])
            old_value = kwargs['param_2']
            new_value = kwargs['param_3']
            var = kwargs['result']
        except KeyError:
            return False, '方法缺少参数，执行失败'
        replaced_data = data.replace(old_value, new_value)
        setattr(Paramete, var, replaced_data)
        param_str = str(replaced_data)
        return True, ' 已替换数据且设置成变量[' + param_str + ']==>[${' + var + '}]'

    def random_str(self, **kwargs):
        try:
            type = kwargs['param_1']
            var_name = kwargs['result']
        except KeyError as e:
            return False, f'缺少必要的输入参数[{e}].'
        try:
            var = kwargs['param_2']
        except Exception:
            var = None
        value = None
        try:
            from faker import Faker
            f = Faker(locale='zh_CN')
        except ImportError:
            return False, "faker 模块未安装"
        if type == '姓名':
            value = f.name()
        elif type == '手机号':
            value = f.phone_number()
        elif type == '邮箱':
            value = f.email()
        elif type == '身份证号':
            value = f.ssn()
        elif type == '公司':
            value = f.company()
        elif type == '随机数':
            value = f.random_number(var)
        elif type == '地址':
            value = f.address()
        elif type == '用户名':
            value = f.user_name()
        elif type =='ip段':
            value = f.ipv4()
        setattr(Paramete, var_name, value)
        return value, f'伪数据[{type}][{value}]已保存到测试用例的变量池[{var_name}]中。'

    def fetch_all_ids(self,**kwargs):
        """
        获取所有id
        :param kwargs:
            param_1: JSON字符串
            result: 结果变量名
            param_2: 第一层key（可选，如'data'）
            param_3: 第二层key（可选，如'list'）
            param_4: 要提取的字段名（可选，默认为'id'）
        :return: (成功标志, 结果信息)
        
        示例1：直接从列表提取id
            param_1='[{"id":1},{"id":2}]', result='ids', param_2=None, param_3=None
        示例2：从data.list提取id  
            param_1='{"data":{"list":[{"id":1}]}}', result='ids', param_2='data', param_3='list'
        示例3：提取其他字段
            param_1='{"data":{"list":[{"ip":"1.1.1.1"}]}}', result='ips', param_2='data', param_3='list', param_4='ip'
        """
        try:
            jsonstr = kwargs['param_1']
            param = kwargs['result']
        except KeyError:
            return False, '方法缺少参数(param_1/result)，执行失败'
        
        # 可选参数
        key1 = kwargs.get('param_2')
        key2 = kwargs.get('param_3')
        field_name = kwargs.get('param_4', 'id')  # 默认提取id字段
        
        param = analyzing_param(param)
        jsonstr = replace_data(jsonstr)
        if param is None or jsonstr is None:
            return False, '传入的参数为空，执行失败'
        
        # JSON解析 - 兼容字符串和字典类型
        try:
            if isinstance(jsonstr, dict):
                # 如果已经是字典，直接使用
                data = jsonstr
            elif isinstance(jsonstr, str):
                # 如果是字符串，进行JSON解析
                data = json.loads(jsonstr)
            else:
                return False, f'不支持的数据类型: {type(jsonstr)}'
        except json.JSONDecodeError as e:
            return False, f'JSON解析失败: {str(e)}'
        
        # 根据key提取目标列表
        try:
            if key1 and key2:
                # 两层嵌套: data.list
                items = data.get(key1, {}).get(key2, [])
            elif key1:
                # 一层嵌套: data
                value = data.get(key1, [])
                items = value if isinstance(value, list) else []
            else:
                # 直接是列表
                items = data if isinstance(data, list) else []
        except Exception as e:
            return False, f'提取列表失败: {str(e)}'
        
        # 提取指定字段
        if not isinstance(items, list):
            return False, f'目标数据不是列表类型: {type(items)}'
        
        field_values = [item[field_name] for item in items if isinstance(item, dict) and field_name in item]
        setattr(Paramete, param, field_values)
        param_str = str(field_values)
        return True, f' 已提取{len(field_values)}个{field_name}值[' + param_str + ']==>[${' + param + '}]'

if __name__ == '__main__':
    a=CommKeyword()
    param_1 = {
    "status": 200,
    "msg": "Get successful",
    "data": {
        "list": [
            {
                "assign_time": 0,
                "bind_mac": 0,
                "broadcast": "192.165.3.15",
                "custom_field_27": "",
                "custom_field_47": "",
                "custom_field_48": "",
                "custom_field_49": "",
                "custom_field_50": "",
                "custom_field_51": "",
                "fault_reason": "",
                "gateway": "",
                "id": 163717,
                "ip": "192.165.3.15",
                "is_fault": 0,
                "mac": "",
                "netmask": "255.255.255.248",
                "network": "192.165.3.8",
                "notes": "",
                "rel_id": 0,
                "rel_type": "",
                "vlan": [
                    100
                ]
            },
            {
                "assign_time": 0,
                "bind_mac": 0,
                "broadcast": "192.165.3.15",
                "custom_field_27": "",
                "custom_field_47": "",
                "custom_field_48": "",
                "custom_field_49": "",
                "custom_field_50": "",
                "custom_field_51": "",
                "fault_reason": "",
                "gateway": "",
                "id": 163716,
                "ip": "192.165.3.14",
                "is_fault": 1,
                "mac": "",
                "netmask": "255.255.255.248",
                "network": "192.165.3.8",
                "notes": "",
                "rel_id": 0,
                "rel_type": "",
                "vlan": [
                    100
                ]
            },
            {
                "assign_time": 0,
                "bind_mac": 0,
                "broadcast": "192.165.3.15",
                "custom_field_27": "",
                "custom_field_47": "",
                "custom_field_48": "",
                "custom_field_49": "",
                "custom_field_50": "",
                "custom_field_51": "",
                "fault_reason": "",
                "gateway": "",
                "id": 163715,
                "ip": "192.165.3.13",
                "is_fault": 1,
                "mac": "",
                "netmask": "255.255.255.248",
                "network": "192.165.3.8",
                "notes": "",
                "rel_id": 0,
                "rel_type": "",
                "vlan": [
                    100
                ]
            },
            {
                "assign_time": 0,
                "bind_mac": 0,
                "broadcast": "192.165.3.15",
                "custom_field_27": "",
                "custom_field_47": "",
                "custom_field_48": "",
                "custom_field_49": "",
                "custom_field_50": "",
                "custom_field_51": "",
                "fault_reason": "",
                "gateway": "",
                "id": 163714,
                "ip": "192.165.3.12",
                "is_fault": 1,
                "mac": "",
                "netmask": "255.255.255.248",
                "network": "192.165.3.8",
                "notes": "",
                "rel_id": 0,
                "rel_type": "",
                "vlan": [
                    100
                ]
            },
            {
                "assign_time": 0,
                "bind_mac": 0,
                "broadcast": "192.165.3.15",
                "custom_field_27": "",
                "custom_field_47": "",
                "custom_field_48": "",
                "custom_field_49": "",
                "custom_field_50": "",
                "custom_field_51": "",
                "fault_reason": "",
                "gateway": "",
                "id": 163713,
                "ip": "192.165.3.11",
                "is_fault": 1,
                "mac": "",
                "netmask": "255.255.255.248",
                "network": "192.165.3.8",
                "notes": "",
                "rel_id": 0,
                "rel_type": "",
                "vlan": [
                    100
                ]
            },
            {
                "assign_time": 0,
                "bind_mac": 0,
                "broadcast": "192.165.3.15",
                "custom_field_27": "",
                "custom_field_47": "",
                "custom_field_48": "",
                "custom_field_49": "",
                "custom_field_50": "",
                "custom_field_51": "",
                "fault_reason": "",
                "gateway": "",
                "id": 163712,
                "ip": "192.165.3.10",
                "is_fault": 1,
                "mac": "",
                "netmask": "255.255.255.248",
                "network": "192.165.3.8",
                "notes": "",
                "rel_id": 0,
                "rel_type": "",
                "vlan": [
                    100
                ]
            },
            {
                "assign_time": 0,
                "bind_mac": 0,
                "broadcast": "192.165.3.15",
                "custom_field_27": "",
                "custom_field_47": "",
                "custom_field_48": "",
                "custom_field_49": "",
                "custom_field_50": "",
                "custom_field_51": "",
                "fault_reason": "",
                "gateway": "",
                "id": 163711,
                "ip": "192.165.3.9",
                "is_fault": 1,
                "mac": "",
                "netmask": "255.255.255.248",
                "network": "192.165.3.8",
                "notes": "",
                "rel_id": 0,
                "rel_type": "",
                "vlan": [
                    100
                ]
            },
            {
                "assign_time": 0,
                "bind_mac": 0,
                "broadcast": "192.165.3.15",
                "custom_field_27": "",
                "custom_field_47": "",
                "custom_field_48": "",
                "custom_field_49": "",
                "custom_field_50": "",
                "custom_field_51": "",
                "fault_reason": "",
                "gateway": "",
                "id": 163710,
                "ip": "192.165.3.8",
                "is_fault": 0,
                "mac": "",
                "netmask": "255.255.255.248",
                "network": "192.165.3.8",
                "notes": "",
                "rel_id": 0,
                "rel_type": "",
                "vlan": [
                    100
                ]
            }
        ],
        "count": 8
    },
    "timestamp": 1760409525
}
    c = a.fetch_all_ids(param_1=param_1, result='ids', param_2='data', param_3='list', param_4='id')
    print(c)
