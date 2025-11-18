# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
from config.config_loader import get_env_var_value
from kemel.commKeyword import CommKeyword



class MethodFactory(object):

    def __init__(self):
        self.comKey = CommKeyword()

    def method_factory(self, **kwargs):

        if kwargs.__len__() > 0:
            try:
                kwargs['method']
            except KeyError:
                return False, 'keyword:用例[method]字段方法没参数为空.'
            try:
                method = get_env_var_value('commkey', kwargs['method'].lower())
            except KeyError:
                return False, 'keyword:方法[' + kwargs['method'] + '] 不存在,或未配置.'
        else:
            return False, '没有传参'
        try:
            func = getattr(self.comKey, method, None)
            _isOk, result = func(**kwargs)
            return _isOk, result
        except Exception as e:
            return False, 'keyword:执行失败，估计不存在，异常：' + str(e)


if __name__ == '__main__':
    fac = MethodFactory()
    print(fac.method_factory(method='获取当前用例文件名称'))



