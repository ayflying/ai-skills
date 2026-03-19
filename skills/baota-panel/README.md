# Baota Panel (宝塔面板管理)

通过宝塔面板 API 管理服务器资源，包括网站、Docker 容器、数据库和文件系统。

## 安装

### 标准化安装 (推荐)

使用 `skills` CLI 一键安装：

```bash
npx skills add ayflying/ai-skills --skill baota-panel
```

### 手动安装

1. **克隆仓库**:
   ```bash
   git clone https://github.com/ayflying/ai-skills.git
   cd ai-skills/skills/baota-panel
   ```

2. **配置环境**:
   复制 `.env.example` 为 `.env` 并填写 `BT_API_KEY`:
   ```bash
   cp .env.example .env
   ```

3. **安装依赖**:
   ```bash
   pip install requests urllib3
   ```

## 使用方式

直接运行 Python 脚本执行相关操作：

```bash
# 获取系统状态
python scripts/bt_api.py

# 列出所有网站
python scripts/bt_api.py sites

# 查看 Docker 容器
python scripts/bt_api.py docker

# 列出数据库
python scripts/bt_api.py databases

# 浏览文件
python scripts/bt_api.py files /www/wwwroot
```

## 功能特性

- ✅ **系统概览**: 实时检查 CPU、内存、负载。
- ✅ **网站管理**: 列表显示及基础运维。
- ✅ **容器化**: 支持 Docker 容器的状态监控与控制。
- ✅ **数据库**: 快速查看和管理 MySQL 数据库。
- ✅ **文件管理**: 远程文件系统浏览。

## 许可证

MIT License
