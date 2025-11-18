# -*- coding: utf-8 -*-
"""
API断言模块
"""
import json
import re
from typing import Any, Dict
import requests
from jsonpath_ng import parse
from jsonschema import validate, ValidationError
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
from common.log import Log

logger = Log.getMylog()

class APIAssertion:
    """API断言类"""
    
    @staticmethod
    def assert_response_time(response: requests.Response, max_time):
        """
        断言响应时间
        
        Args:
            response: 响应对象
            max_time: 最大响应时间（秒）
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            elapsed = response.elapsed.total_seconds()
            assert elapsed <= int(max_time)
            _isOk = True
            _reason = f"响应时间断言通过: {elapsed:.2f}s <= {max_time}s"
        except AssertionError:
            _isOk = False
            _reason = f"响应时间断言失败: {elapsed:.2f}s > {max_time}s"
        return _isOk, _reason
    
    @staticmethod
    def assert_json_contains(response: requests.Response, key: str):
        """
        断言JSON响应包含指定键，支持嵌套路径（用点号分隔）
        
        Args:
            response: 响应对象
            key: 期望包含的键，支持嵌套路径如 'data.list' 或 'data.count'
        """
        try:
            data = response.json()
            
            # 支持嵌套路径，用点号分隔
            if '.' in key:
                keys = key.split('.')
                current_data = data
                
                # 逐层检查嵌套键
                for nested_key in keys:
                    if isinstance(current_data, dict) and nested_key in current_data:
                        current_data = current_data[nested_key]
                    else:
                        raise AssertionError(f"嵌套路径 '{key}' 中的键 '{nested_key}' 不存在")
                
                _isOk = True
                _reason = f"接口响应【{response.json()}】包含断言通过: 包含嵌套键 '{key}'"
            else:
                # 原有逻辑：检查顶级键
                assert key in data
                _isOk = True
                _reason = f"接口响应【{response.json()}】包含断言通过: 包含键 '{key}'"
        except AssertionError as e:
            _isOk = False
            if '.' in key:
                _reason = f"接口响应【{response.json()}】包含断言不通过: {str(e)}"
            else:
                _reason = f"接口响应【{response.json()}】包含断言不通过: 不包含键 '{key}'"
        except (json.JSONDecodeError, TypeError) as e:
            _isOk = False
            _reason = f"接口响应【{response.text}】包含断言失败: JSON解析错误 - {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_json_value(response: requests.Response, key: str, expected_value: Any):
        """
        断言JSON响应中指定键的值，支持嵌套路径（用点号分隔）
        
        Args:
            response: 响应对象
            key: 键名，支持嵌套路径如 'data.status' 或 'data.count'
            expected_value: 期望值
        """
        try:
            data = response.json()
            
            # 支持嵌套路径，用点号分隔
            if '.' in key:
                keys = key.split('.')
                current_data = data
                
                # 逐层获取嵌套值
                for nested_key in keys:
                    if isinstance(current_data, dict) and nested_key in current_data:
                        current_data = current_data[nested_key]
                    else:
                        raise KeyError(f"嵌套路径 '{key}' 中的键 '{nested_key}' 不存在")
                
                actual_value = current_data
            else:
                # 原有逻辑：获取顶级键值
                actual_value = data.get(key)
                if actual_value is None and key not in data:
                    raise KeyError(f"键 '{key}' 不存在")
            
            assert str(actual_value) == str(expected_value) 
            _isOk = True
            _reason = f"键 '{key}' 的值匹配，期望: {expected_value},实际: {actual_value}"
        except AssertionError:
            _isOk = False
            _reason = f"键 '{key}' 的值不匹配，期望: {expected_value},实际: {actual_value}"
        except KeyError as e:
            _isOk = False
            _reason = f"键值断言失败: {str(e)}"
        except (json.JSONDecodeError, TypeError) as e:
            _isOk = False
            _reason = f"键值断言失败: JSON解析错误 - {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_json_path(response: requests.Response, json_path: str, expected_value: Any):
        """
        使用JSONPath断言JSON响应
        
        Args:
            response: 响应对象
            json_path: JSONPath表达式
            expected_value: 期望值
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            data = response.json()
            jsonpath_expr = parse(json_path)
            #使用 jsonpath_expr在 data中查找所有匹配的节点，并将它们的 value 属性提取到一个列表 matches 中
            matches = [match.value for match in jsonpath_expr.find(data)]
            
            if not matches:
                _isOk = False
                _reason = f"JSONPath断言失败: 路径 '{json_path}' 未找到匹配项"
            elif len(matches) == 1:
                actual_value = matches[0]
                if str(actual_value) == str(expected_value):
                    _isOk = True
                    _reason = f"JSONPath断言通过: '{json_path}' 期望 {expected_value}，实际 {actual_value}"
                else:
                    _isOk = False
                    _reason = f"JSONPath断言失败: '{json_path}' 期望 {expected_value}，实际 {actual_value}"
            else:
                if expected_value in matches:
                    _isOk = True
                    _reason = f"JSONPath断言通过: '{json_path}' 包含期望值 {expected_value}，实际 {matches}"
                else:
                    _isOk = False
                    _reason = f"JSONPath断言失败: '{json_path}' 不包含期望值 {expected_value}，实际 {matches}"
        except (json.JSONDecodeError, Exception) as e:
            _isOk = False
            _reason = f"JSONPath断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_json_path_contains(response: requests.Response, json_path: str, expected_value: Any):
        """
        使用JSONPath断言JSON响应
        
        Args:
            response: 响应对象
            json_path: JSONPath表达式
            expected_value: 期望值
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            data = response.json()
            jsonpath_expr = parse(json_path)
            #使用 jsonpath_expr在 data中查找所有匹配的节点，并将它们的 value 属性提取到一个列表 matches 中
            matches = [match.value for match in jsonpath_expr.find(data)]
            
            if not matches:
                _isOk = False
                _reason = f"JSONPath断言失败: 路径 '{json_path}' 未找到匹配项"
            elif len(matches) == 1:
                actual_value = matches[0]
                if str(expected_value) in str(actual_value):
                    _isOk = True
                    _reason = f"JSONPath断言通过: '{json_path}' 的值{actual_value}包含期望值 {expected_value} "
                else:
                    _isOk = False
                    _reason = f"JSONPath断言失败: '{json_path}' 的值{actual_value}不包含期望值 {expected_value} "
            else:
                if expected_value in matches:
                    _isOk = True
                    _reason = f"JSONPath断言通过: '{json_path}' 的值{matches}包含期望值 {expected_value} "
                else:
                    _isOk = False
                    _reason = f"JSONPath断言失败: '{json_path}' 的值{matches}不包含期望值 {expected_value} "
        except (json.JSONDecodeError, Exception) as e:
            _isOk = False
            _reason = f"JSONPath断言失败: {str(e)}"
        return _isOk, _reason

    @staticmethod
    def assert_json_path_greater(response: requests.Response, json_path: str, expected_value: Any):
        """
        使用JSONPath断言JSON响应
        
        Args:
            response: 响应对象
            json_path: JSONPath表达式
            expected_value: 期望值
        """
        try:
            data = response.json()
            jsonpath_expr = parse(json_path)
            matches = [match.value for match in jsonpath_expr.find(data)]
            if not matches:
                _isOk = False
                _reason = f"JSONPath断言失败: 路径 '{json_path}' 未找到匹配项"
            elif len(matches) == 1:
                actual_value = matches[0]
                if int(actual_value) > int(expected_value):
                    _isOk = True
                    _reason = f"JSONPath断言通过: '{json_path}' 的值{actual_value}大于期望值 {expected_value} "
                else:
                    _isOk = False
                    _reason = f"JSONPath断言失败: '{json_path}' 的值{actual_value}不大于期望值 {expected_value} "
        except (json.JSONDecodeError, Exception) as e:
            _isOk = False
            _reason = f"JSONPath断言失败: {str(e)}"
        return _isOk, _reason

    @staticmethod
    def assert_json_path_less(response: requests.Response, json_path: str, expected_value: Any):
        """
        使用JSONPath断言JSON响应
        
        Args:
            response: 响应对象
            json_path: JSONPath表达式
            expected_value: 期望值
        """
        try:
            data = response.json()
            jsonpath_expr = parse(json_path)
            matches = [match.value for match in jsonpath_expr.find(data)]
            if not matches:
                _isOk = False
                _reason = f"JSONPath断言失败: 路径 '{json_path}' 未找到匹配项"
            elif len(matches) == 1:
                actual_value = matches[0]
                if int(actual_value) < int(expected_value):
                    _isOk = True
                    _reason = f"JSONPath断言通过: '{json_path}' 的值{actual_value}小于期望值 {expected_value} "
                else:
                    _isOk = False
                    _reason = f"JSONPath断言失败: '{json_path}' 的值{actual_value}不小于期望值 {expected_value} "
        except (json.JSONDecodeError, Exception) as e:
            _isOk = False
            _reason = f"JSONPath断言失败: {str(e)}"
        return _isOk, _reason

    @staticmethod
    def assert_json_path_not_equal(response: requests.Response, json_path: str, expected_value: Any):
        """
        使用JSONPath断言JSON响应
        
        Args:
            response: 响应对象
            json_path: JSONPath表达式
            expected_value: 期望值
        """
        try:
            data = response.json()
            jsonpath_expr = parse(json_path)
            matches = [match.value for match in jsonpath_expr.find(data)]
            if not matches:
                _isOk = False
                _reason = f"JSONPath断言失败: 路径 '{json_path}' 未找到匹配项"
            elif len(matches) == 1:
                actual_value = matches[0]
                if int(actual_value) != int(expected_value):
                    _isOk = True
                    _reason = f"JSONPath断言通过: '{json_path}' 的值{actual_value}不等于期望值 {expected_value} "
                else:
                    _isOk = False
                    _reason = f"JSONPath断言失败: '{json_path}' 的值{actual_value}等于期望值 {expected_value} "
        except (json.JSONDecodeError, Exception) as e:
            _isOk = False
            _reason = f"JSONPath断言失败: {str(e)}"
        return _isOk, _reason

    @staticmethod
    def assert_json_schema(response: requests.Response, schema: Dict[str, Any]):
        """
        断言JSON响应符合指定schema
        
        Args:
            response: 响应对象
            schema: JSON Schema
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            data = response.json()
            validate(instance=data, schema=schema)
            _isOk = True
            _reason = "JSON Schema断言通过: 响应数据符合预期结构"
        except json.JSONDecodeError as e:
            _isOk = False
            _reason = f"JSON Schema断言失败: JSON解析错误 - {str(e)}"
        except ValidationError as e:
            _isOk = False
            _reason = f"JSON Schema断言失败: 数据结构验证失败 - {str(e)}"
        except Exception as e:
            _isOk = False
            _reason = f"JSON Schema断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_header_contains(response: requests.Response, header_name: str, expected_value: str):
        """
        断言响应头包含指定值
        
        Args:
            response: 响应对象
            header_name: 响应头名称
            expected_value: 期望值
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            header_value = response.headers.get(header_name)
            if header_value is None:
                _isOk = False
                _reason = f"响应头断言失败: 响应头中不包含 '{header_name}'"
            elif expected_value in header_value:
                _isOk = True
                _reason = f"响应头断言通过: '{header_name}' 包含 '{expected_value}'"
            else:
                _isOk = False
                _reason = f"响应头断言失败: '{header_name}' 不包含期望值，期望: {expected_value}，实际: {header_value}"
        except Exception as e:
            _isOk = False
            _reason = f"响应头断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_header_value(response: requests.Response, header_name: str, expected_value: str):
        """
        断言响应头的值
        
        Args:
            response: 响应对象
            header_name: 响应头名称
            expected_value: 期望值
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            header_value = response.headers.get(header_name)
            if str(header_value) == str(expected_value):
                _isOk = True
                _reason = f"响应头值断言通过: '{header_name}' 期望 {expected_value}，实际 {header_value}"
            else:
                _isOk = False
                _reason = f"响应头值断言失败: '{header_name}' 期望 {expected_value}，实际 {header_value}"
        except Exception as e:
            _isOk = False
            _reason = f"响应头值断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_text_contains(response: requests.Response, expected_text: str):
        """
        断言响应文本包含指定内容
        
        Args:
            response: 响应对象
            expected_text: 期望包含的文本
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            if expected_text in response.text:
                _isOk = True
                _reason = f"文本包含断言通过: 响应中包含 '{expected_text}'"
            else:
                _isOk = False
                _reason = f"文本包含断言失败: 响应中不包含 '{expected_text}'"
        except Exception as e:
            _isOk = False
            _reason = f"文本包含断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_text_matches(response: requests.Response, pattern: str):
        """
        断言响应文本匹配正则表达式
        
        Args:
            response: 响应对象
            pattern: 正则表达式模式
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            if re.search(pattern, response.text):
                _isOk = True
                _reason = f"文本匹配断言通过: 响应匹配正则表达式 '{pattern}'"
            else:
                _isOk = False
                _reason = f"文本匹配断言失败: 响应不匹配正则表达式 '{pattern}'"
        except Exception as e:
            _isOk = False
            _reason = f"文本匹配断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_cookies_contain(response: requests.Response, cookie_name: str):
        """
        断言响应包含指定cookie
        
        Args:
            response: 响应对象
            cookie_name: cookie名称
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            if cookie_name in response.cookies:
                _isOk = True
                _reason = f"Cookie断言通过: 响应中包含cookie '{cookie_name}'"
            else:
                _isOk = False
                _reason = f"Cookie断言失败: 响应中不包含cookie '{cookie_name}'"
        except Exception as e:
            _isOk = False
            _reason = f"Cookie断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_cookie_value(response: requests.Response, cookie_name: str, expected_value: str):
        """
        断言指定cookie的值
        
        Args:
            response: 响应对象
            cookie_name: cookie名称
            expected_value: 期望值
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            cookie_value = response.cookies.get(cookie_name)
            if str(cookie_value) == str(expected_value):
                _isOk = True
                _reason = f"Cookie值断言通过: '{cookie_name}' 期望 {expected_value}，实际 {cookie_value}"
            else:
                _isOk = False
                _reason = f"Cookie值断言失败: '{cookie_name}' 期望 {expected_value}，实际 {cookie_value}"
        except Exception as e:
            _isOk = False
            _reason = f"Cookie值断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_response_size(response: requests.Response, min_size: int = None, max_size: int = None):
        """
        断言响应大小
        
        Args:
            response: 响应对象
            min_size: 最小大小（字节）
            max_size: 最大大小（字节）
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            content_length = len(response.content)
            
            if min_size is not None and content_length < min_size:
                _isOk = False
                _reason = f"响应大小断言失败: 实际 {content_length} 字节 < 最小值 {min_size} 字节"
            elif max_size is not None and content_length > max_size:
                _isOk = False
                _reason = f"响应大小断言失败: 实际 {content_length} 字节 > 最大值 {max_size} 字节"
            else:
                _isOk = True
                _reason = f"响应大小断言通过: {content_length} 字节"
                if min_size is not None:
                    _reason += f" >= {min_size}"
                if max_size is not None:
                    _reason += f" <= {max_size}"
        except Exception as e:
            _isOk = False
            _reason = f"响应大小断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_json_structure(response: requests.Response, expected_structure: Dict[str, Any]):
        """
        断言JSON结构
        
        Args:
            response: 响应对象
            expected_structure: 期望的JSON结构
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        def check_structure(data: Any, structure: Any, path: str = ""):
            if isinstance(structure, dict):
                if not isinstance(data, dict):
                    raise AssertionError(f"路径 '{path}' 期望字典类型")
                for key, expected_type in structure.items():
                    if key not in data:
                        raise AssertionError(f"路径 '{path}' 缺少键 '{key}'")
                    check_structure(data[key], expected_type, f"{path}.{key}" if path else key)
            elif isinstance(structure, list):
                if not isinstance(data, list):
                    raise AssertionError(f"路径 '{path}' 期望列表类型")
                if data and isinstance(structure[0], (dict, list)):
                    check_structure(data[0], structure[0], f"{path}[0]")
            elif isinstance(structure, type):
                if not isinstance(data, structure):
                    raise AssertionError(f"路径 '{path}' 期望类型 {structure.__name__}")
        
        try:
            data = response.json()
            check_structure(data, expected_structure)
            _isOk = True
            _reason = "JSON结构断言通过: 响应数据结构符合预期"
        except json.JSONDecodeError as e:
            _isOk = False
            _reason = f"JSON结构断言失败: JSON解析错误 - {str(e)}"
        except AssertionError as e:
            _isOk = False
            _reason = f"JSON结构断言失败: {str(e)}"
        except Exception as e:
            _isOk = False
            _reason = f"JSON结构断言失败: {str(e)}"
        return _isOk, _reason
    
    @staticmethod
    def assert_custom(response: requests.Response, assertion_func, *args, **kwargs):
        """
        自定义断言
        
        Args:
            response: 响应对象
            assertion_func: 断言函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            tuple: (是否成功, 断言结果信息)
        """
        try:
            result = assertion_func(response, *args, **kwargs)
            if result is not None:
                if result:
                    _isOk = True
                    _reason = "自定义断言通过"
                else:
                    _isOk = False
                    _reason = "自定义断言失败: 自定义函数返回 False"
            else:
                _isOk = True
                _reason = "自定义断言通过: 无返回值"
        except Exception as e:
            _isOk = False
            _reason = f"自定义断言失败: {str(e)}"
        return _isOk, _reason 