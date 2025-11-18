import json
from urllib.parse import urlparse, parse_qs
import re
import requests
import jsonpath
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()

# 使用相对导入
from config.config_loader import get_env_var_value, get_env_now
from common.api_assertion import APIAssertion


class Paramete:
    """
    全局参数存储类
    注意：所有模块都应该使用同一个 Paramete 实例
    导入方式：from common.publicFunction import Paramete
    """
    pass


def replace_data(data):
    """
    替换变量
    :param data:
    :return:
    """
    keys = None
    try:
        ru = r'\${(.*?)}'
        while re.search(ru, data):
            res = re.search(ru, data)
            keys = res.group(1)
            value = get_env_var_value(get_env_now(), keys)  # 先找系统变量
            if value is None:
                value = getattr(Paramete, keys)  # 再找环境变量
                value = value.text if isinstance(value, requests.Response) else str(value)
            data = re.sub(re.escape(res.group(0)), value, data, 1)
            data = data.replace('\\', '')
            data = data.replace('\n', '\\n')
    except Exception as e:
        print(f'❌ 替换变量失败:未找到系统变量或环境变量【{keys}】')
    return data


def analyzing_param(param):
    """
     ${abc}取出abc
    :param param:
    :return:
    """
    ru = r'\${(.*?)}'
    if re.search(ru, param):
        return re.findall(ru, param)[0]
    return param


def contains_http(param):
    """
    检测传入的参数是否包含 'http' 或 'https'。

    :param param: 要检测的字符串参数
    :return: 如果包含 'http' 或 'https'，则返回 True，否则返回 False
    """
    pattern = r'(http|https):\/\/'
    if re.search(pattern, param):
        return True
    return False

def extract_variable(response, **case):
    other = case['other']
    rul = ''
    type = ''
    s = ''
    try:
        parts = other.split('|')
        type = parts[0]
        s = parts[1]
    except Exception:
        _reason = '格式错误'
    if type == 'obj':
        result = ''
        key = ''
        par = ''
        try:
            parts = s.split(':')
            par = parts[0]
            key = parts[1]
        except Exception:
            _reason = '变量提取格式错误'
        try:
            res = json.dumps(response.json(), ensure_ascii=False)
        except Exception:
            res = response.text
        escaped_str = res.replace("\n", "#$#")  # 处理json字符串中带有“\n“换行符无法转换
        try:
            result = json.loads(escaped_str, strict=False)  # 指定在解析 JSON 数据时允许一些非严格的解析模式
        except json.JSONDecodeError as e:
            print(f"JSON解析错误：{e}")
        key = '$..' + key
        try:
            value1 = str(jsonpath.jsonpath(result, key)[0])
        except Exception:
            return False, '字典中[' + str(result) + ']没有键[' + key + '], 执行失败'
        value = value1.replace("#$#", "\\n")
        value = value.replace("'", '"')
        setattr(Paramete, par, value)
        rul = f' 已经取得值[' + value + '] \n ==>存入变量[${' + par + '}]中'
    return rul

def postPrint(**case):
    api = replace_data(str(case['url']))
    if case.get('method') in ['post', 'put', 'get', 'delete']:
        print(f'用例ID：【{str(case["case_id"])}】  接口地址：【{api}】  类型：【{case["method"]}】')
    elif case.get('title') is not None:
        print(
            f'用例ID：【{str(case["case_id"])}】  方法名称：【{case["method"]}】  类型：【{str(case["url"])}】  变量值：【{case["title"]}】')
    else:
        print(f'用例ID：【{str(case["case_id"])}】  方法名称：【{case["method"]}】  类型：【{str(case["url"])}】')
    # 只有当data有实际值时才打印（空字符串、None、0、False等都不进入）
    if case.get('data'):
        data = replace_data(str(case['data']))
        data = str(data)
        print('参数：【' + data + '】')
    # if case.get('method', '').lower() == 'get':
    #     url = str(case['url'])
    #     parsed_url = urlparse(url)
    #     params = parse_qs(parsed_url.query)  # 解析URL中的查询参数
    #     print('参数：【')
    #     for key, values in params.items():
    #         for value in values:
    #             print(f'{key}={value}')  # 打印每个参数及其值
    #     print('】')

def _execute_assertions(response, **case):
    """
    执行断言列表
    
    Args:
        response: 响应对象
        case: 测试用例数据，包含断言信息
        
    Returns:
        tuple: (是否成功, 断言结果信息)
    """
    
    # 初始化结果变量
    all_passed = True
    reason_list = []
    assertions = []
    try:
        assertions = json.loads(case['assertions'])  
    except Exception:
        _isOk = False
        _reason = f"断言格式错误：{case['assertions']}"
        return _isOk, _reason
    
    for i, assertion in enumerate(assertions, 1):
        
        if assertion.startswith("contains_"):#响应体json包含字段
            # 格式: contains_id;contains_data.list
            field = replace_data(assertion.replace("contains_", ""))
            _isOk, _reason = APIAssertion.assert_json_contains(response, field)
        elif assertion.startswith("value_"):#响应体json字段值等于
            # 格式: value_field_name=expected_value
            parts = replace_data(assertion.replace("value_", "")).split("=", 1)
            if len(parts) == 2:
                field, expected_value = parts
                _isOk, _reason = APIAssertion.assert_json_value(response, field, expected_value)
            else:
                _isOk = False
                _reason = f'断言格式错误：{assertion}'
        elif assertion.startswith("time_"):#响应时间小于
            # 格式: time_10
            max_time = assertion.replace("time_", "")
            _isOk, _reason = APIAssertion.assert_response_time(response, int(max_time))
        elif assertion.startswith("jsonpath_"):#响应体json路径值等于
            # 格式说明：
            # jsonpath_$.data.id=123        # 精确匹配（相等）
            # jsonpath_$.data.name&张三     # 包含匹配
            # jsonpath_$.data.age>18        # 大于
            # jsonpath_$.data.age<100       # 小于
            jsonpath_part = assertion.replace("jsonpath_", "")
            
            if "=" in jsonpath_part:
                json_path, expected_value = jsonpath_part.split("=", 1)
                expected_value = replace_data(expected_value)
                _isOk, _reason = APIAssertion.assert_json_path(response, json_path, expected_value)
            elif "&" in jsonpath_part:
                json_path, expected_value = jsonpath_part.split("&", 1)
                expected_value = replace_data(expected_value)
                _isOk, _reason = APIAssertion.assert_json_path_contains(response, json_path, expected_value)
            elif ">" in jsonpath_part and "<" not in jsonpath_part:
                json_path, expected_value = jsonpath_part.split(">", 1)
                expected_value = replace_data(expected_value)
                _isOk, _reason = APIAssertion.assert_json_path_greater(response, json_path, expected_value)
            elif "<" in jsonpath_part and ">" not in jsonpath_part:
                json_path, expected_value = jsonpath_part.split("<", 1)
                expected_value = replace_data(expected_value)
                _isOk, _reason = APIAssertion.assert_json_path_less(response, json_path, expected_value)
            elif "<>" in jsonpath_part:
                json_path, expected_value = jsonpath_part.split("<>", 1)
                expected_value = replace_data(expected_value)
                _isOk, _reason = APIAssertion.assert_json_path_not_equal(response, json_path, expected_value)
            else:
                _isOk = False
                _reason = f'JSONPath断言格式错误，缺少期望值：{expected_value}'
        elif assertion.startswith("schema_"):#响应体json结构等于
            # 格式: schema_schema.json
            schema_file = assertion.replace("schema_", "")
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            _isOk, _reason = APIAssertion.assert_json_schema(response, schema)
        elif assertion.startswith("header_"):#响应头包含字段
            # 格式: header_Content-Type
            header_part = assertion.replace("header_", "")
            if "=" in header_part:
                header_name, expected_value = header_part.split("=", 1)
                expected_value = replace_data(expected_value)
                _isOk, _reason = APIAssertion.assert_header_contains(response, header_name, expected_value)
            else:
                _isOk = False
                _reason = f'头部断言格式错误，缺少期望值：{assertion}'
        elif assertion.startswith("headerValue_"):
            # 格式: header_value_Content-Type=application/json
            header_part = assertion.replace("headerValue_", "")
            if "=" in header_part:
                header_name, expected_value = header_part.split("=", 1)
                expected_value = replace_data(expected_value)
                _isOk, _reason = APIAssertion.assert_header_value(response, header_name, expected_value)
            else:
                _isOk = False
                _reason = f'头部值断言格式错误，缺少期望值：{assertion}'
        elif assertion.startswith("header_text_"):#响应头文本包含
            # 格式: text_响应内容包含"success"
            expected_text = assertion.replace("header_text_", "")
            _isOk, _reason = APIAssertion.assert_text_contains(response, expected_text)
        elif assertion.startswith("text_matches_"):#响应文本匹配正则表达式
            # 格式: text_matches_响应内容匹配正则表达式"^[0-9]+$"
            pattern = assertion.replace("text_matches_", "") 
            _isOk, _reason = APIAssertion.assert_text_matches(response, pattern)
        elif assertion.startswith("text_contains_"):#
            # 格式: text_contains_响应内容包含"success"
            expected_text = assertion.replace("text_contains_", "")
            _isOk, _reason = APIAssertion.assert_text_contains(response, expected_text)
        elif assertion.startswith("cookies_contain_"):#响应头cookies包含字段
            # 格式: cookies_contain_cookie_name
            cookie_name = assertion.replace("cookies_contain_", "")
            _isOk, _reason = APIAssertion.assert_cookies_contain(response, cookie_name)
        elif assertion.startswith("cookie_value_"):#响应头cookies值等于
            # 格式: cookie_value_cookie_name=expected_value
            cookie_part = assertion.replace("cookie_value_", "")
            if "=" in cookie_part:
                cookie_name, expected_value = cookie_part.split("=", 1)
                expected_value = replace_data(expected_value)
                _isOk, _reason = APIAssertion.assert_cookie_value(response, cookie_name, expected_value)
            else:
                _isOk = False
                _reason = f'Cookie值断言格式错误，缺少期望值：{assertion}'
        elif assertion.startswith("response_size_"):#响应大小
            # 格式: response_size_min=100&max=200
            size_part = assertion.replace("response_size_", "")
            if "&" in size_part:
                min_size, max_size = size_part.split("&", 1)
                min_size = int(min_size.split("=")[1])
                max_size = int(max_size.split("=")[1])
                _isOk, _reason = APIAssertion.assert_response_size(response, min_size, max_size)
            else:
                _isOk = False
                _reason = f'响应大小断言格式错误，缺少期望值：{assertion}'
        elif assertion.startswith("structure_"):#响应体json结构等于 
            # 格式: structure_schema.json
            schema_file = assertion.replace("structure_", "")
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            _isOk, _reason = APIAssertion.assert_json_structure(response, schema)
        else:
            print(assertion)
            _isOk = False
            _reason = '未定义的断言规则：【{}】'.format(assertion)
        
        # 收集每个断言的结果
        status = "✓ 通过" if _isOk else "✗ 失败"
        reason_list.append(f"---断言{i}: {assertion} -> {status}: {_reason}")
        
        # 如果有断言失败，标记整体失败
        if not _isOk:
            all_passed = False
    
    # 合并所有断言结果
    total_assertions = len(assertions)
    passed_count = sum(1 for reason in reason_list if "✓ 通过" in reason)
    failed_count = total_assertions - passed_count
    
    summary = f"断言执行完成: 总计{total_assertions}个, 通过{passed_count}个, 失败{failed_count}个"
    combined_reason = f"{summary}\n" + "\n".join(reason_list)
    return all_passed, combined_reason