# -*- coding: utf-8 -*-
"""
HTTP状态码处理器
用于统一处理不同HTTP状态码的响应逻辑
"""
from typing import Dict, Tuple, Any
import json
import requests


class HTTPStatusHandler:
    """HTTP状态码处理器"""
    
    def __init__(self):
        self.status_handlers = {
            '200': self._handle_200,
            '201': self._handle_201,
            '204': self._handle_204,
            '400': self._handle_400,
            '401': self._handle_401,
            '403': self._handle_403,
            '404': self._handle_404,
            '500': self._handle_500,
            '502': self._handle_502,
            '503': self._handle_503,
        }
    
    def handle_status_code(self, response: requests.Response, case: Dict[str, Any], 
                          timer: float, method_factory) -> Tuple[bool, str]:
        """
        处理HTTP状态码
        
        Args:
            response: HTTP响应对象
            case: 测试用例数据
            timer: 响应时间
            method_factory: 方法工厂实例
            
        Returns:
            Tuple[bool, str]: (是否成功, 日志信息)
        """
        code = str(response.status_code)
        handler = self.status_handlers.get(code, self._handle_unknown_status)
        return handler(response, case, timer, method_factory)
    
    def _handle_200(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理200状态码 - 成功响应"""
        title = case['title']
        
        # 处理响应内容
        try:
            res = json.dumps(response.json(), ensure_ascii=False)
            method_factory(method='设置变量', result='response', param_1=res)
        except ValueError:
            res = response.text
            method_factory(method='设置变量', result='response', param_1=res)
        
        # 执行断言
        if not case.get('assertions'):
            is_ok = True
            reason = f'用例[{case["case_id"]}]：[{title}]执行完成,未添加断言.'
        else:
            from common.publicFunction import _execute_assertions
            is_ok, reason = _execute_assertions(response, **case)
        
        # 变量提取
        if not case.get('other'):
            variable_result = '无变量提取'
        else:
            from common.publicFunction import extract_variable
            variable_result = extract_variable(response, **case)
        # 生成日志信息
        if is_ok:
            log_msg = (f'接口名称：【{title}】-响应状态码[200]-接口响应时间[{timer:.2f} ms]-执行通过 ✅. '
                      f'\n 校验结果：{reason} \n 变量提取结果：{variable_result}')
        else:
            log_msg = (f'接口名称：【{title}】-响应状态码[200]-接口响应时间[{timer:.2f} ms]-执行不通过 ❌.\n原始响应为{response.text}\n不通过原因如下：\n {reason}')
        return is_ok, log_msg,reason
    
    def _handle_201(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理201状态码 - 创建成功"""
        title = case['title']
        log_msg = f'接口名称：【{title}】-响应状态码[201]-资源创建成功-接口响应时间[{timer:.2f} ms]'
        return True, log_msg
    
    def _handle_204(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理204状态码 - 无内容"""
        title = case['title']
        log_msg = f'接口名称：【{title}】-响应状态码[204]-无内容返回-接口响应时间[{timer:.2f} ms]'
        return True, log_msg
    
    def _handle_400(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理400状态码 - 请求错误"""
        is_ok = False
        title = case['title']
        reason = ''
        log_msg = f'接口名称：【{title}】-响应状态码[400]-请求参数错误\n{response.text}'
        return is_ok, log_msg,reason
    
    def _handle_401(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理401状态码 - 未授权"""
        title = case['title']
        log_msg = f'接口名称：【{title}】-响应状态码[401]-未授权访问\n{response.text}'
        return False, log_msg
    
    def _handle_403(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理403状态码 - 禁止访问"""
        title = case['title']
        log_msg = f'接口名称：【{title}】-响应状态码[403]-禁止访问\n{response.text}'
        return False, log_msg
    
    def _handle_404(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理404状态码 - 资源不存在"""
        is_ok = False
        title = case['title']
        reason = ''
        log_msg = f'接口名称：【{title}】-响应状态码[404]-接口地址不存在\n'
        return is_ok, log_msg,reason
    
    def _handle_500(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理500状态码 - 服务器内部错误"""
        is_ok = False
        title = case['title']
        reason = ''
        log_msg = f'接口名称：【{title}】-响应状态码[500]-服务器内部错误\n{response.text}'
        return is_ok, log_msg,reason
    
    def _handle_502(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理502状态码 - 网关错误"""
        title = case['title']
        log_msg = f'接口名称：【{title}】-响应状态码[502]-网关错误\n{response.text}'
        return False, log_msg
    
    def _handle_503(self, response: requests.Response, case: Dict[str, Any], 
                    timer: float, method_factory) -> Tuple[bool, str]:
        """处理503状态码 - 服务不可用"""
        title = case['title']
        log_msg = f'接口名称：【{title}】-响应状态码[503]-服务不可用\n{response.text}'
        return False, log_msg
    
    def _handle_unknown_status(self, response: requests.Response, case: Dict[str, Any], 
                              timer: float, method_factory) -> Tuple[bool, str]:
        """处理未知状态码"""
        title = case['title']
        code = response.status_code
        log_msg = f'接口名称：【{title}】-响应状态码[{code}]-未处理的状态码\n{response.text}'
        return False, log_msg 