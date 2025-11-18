# 导入os包
import os

def get_project_path():
    """
    获取项目目录
    :return:
    """
    # api_auto_test为项目名称，可以自行调整
    project_name = "pytestApi"
    # 获取当前项目路径
    file_path = os.path.dirname(__file__)
    # 因为file_path返回的是当前文件所在位置的目录，而我们需要项目的跟目录
    # 所以这里使用切片，把返回的路径切片到刚好为根目录的地方（方法不唯一）
    a = file_path[:file_path.find(project_name) + len(project_name)]
    return a


def sep(path, add_sep_before=False, add_sep_after=False):
    """
    拼接文件路径，添加系统分隔符
    :param path: 路径列表，类型为数组  ["config","environment.yaml"]
    :param add_sep_before: 是否需要在拼接的路径前加一个分隔符
    :param add_sep_after: 是否需要再拼接的路径后加一个分隔符
    :return:
    """
    # 拼接传入的数组
    all_path = os.sep.join(path)
    # 如果before为TRUE，那就在路径前面加“/”
    if add_sep_before:
        all_path = os.sep + all_path
    # 如果after为TRUE，那就在路径后面加“/”
    if add_sep_after:
        all_path = all_path + os.sep
    return all_path

if __name__ == '__main__':
    # 测试一下
    print(get_project_path())
    print(sep(["config","environment.yaml"], add_sep_before=True))

