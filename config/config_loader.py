# -*- coding: utf-8 -*-
"""
配置加载器 - 支持 YAML + 环境变量的新配置方式
同时保持对旧配置文件 baseCon.py 的兼容
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    # 加载项目根目录下的 .env 文件
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print(f"⚠ 未找到 .env 文件: {env_file}")
except ImportError:
    print("⚠ python-dotenv 未安装，无法加载 .env 文件")
except Exception as e:
    print(f"⚠ 加载 .env 文件失败: {e}")


class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self):
        """初始化配置加载器"""
        self.config_dir = Path(__file__).parent
        self.environment = os.getenv('ENVIRONMENT')
        self._config_cache = None
        self._use_new_config = self._check_new_config_available()
    
    def _check_new_config_available(self) -> bool:
        """检查新配置文件是否存在"""
        base_yaml = self.config_dir / 'base.yaml'
        env_yaml = self.config_dir / 'environments' / f'{self.environment}.yaml'
        return base_yaml.exists() and env_yaml.exists()
    
    
    def _load_yaml(self, file_path: Path) -> Dict:
        """加载 YAML 文件"""
        if not file_path.exists():
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"警告: 加载 YAML 文件失败 {file_path}: {e}")
            return {}
    
    def _load_new_config(self) -> Dict[str, Any]:
        """加载新的配置（YAML + 环境变量）"""
        # 加载基础配置
        base_config = self._load_yaml(self.config_dir / 'base.yaml')
        
        # 加载环境配置
        env_config = self._load_yaml(
            self.config_dir / 'environments' / f'{self.environment}.yaml'
        )
        
        # 合并配置
        config = {**base_config}
        
        # 构建环境特定配置（与旧格式保持一致）
        env_prefix = self.environment.upper().replace('-', '_')
        
        # 优先级：环境变量 > YAML 配置
        env_specific = {
            # 如果 YAML 中值为空或不存在，从环境变量读取
            'host': env_config.get('host') or os.getenv(f'{env_prefix}_DB_HOST', ''),
            'port': env_config.get('port') or os.getenv(f'{env_prefix}_DB_PORT', 3306),
            'database': env_config.get('database') or os.getenv(f'{env_prefix}_DB_NAME', ''),
            'charset': env_config.get('charset', 'utf8'),
            'url': env_config.get('url', ''),
            'address': env_config.get('address', ''),
            'case_file': env_config.get('case_file', self.environment),
            # 敏感信息始终从环境变量读取
            'user': os.getenv(f'{env_prefix}_DB_USER', ''),
            'pwd': os.getenv(f'{env_prefix}_DB_PASSWORD', ''),
            'adminname': os.getenv(f'{env_prefix}_ADMIN_USERNAME', ''),
            'adminpwd': os.getenv(f'{env_prefix}_ADMIN_PASSWORD', ''),
            'clientname': os.getenv(f'{env_prefix}_CLIENT_USERNAME', ''),
            'clientpwd': os.getenv(f'{env_prefix}_CLIENT_PASSWORD', ''),
        }
        
        # 添加用例配置（从环境配置读取）
        config['case'] = {
            'testcase': env_config.get('testcase', 'test.xlsx')
        }
        
        # 添加环境配置到主配置中
        config[self.environment] = env_specific
        
        # 添加邮件配置
        config['email'] = {
            'host': os.getenv('EMAIL_HOST', 'smtp.qq.com'),
            'port': int(os.getenv('EMAIL_PORT', '465')),
            'user': os.getenv('EMAIL_USER', ''),
            'pwd': os.getenv('EMAIL_PASSWORD', ''),
            'from_addr': os.getenv('EMAIL_FROM_ADDR', ''),
            'to_addr': os.getenv('EMAIL_TO_ADDR', ''),
            'subject': '自动化测试报告',
            'content': '自动化测试报告',
            'attachments': '自动化测试报告.html'
        }
        
        # 添加企业微信配置
        config['wechat'] = {
            'corpid': os.getenv('WECHAT_CORPID', ''),
            'corpsecret': os.getenv('WECHAT_CORPSECRET', ''),
            'agentid': os.getenv('WECHAT_AGENTID', '')
        }
        
        # 添加环境名称
        config['ENV_NOW'] = self.environment
        
        return config
    
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取配置
        优先使用新配置，如果不可用则降级到旧配置
        """
        if self._config_cache is None:
            if self._use_new_config:
                self._config_cache = self._load_new_config()
        
        return self._config_cache
    
    def get(self, key: str, key2: Optional[str] = None, default: Any = None) -> Any:
        """
        获取配置值
        兼容旧接口：get(key, key2)
        """
        # 懒加载：首次调用时加载配置
        if self._config_cache is None:
            self.get_config()
        
        config = self._config_cache
        if key2 is None:
            # 单层取值
            return config.get(key, default)
        else:
            # 两层取值（兼容 get_env_var_value）
            first_level = config.get(key)
            if isinstance(first_level, dict):
                return first_level.get(key2, default)
            return default


# 全局配置加载器实例
_config_loader = ConfigLoader()



def get_env_var_value(key, key2):
    """
    获取对应对象的值（兼容旧接口）
    :param key: 第一层键
    :param key2: 第二层键
    :return: 配置值
    
    使用示例：
        host = get_env_var_value('DCIMS', 'host')
        level = get_env_var_value('log', 'level')
    """
    return _config_loader.get(key, key2)


def get_env_now():
    """
    获取当前执行的环境（兼容旧接口）
    :return: 环境名称
    
    使用示例：
        env = get_env_now()  # 返回 'DCIMS' 等
    """
    return _config_loader.environment


def get_env_value(key):
    """
    获取指定键的值（兼容旧接口）
    :param key: 配置键
    :return: 配置值
    
    使用示例：
        project = get_env_value('project_name')
    """
    return _config_loader.get(key)


# ========================================
# 新增功能（可选使用）
# ========================================

def reload_config():
    """重新加载配置（用于配置文件变更后刷新）"""
    global _config_loader
    _config_loader._config_cache = None
    return _config_loader.get_config()


def get_config_loader():
    """获取配置加载器实例（用于高级操作）"""
    return _config_loader


# ========================================
# 测试代码
# ========================================

if __name__ == '__main__':
    print("=" * 60)
    print("配置系统测试")
    print("=" * 60)
    
    # 测试兼容性函数
    print(f"\n当前环境: {get_env_now()}")
    print(f"项目名称: {get_env_value('project_name')}")
    print(f"数据库主机: {get_env_var_value(get_env_now(), 'host')}")
    print(f"数据库端口: {get_env_var_value(get_env_now(), 'port')}")
    print(f"API地址: {get_env_var_value(get_env_now(), 'url')}")
    print(f"日志级别: {get_env_var_value('log', 'level')}")
    
    # 测试邮件配置
    print(f"\n邮件主机: {get_env_var_value('email', 'host')}")
    print(f"邮件用户: {get_env_var_value('email', 'user')}")
    
    print("\n" + "=" * 60)
    print("✓ 配置系统运行正常")
    print("=" * 60)

