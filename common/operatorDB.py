import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
import pymysql
from config.config_loader import get_env_var_value, get_env_now


class OpeartorDB(object):
    def __init__(self):
        """
        初始化方法，习惯性留着
        """
        self.database = get_env_var_value(get_env_now(), 'database')
        self.host = get_env_var_value(get_env_now(), 'host')
        self.port = get_env_var_value(get_env_now(), 'port')
        self.user = get_env_var_value(get_env_now(), 'user')
        self.password = get_env_var_value(get_env_now(), 'password')
        self.conn = None
        self.cursor = None

    def connectDB(self):
        """
        连接数据库
        :return: 返回成功失败，原因
        """
        try:
            self.db = pymysql.connect(host=self.host, port=int(self.port), user=self.user, password=self.password, database=self.database,
                                      charset='utf8')
            return True, '连接数据成功'
        except Exception as e:
            return False, '连接数据失败' + str(e) 

    def closeDB(self):
        """
        关闭数据连接，不关闭会导致数据连接数不能释放，影响数据库性能
        :return:
        """
        self.db.close()

    def excetSql(self, sql, table_name):
        """
        执行sql方法，
        :param table_name: 表名
        :param sql: 传入的sql语句
        :return: 返回成功与执行结果 或 失败与失败原因
        """
        isOK, result = self.connectDB()
        if isOK is False:
            return isOK, result
        try:
            cursor = self.db.cursor()
            cursor.execute(sql)
            res = cursor.fetchone()  # 为了自动化测试的速度，一般场景所以只取一条数据
            if res is not None and 'select' in sql.lower():  # 判断是不是查询，
                cursor.execute("DESCRIBE %s" % table_name)  # 替换table_name为实际表名
                columns = [column[0] for column in cursor.fetchall()]
                if len(columns) > 0:
                    result = dict(zip(columns, res))  # 将返回数据与字段名进行关联，格式化为JSON串
                else:
                    result = '查询结果为空或无法获取字段信息'
                # des = cursor.description[0]
                # result = dict(zip(des, res))  # 将返回数据格式化成JSON串
            elif res is None and ('insert' in sql.lower() or 'update' in sql.lower()):  # 判断是不是插入或者更新数据
                self.db.commit()  # 提交数据操作，不然插入或者更新，数据只会更新在缓存，没正式落库
                result = ''  # 操作数据，不需要返回数据
            cursor.close()  # 关闭游标
            self.closeDB()  # 关闭数据连接
            return True, result
        except Exception as e:
            return False, 'SQL执行失败,原因：[' + str(e) + ']'


if __name__ == "__main__":
    sql = "select * from idcsmart_addon_idcsmart_file_folder  where name='朱莉'"
    table_name = 'idcsmart_addon_idcsmart_file_folder'
    oper = OpeartorDB()
    isOK, result = oper.excetSql(sql, table_name)
    print(result)
