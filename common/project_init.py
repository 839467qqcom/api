# -*- coding: utf-8 -*-
"""
项目路径自动设置模块
支持灵活的项目路径导入，适用于多项目环境
"""
import os
import sys
from pathlib import Path


def setup_project_path(project_name="pytestApi", auto_detect=True):
    """
    自动设置项目路径，支持从任意子目录开始导入
    
    Args:
        project_name (str): 项目名称
        auto_detect (bool): 是否自动检测项目根目录
    
    Returns:
        str: 项目根目录路径
    """
    # 获取当前文件的绝对路径
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    project_root = None
    
    if auto_detect:
        # 方法1：向上搜索，查找项目根目录特征
        search_dir = current_dir
        while search_dir and search_dir != os.path.dirname(search_dir):
            # 检查项目特征文件/目录
            project_markers = [
                'pytest.ini', 'run.py', '__init__.py',
                os.path.join('testcase'),
                os.path.join('common'),
                os.path.join('config')
            ]
            
            # 如果当前目录包含多个项目特征，很可能是项目根目录
            marker_count = sum(1 for marker in project_markers 
                             if os.path.exists(os.path.join(search_dir, marker)))
            
            if marker_count >= 2:  # 至少包含2个特征文件/目录
                project_root = search_dir
                break
            
            # 如果目录名就是项目名
            if os.path.basename(search_dir) == project_name:
                project_root = search_dir
                break
                
            search_dir = os.path.dirname(search_dir)
    
    # 如果自动检测失败，使用相对路径
    if not project_root:
        # 从common目录回到项目根目录（假设当前在common目录）
        if current_dir.endswith('common'):
            project_root = os.path.dirname(current_dir)
        else:
            # 其他情况，向上查找
            project_root = current_dir
            while project_root and not os.path.exists(os.path.join(project_root, 'common')):
                parent = os.path.dirname(project_root)
                if parent == project_root:  # 到达根目录
                    break
                project_root = parent
    
    # 添加项目根目录到sys.path
    if project_root and project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # 添加主要子目录到sys.path，支持直接导入
    if project_root:
        subdirs = ['common', 'config', 'testcase', 'kemel', 'data', 'tools']
        for subdir in subdirs:
            subdir_path = os.path.join(project_root, subdir)
            if os.path.exists(subdir_path) and subdir_path not in sys.path:
                sys.path.insert(0, subdir_path)
    
    return project_root


def get_project_root():
    """
    获取项目根目录（简化版本）
    """
    return setup_project_path()


# 在模块导入时自动执行路径设置
_project_root = setup_project_path()