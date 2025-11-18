# -*- coding: utf-8 -*-
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from setup_paths import init_paths
init_paths()
from config.config_loader import get_env_var_value
from common.initPath import LOGDIR

class Log(object):
    """
    日志管理类
    使用单例模式，确保整个应用只有一个日志实例
    """
    _instance = None
    _lock = threading.Lock()
    _logger = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Log, cls).__new__(cls)
        return cls._instance

    @classmethod
    def getMylog(cls):
        """
        获取日志实例（保持原有接口不变）
        
        Returns:
            logging.Logger: 配置好的日志实例
        """
        if cls._logger is None:
            with cls._lock:
                if cls._logger is None:
                    cls._logger = cls._create_logger()
        return cls._logger
    
    @classmethod
    def _create_logger(cls):
        """
        创建并配置日志实例
        
        Returns:
            logging.Logger: 配置好的日志实例
        """
        try:
            # 从新配置系统获取日志等级配置
            log_level_str = get_env_var_value('log', 'level')
            if log_level_str:
                level = getattr(logging, log_level_str.upper(), logging.INFO)
            else:
                level = logging.INFO
            
            # 创建日志实例
            logger = logging.getLogger('DJ')
            
            # 如果已经有处理器，说明已经初始化过了，直接返回
            if logger.handlers:
                return logger
            
            # 设置日志等级
            logger.setLevel(level)
            
            # 确保日志目录存在
            cls._ensure_log_directory()
            
            # 创建文件处理器
            file_handler = cls._create_file_handler(level)
            if file_handler:
                logger.addHandler(file_handler)
            
            # 根据配置决定是否添加控制台输出
            console_enabled = get_env_var_value('log', 'console_enabled')
            if console_enabled and console_enabled.lower() == 'true':
                console_handler = cls._create_console_handler(level)
                if console_handler:
                    logger.addHandler(console_handler)
            
            # 防止日志向上传播，避免重复输出
            logger.propagate = False
            
            return logger
            
        except Exception as e:
            # 如果日志配置失败，创建一个基本的日志实例
            fallback_logger = logging.getLogger('DJ_FALLBACK')
            fallback_logger.setLevel(logging.INFO)
            if not fallback_logger.handlers:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
                ))
                fallback_logger.addHandler(console_handler)
                fallback_logger.propagate = False
            
            fallback_logger.error(f"日志配置失败，使用默认配置: {str(e)}")
            return fallback_logger
    
    @staticmethod
    def _ensure_log_directory():
        """确保日志目录存在"""
        try:
            if not os.path.exists(LOGDIR):
                os.makedirs(LOGDIR, exist_ok=True)
        except Exception as e:
            print(f"创建日志目录失败: {str(e)}")
    
    @staticmethod
    def _create_file_handler(level):
        """
        创建文件处理器
        
        Args:
            level: 日志等级
            
        Returns:
            TimedRotatingFileHandler: 文件处理器
        """
        try:
            # 从配置读取日志文件名，默认为 'log'
            log_filename = get_env_var_value('log', 'filename') or 'log.log'
            # 去掉扩展名，因为 TimedRotatingFileHandler 会自动添加
            log_name = log_filename.rsplit('.', 1)[0] if '.' in log_filename else log_filename
            
            # 🔧 支持并发执行：如果是 worker 进程，使用独立的日志文件
            worker_id = os.getenv('WORKER_ID')
            if worker_id:
                log_name = f"{log_name}.worker_{worker_id}"
            
            log_path = os.path.join(LOGDIR, log_name)
            
            # 从配置读取轮转参数
            when = get_env_var_value('log', 'when') or 'D'
            backup_count = get_env_var_value('log', 'backup_count') or 30
            try:
                backup_count = int(backup_count)
            except (ValueError, TypeError):
                backup_count = 30
            
            # 创建时间轮转文件处理器
            file_handler = TimedRotatingFileHandler(
                filename=log_path,
                when=when,
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
            
            # 设置历史日志文件名格式
            file_handler.suffix = "%Y-%m-%d.log"
            file_handler.setLevel(level)
            
            # 从配置读取日志格式
            log_format = get_env_var_value('log', 'format') or '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
            formatter = logging.Formatter(
                log_format,
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            return file_handler
            
        except Exception as e:
            print(f"创建文件处理器失败: {str(e)}")
            return None
    
    @staticmethod
    def _create_console_handler(level):
        """
        创建控制台处理器
        
        Args:
            level: 日志等级
            
        Returns:
            StreamHandler: 控制台处理器
        """
        try:
            # 🔧 确保控制台使用 UTF-8 编码，避免 emoji 字符显示问题
            # 如果 stdout 有 buffer 属性（Python 3），使用 UTF-8 包装
            if hasattr(sys.stdout, 'buffer'):
                import io
                console_stream = io.TextIOWrapper(
                    sys.stdout.buffer, 
                    encoding='utf-8', 
                    errors='replace',
                    line_buffering=True
                )
                console_handler = logging.StreamHandler(console_stream)
            else:
                # 否则使用默认的 stdout
                console_handler = logging.StreamHandler()
            
            console_handler.setLevel(level)
            
            # 控制台使用简化格式（不显示模块名，更简洁）
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s: %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            return console_handler
            
        except Exception as e:
            print(f"创建控制台处理器失败: {str(e)}")
            return None


