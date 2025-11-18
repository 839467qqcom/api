# -*- coding: utf-8 -*-
"""
通用路径设置模块
可以在项目的任何文件中导入使用，自动设置正确的导入路径
使用方法：在需要导入其他模块的文件开头添加以下代码：

# 自动设置项目路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from setup_paths import init_paths
init_paths()

# 然后就可以直接从目录名开始导入了
from config.config_loader import get_env_var_value
from common.publicFunction import replace_data
"""
import os
import sys
from config.config_loader import get_env_value

def init_paths(project_name=get_env_value('project_name')):
    """
    初始化项目路径，使导入更灵活
    
    Args:
        project_name (str): 项目名称，用于定位项目根目录
    """
    # 获取调用此函数的文件路径
    caller_file = sys._getframe(1).f_globals.get('__file__')
    if caller_file:
        current_dir = os.path.dirname(os.path.abspath(caller_file))
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找项目根目录
    project_root = find_project_root(current_dir, project_name)
    
    if project_root:
        # 添加项目根目录到 sys.path
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # 添加主要子目录到 sys.path，支持直接从子目录名开始导入
        subdirs = ['common', 'config', 'testcase', 'kemel', 'data', 'tools']
        for subdir in subdirs:
            subdir_path = os.path.join(project_root, subdir)
            if os.path.exists(subdir_path) and subdir_path not in sys.path:
                sys.path.insert(0, subdir_path)
        
        return project_root
    else:
        print(f"警告: 无法找到项目根目录 '{project_name}'")
        return None


def find_project_root(start_path, project_name=get_env_value('project_name')):
    """
    从给定路径开始向上查找项目根目录
    
    Args:
        start_path (str): 开始搜索的路径
        project_name (str): 项目名称
    
    Returns:
        str: 项目根目录路径，如果未找到返回None
    """
    current_path = os.path.abspath(start_path)
    
    while current_path and current_path != os.path.dirname(current_path):
        # 方法1: 检查目录名是否为项目名
        if os.path.basename(current_path) == project_name:
            return current_path
        
        # 方法2: 检查是否包含项目特征文件/目录
        project_markers = [
            'kemel'
        ]
        
        marker_count = 0
        for marker in project_markers:
            marker_path = os.path.join(current_path, marker)
            if os.path.exists(marker_path):
                marker_count += 1
        
        # 如果包含多个特征，很可能是项目根目录
        if marker_count >= 1:
            return current_path
        
        # 向上一级目录继续搜索
        current_path = os.path.dirname(current_path)
    
    return None


def get_project_root():
    """
    获取项目根目录路径
    """
    return find_project_root(os.path.dirname(os.path.abspath(__file__)))


# 如果直接运行此模块，执行初始化
if __name__ == "__main__":
    root = init_paths()
    if root:
        print(f"项目根目录: {root}")
        print(f"当前 sys.path: {sys.path[:5]}...")  # 只显示前5个路径
    else:
        print("未能找到项目根目录")