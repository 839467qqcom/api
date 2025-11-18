# -*- coding: utf-8 -*-
"""
增强的数据加载器
支持多种数据源、缓存机制和数据验证
"""
import json
import yaml
import hashlib
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import openpyxl
import pandas as pd
from functools import lru_cache
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()

from common.initPath import DATADIR
from config.config_loader import get_env_now, get_env_var_value


class DataValidationError(Exception):
    """数据验证异常"""
    pass


class DataSourceNotSupportedError(Exception):
    """不支持的数据源异常"""
    pass


class DataCache:
    """数据缓存管理器"""
    
    def __init__(self, cache_ttl: int = 300):
        """
        初始化缓存管理器
        
        Args:
            cache_ttl: 缓存生存时间（秒），默认5分钟
        """
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_timestamps = {}
    
    def _generate_cache_key(self, file_path: str, sheet_name: Optional[str] = None) -> str:
        """生成缓存键"""
        key_parts = [file_path]
        if sheet_name:
            key_parts.append(sheet_name)
        return hashlib.md5('_'.join(key_parts).encode()).hexdigest()
    
    def get(self, file_path: str, sheet_name: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """获取缓存数据"""
        cache_key = self._generate_cache_key(file_path, sheet_name)
        
        if cache_key in self._cache:
            # 检查缓存是否过期
            if time.time() - self._cache_timestamps[cache_key] < self.cache_ttl:
                return self._cache[cache_key]
            else:
                # 清除过期缓存
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
        
        return None
    
    def set(self, file_path: str, data: List[Dict[str, Any]], sheet_name: Optional[str] = None) -> None:
        """设置缓存数据"""
        cache_key = self._generate_cache_key(file_path, sheet_name)
        self._cache[cache_key] = data
        self._cache_timestamps[cache_key] = time.time()
    
    def clear(self) -> None:
        """清除所有缓存"""
        self._cache.clear()
        self._cache_timestamps.clear()
    
    def clear_expired(self) -> None:
        """清除过期缓存"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._cache_timestamps.items()
            if current_time - timestamp >= self.cache_ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
            del self._cache_timestamps[key]


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_case_structure(case: Dict[str, Any]) -> bool:
        """
        验证测试用例结构
        
        Args:
            case: 测试用例数据
            
        Returns:
            bool: 验证是否通过
        """
        required_fields = ['case_id', 'title', 'method', 'url']
        optional_fields = ['headers', 'data', 'expected', 'checkey', 'assertpath', 'other']
        
        # 检查必需字段
        for field in required_fields:
            if field not in case or case[field] is None:
                raise DataValidationError(f"缺少必需字段: {field}")
        
        # 验证字段类型
        if not isinstance(case['case_id'], (str, int)):
            raise DataValidationError("case_id必须是字符串或整数")
        
        if not isinstance(case['title'], str):
            raise DataValidationError("title必须是字符串")
        
        if not isinstance(case['method'], str):
            raise DataValidationError("method必须是字符串")
        
        if not isinstance(case['url'], str):
            raise DataValidationError("url必须是字符串")
        
        return True
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证URL格式"""
        if not url or not isinstance(url, str):
            return False
        
        # 简单的URL格式验证
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        return True
    
    @staticmethod
    def validate_http_method(method: str) -> bool:
        """验证HTTP方法"""
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        return method.upper() in valid_methods


class EnhancedDataLoader:
    """增强的数据加载器"""
    
    def __init__(self, cache_ttl: int = 300):
        """
        初始化数据加载器
        
        Args:
            cache_ttl: 缓存生存时间（秒）
        """
        self.cache = DataCache(cache_ttl)
        self.validator = DataValidator()
        self.note = get_env_var_value('identifier', 'note')
        self.logger = logging.getLogger(__name__)
        self._custom_file_path = None  # 用于并发执行时动态设置文件路径
        
        # 支持的数据源处理器
        self.data_handlers = {
            '.xlsx': self._load_excel,
            '.xls': self._load_excel,
            '.json': self._load_json,
            '.yaml': self._load_yaml,
            '.yml': self._load_yaml,
            '.csv': self._load_csv,
        }
    
    def set_case_file(self, file_path: str) -> None:
        """
        动态设置要加载的测试文件（用于并发执行）
        
        Args:
            file_path: 测试文件的完整路径
        """
        self._custom_file_path = file_path
        self.logger.info(f"设置自定义测试文件: {file_path}")
    
    def load_test_cases(self, file_path: Optional[str] = None, 
                       sheet_name: Optional[str] = None,
                       use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        加载测试用例
        
        Args:
            file_path: 文件路径，如果为None则使用配置文件中的路径或自定义路径
            sheet_name: Excel工作表名称，仅对Excel文件有效
            use_cache: 是否使用缓存
            
        Returns:
            List[Dict[str, Any]]: 测试用例列表
        """
        # 优先级: file_path参数 > 自定义文件路径 > 配置文件路径
        if file_path is None:
            if self._custom_file_path:
                # 使用自定义文件路径（并发执行模式）
                file_path = self._custom_file_path
            else:
                # 使用配置文件路径（标准模式）
                filename = get_env_var_value('case', 'testcase')
                file_path = os.path.join(DATADIR, get_env_var_value(get_env_now(),'case_file'), filename)
            # print(file_path)  # 注释掉调试输出
        
        # 检查缓存
        if use_cache:
            cached_data = self.cache.get(file_path, sheet_name)
            if cached_data:
                self.logger.info(f"从缓存加载数据: {file_path}")
                return cached_data
        
        # 获取文件扩展名
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.data_handlers:
            raise DataSourceNotSupportedError(f"不支持的文件格式: {file_ext}")
        
        # 加载数据
        try:
            cases = self.data_handlers[file_ext](file_path, sheet_name)
            
            # 验证数据
            validated_cases = []
            for case in cases:
                try:
                    self.validator.validate_case_structure(case)
                    validated_cases.append(case)
                except DataValidationError as e:
                    self.logger.warning(f"跳过无效用例 {case.get('case_id', 'unknown')}: {e}")
            
            # 缓存数据
            if use_cache:
                self.cache.set(file_path, validated_cases, sheet_name)
            
            self.logger.info(f"成功加载 {len(validated_cases)} 个测试用例")
            return validated_cases
            
        except Exception as e:
            self.logger.error(f"加载测试用例失败: {e}")
            raise
    
    def _load_excel(self, file_path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """加载Excel文件"""
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True)
            cases = []
            
            if sheet_name:
                # 加载指定工作表
                if sheet_name in wb.sheetnames:
                    cases = self._process_excel_sheet(wb[sheet_name])
                else:
                    raise DataValidationError(f"工作表 '{sheet_name}' 不存在")
            else:
                # 加载所有工作表
                for sheet in wb.worksheets:
                    if sheet.title[0] != self.note:  # 过滤注释的工作表
                        sheet_cases = self._process_excel_sheet(sheet)
                        cases.extend(sheet_cases)
            
            wb.close()
            return cases
            
        except Exception as e:
            raise DataValidationError(f"Excel文件加载失败: {e}")
    
    def _process_excel_sheet(self, sheet) -> List[Dict[str, Any]]:
        """处理Excel工作表"""
        cases = []
        rows = list(sheet.rows)
        
        if not rows:
            return cases
        
        # 获取标题行
        headers = [cell.value for cell in rows[0]]
        
        # 处理数据行
        for row in rows[1:]:
            row_data = [cell.value for cell in row]
            case = dict(zip(headers, row_data))
            
            # 过滤注释的用例
            # if case.get('case_id') and str(case['case_id'])[0] != self.note:
            case['sheet'] = sheet.title
            cases.append(case)
        
        return cases
    
    def _load_json(self, file_path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # 如果JSON是对象格式，尝试提取测试用例
                if 'test_cases' in data:
                    return data['test_cases']
                elif 'cases' in data:
                    return data['cases']
                else:
                    raise DataValidationError("JSON文件格式不正确，应为数组或包含test_cases/cases字段的对象")
            else:
                raise DataValidationError("JSON文件格式不正确")
                
        except Exception as e:
            raise DataValidationError(f"JSON文件加载失败: {e}")
    
    def _load_yaml(self, file_path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """加载YAML文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # 如果YAML是对象格式，尝试提取测试用例
                if 'test_cases' in data:
                    return data['test_cases']
                elif 'cases' in data:
                    return data['cases']
                else:
                    raise DataValidationError("YAML文件格式不正确，应为数组或包含test_cases/cases字段的对象")
            else:
                raise DataValidationError("YAML文件格式不正确")
                
        except Exception as e:
            raise DataValidationError(f"YAML文件加载失败: {e}")
    
    def _load_csv(self, file_path: str, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """加载CSV文件"""
        try:
            df = pd.read_csv(file_path)
            cases = []
            
            for _, row in df.iterrows():
                case = row.to_dict()
                # 过滤注释的用例
                if case.get('case_id') and str(case['case_id'])[0] != self.note:
                    cases.append(case)
            
            return cases
            
        except Exception as e:
            raise DataValidationError(f"CSV文件加载失败: {e}")
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return list(self.data_handlers.keys())
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            'cache_size': len(self.cache._cache),
            'cache_ttl': self.cache.cache_ttl,
            'supported_formats': self.get_supported_formats()
        }
