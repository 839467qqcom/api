# 配置系统使用指南

## 快速开始

### 首次使用

1. **创建环境配置文件**

```powershell
# Windows
cd D:\Python-file\pytestApi
Copy-Item .env.example .env
```

2. **编辑 .env 文件，填入真实配置**

```bash
# 设置当前环境
ENVIRONMENT=DCIMS

# 填入真实的数据库密码、管理员密码等
DCIMS_DB_PASSWORD=your_real_password
DCIMS_ADMIN_PASSWORD=your_real_password
```

3. **测试配置**

```powershell
python config\baseCon.py
```

### 日常使用

代码完全不需要改动，继续使用原有方式：

```python
from config.baseCon import get_env_now, get_env_var_value

# 获取当前环境
env = get_env_now()  # 'DCIMS'

# 获取配置值
host = get_env_var_value(env, 'host')
password = get_env_var_value(env, 'pwd')  # 会从 .env 读取
```

## 配置文件说明

```
config/
├── baseCon.py              # 配置入口，导入即用
├── config_loader.py        # 配置加载器（自动工作）
├── base.yaml               # 通用配置（项目名、日志等）
└── environments/           # 各环境配置
    ├── DCIMS.yaml         # DCIMS 环境（非敏感信息）
    ├── KFC.yaml
    └── ...
```

## 环境变量命名规范

格式：`{环境名大写}_{类型}_{字段}`

示例：
- `DCIMS_DB_PASSWORD` - DCIMS 环境数据库密码
- `V10_3_ADMIN_USERNAME` - v10-3 环境管理员用户名
- `EMAIL_PASSWORD` - 邮件密码（全局）

## 安全注意事项

⚠️ **绝对不要：**
1. 将 `.env` 文件提交到 Git
2. 在 YAML 文件中写敏感信息
3. 在代码中硬编码密码
4. 通过不安全渠道分享 `.env`

✅ **推荐做法：**
1. 每人维护自己的 `.env`
2. 使用 `.env.example` 作为模板
3. 通过密码管理工具分享敏感信息

## 故障排查

### 问题 1：提示使用传统配置系统

```
⚠ 使用传统配置系统（建议升级）
```

**原因：** `.env` 或 YAML 文件不存在

**解决：**
1. 检查 `.env` 是否存在
2. 检查 `base.yaml` 和 `environments/*.yaml` 是否存在

### 问题 2：配置读取失败

**解决步骤：**
1. 运行测试：`python config\baseCon.py`
2. 检查 `.env` 文件格式（KEY=VALUE，无空格）
3. 检查 YAML 文件语法（注意缩进）

### 问题 3：密码读取为空

**原因：** 环境变量名称不匹配

**解决：**
1. 检查 `.env` 中变量名是否正确
2. 环境名需大写，横线改下划线（如 `v10-3` → `V10_3`）

## 更多信息

详见项目根目录 `配置系统升级说明.md`

