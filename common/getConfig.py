import os
from configparser import ConfigParser
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
from common.initPath import CONFDIR

"""
定义Config继续ConfigParser
"""


class Config(ConfigParser):

    def __init__(self):
        """
        初始化
        将配置文件读取出来
        super().    调用父类
        """
        self.conf_name = os.path.join(CONFDIR, 'baseCon.ini')
        super().__init__()
        super().read(self.conf_name, encoding='utf-8')

    def getAllsections(self):
        """
        :return: 返回所有的节点名称
        """
        return super().sections()

    def getOptions(self, sectioName):
        """
        :param sectioName: 节点名称
        :return: 返回节点所有的key
        """
        return super().options(sectioName)

    def getItems(self, sectioName):
        """
        :param sectioName: 节点名称
        :return: 返回节点的所有item
        """
        return super().items(sectioName)

    def getValue(self, sectioName, key):
        """
        :param sectioName: 节点的名称
        :param key: key名称
        :return: 返回sectioName下key 的value
        """
        return super().get(sectioName, key)

    def saveData(self, sectioName, key, value):
        """
        添加配置
        :param sectioName: 节点名称
        :param key: key名
        :param value: 值
        :return:
        """
        super().set(section=sectioName, option=key, value=value)
        super().write(fp=open(self.conf_name, 'w'))


myCof = Config()
# print(myCof.getAllsections())
# print(myCof.getOptions('db'))
# print(myCof.getItems('db'))
# print(myCof.getValue('db', 'host'))
# # myCof.saveData('db', 'newKey', 'newValue')