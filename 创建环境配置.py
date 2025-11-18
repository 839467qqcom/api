# -*- coding: utf-8 -*-
"""
环境配置文件创建脚本
快速创建并配置 .env 文件
"""
import os
from pathlib import Path


def create_env_file():
    """创建 .env 文件"""
    
    print("=" * 70)
    print("🚀 pytestApi 配置系统 - 环境配置向导")
    print("=" * 70)
    
    # 获取脚本所在目录
    current_dir = Path(__file__).parent
    env_file = current_dir / '.env'
    env_example = current_dir / '.env.example'
    
    # 检查 .env 是否已存在
    if env_file.exists():
        print(f"\n⚠️  发现已存在的 .env 文件")
        print(f"   位置: {env_file}")
        choice = input("\n是否要覆盖现有文件？(y/N): ").strip().lower()
        if choice != 'y':
            print("\n❌ 操作已取消")
            return
    
    # 检查 .env.example 是否存在
    if not env_example.exists():
        print(f"\n❌ 错误: 找不到模板文件 .env.example")
        print(f"   请确保项目结构完整")
        return
    
    print("\n📝 配置环境变量")
    print("-" * 70)
    
    # 选择环境
    print("\n可用环境:")
    environments = ['DCIMS', 'KFC', 'v10-2', 'v10-3', 'v10-4', 'my-2']
    for i, env in enumerate(environments, 1):
        print(f"  {i}. {env}")
    
    env_choice = input("\n请选择默认环境 (1-6) [默认: 1]: ").strip() or "1"
    try:
        env_index = int(env_choice) - 1
        selected_env = environments[env_index]
    except (ValueError, IndexError):
        selected_env = "DCIMS"
    
    print(f"✓ 已选择环境: {selected_env}")
    
    # 询问是否使用默认值
    print("\n" + "-" * 70)
    use_default = input("是否使用默认配置？(Y/n): ").strip().lower()
    
    if use_default != 'n':
        # 使用默认值（从原 baseCon.py 读取）
        print("\n✓ 使用默认配置创建 .env 文件...")
        create_env_with_defaults(env_file, selected_env)
    else:
        # 交互式配置
        print("\n⚠️  请注意：敏感信息将保存在 .env 文件中")
        print("   确保该文件不会被提交到 Git（已在 .gitignore 中）\n")
        create_env_interactive(env_file, selected_env)
    
    print("\n" + "=" * 70)
    print("✅ 配置完成！")
    print("=" * 70)
    print(f"\n📄 配置文件已创建: {env_file}")
    print("\n⚠️  重要提示:")
    print("   1. .env 文件包含敏感信息，请妥善保管")
    print("   2. 不要将此文件提交到 Git（已自动忽略）")
    print("   3. 不要通过不安全渠道分享此文件")
    print("\n🧪 测试配置:")
    print("   cd pytestApi")
    print("   python config\\baseCon.py")
    print("\n📖 详细文档:")
    print("   查看 '配置系统升级说明.md'")
    print("=" * 70)


def create_env_with_defaults(env_file: Path, environment: str):
    """使用默认值创建 .env 文件"""
    
    # 从原配置文件读取默认值
    from config.baseCon import ENV_VARS
    
    env_configs = {
        'KFC': ENV_VARS.get('KFC', {}),
        'v10-2': ENV_VARS.get('v10-2', {}),
        'v10-3': ENV_VARS.get('v10-3', {}),
        'v10-4': ENV_VARS.get('v10-4', {}),
        'my-2': ENV_VARS.get('my-2', {}),
        'DCIMS': ENV_VARS.get('DCIMS', {})
    }
    
    email_config = ENV_VARS.get('email', {})
    wechat_config = ENV_VARS.get('wechat', {})
    
    content = f"""# ========================================
# 环境变量配置文件（自动生成）
# ========================================
# 生成时间: 由配置脚本自动创建
# 注意：此文件包含敏感信息，不应提交到 Git

# ========================================
# 当前环境设置
# ========================================
ENVIRONMENT={environment}

"""
    
    # 添加所有环境配置
    for env_name, config in env_configs.items():
        env_prefix = env_name.upper().replace('-', '_')
        content += f"""# ========================================
# {env_name} 环境配置
# ========================================
{env_prefix}_DB_HOST={config.get('host', '')}
{env_prefix}_DB_PORT={config.get('port', 3306)}
{env_prefix}_DB_USER={config.get('user', '')}
{env_prefix}_DB_PASSWORD={config.get('pwd', '')}
{env_prefix}_DB_NAME={config.get('database', '')}
{env_prefix}_ADMIN_USERNAME={config.get('adminname', '')}
{env_prefix}_ADMIN_PASSWORD={config.get('adminpwd', '')}
{env_prefix}_CLIENT_USERNAME={config.get('clientname', '')}
{env_prefix}_CLIENT_PASSWORD={config.get('clientpwd', '')}

"""
    
    # 添加邮件配置
    content += f"""# ========================================
# 邮件配置
# ========================================
EMAIL_HOST={email_config.get('host', 'smtp.qq.com')}
EMAIL_PORT={email_config.get('port', 465)}
EMAIL_USER={email_config.get('user', '')}
EMAIL_PASSWORD={email_config.get('pwd', '')}
EMAIL_FROM_ADDR={email_config.get('from_addr', '')}
EMAIL_TO_ADDR={email_config.get('to_addr', '')}

"""
    
    # 添加企业微信配置
    content += f"""# ========================================
# 企业微信配置
# ========================================
WECHAT_CORPID={wechat_config.get('corpid', '')}
WECHAT_CORPSECRET={wechat_config.get('corpsecret', '')}
WECHAT_AGENTID={wechat_config.get('agentid', '')}
"""
    
    # 写入文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ 已从原配置迁移所有环境的配置")


def create_env_interactive(env_file: Path, environment: str):
    """交互式创建 .env 文件"""
    
    env_prefix = environment.upper().replace('-', '_')
    
    print(f"\n配置 {environment} 环境:")
    
    # 数据库配置
    db_user = input(f"  数据库用户名: ").strip()
    db_password = input(f"  数据库密码: ").strip()
    db_name = input(f"  数据库名: ").strip()
    
    # 管理员配置
    admin_username = input(f"  管理员用户名: ").strip()
    admin_password = input(f"  管理员密码: ").strip()
    
    # 客户端配置
    client_username = input(f"  客户端用户名: ").strip()
    client_password = input(f"  客户端密码: ").strip()
    
    # 邮件配置
    print("\n邮件配置:")
    email_user = input(f"  邮箱地址: ").strip()
    email_password = input(f"  邮箱密码/授权码: ").strip()
    email_to = input(f"  收件人地址: ").strip()
    
    content = f"""# ========================================
# 环境变量配置文件
# ========================================

ENVIRONMENT={environment}

# {environment} 环境配置
{env_prefix}_DB_USER={db_user}
{env_prefix}_DB_PASSWORD={db_password}
{env_prefix}_DB_NAME={db_name}
{env_prefix}_ADMIN_USERNAME={admin_username}
{env_prefix}_ADMIN_PASSWORD={admin_password}
{env_prefix}_CLIENT_USERNAME={client_username}
{env_prefix}_CLIENT_PASSWORD={client_password}

# 邮件配置
EMAIL_HOST=smtp.qq.com
EMAIL_PORT=465
EMAIL_USER={email_user}
EMAIL_PASSWORD={email_password}
EMAIL_FROM_ADDR={email_user}
EMAIL_TO_ADDR={email_to}

# 企业微信配置（可选）
WECHAT_CORPID=
WECHAT_CORPSECRET=
WECHAT_AGENTID=
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\n❌ 操作已取消")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

