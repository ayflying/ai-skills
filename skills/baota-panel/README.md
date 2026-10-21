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
   python -m pip install -r requirements.txt
   ```

## 证书与授权

- 默认校验 HTTPS 证书。自签名面板需先核验可信 CA，再通过环境变量或 `.env` 的 `BT_CA_BUNDLE` 配置 CA 文件路径；Python 调用也可传 `ca_bundle="/path/to/ca.pem"`。
- 普通 API 不读取登录态、不创建代理计划任务。部分 Docker 内部接口需要登录态，默认 CLI 将返回未授权提示；确认授权后，Python 调用使用 `BTPanelAPI(url, key, allow_session_access=True)`。
- Shell 空响应不代表防火墙拦截。仅在确认目标、安全策略和创建/执行/清理计划任务的授权后设置 `allow_crontab_fallback=True`；不保证代理成功。
- 删除、清空、部署和执行 Shell 前确认影响与授权；不记录凭证、会话和原始错误响应。

## 使用方式

直接运行 Python 脚本执行相关操作：

```bash
# 获取系统状态
python scripts/bt_api.py

# 列出所有网站
python scripts/bt_api.py sites

# 查看 Docker 容器（需要登录态时改用上方已授权的 Python 调用）
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
- ✅ **文件管理**: 远程文件系统读写与传输。

## 技术文档

该技能深度集成了宝塔面板 API，详细的接口定义（路径、参数、响应格式）请参阅：

- [公共规范](references/common.md) - 认证与 Token 生成
- [网站管理](references/site.md) - 增删改查、SSL
- [文件管理](references/files.md) - 目录、读写、Shell
- [Docker 管理](references/docker.md) - 容器与 Compose
- [系统管理](references/system.md) - 资源状态、软件安装与更新
- [数据库管理](references/database.md) - 数据库增删改
- [安全管理](references/security.md) - 防火墙与 SSH
- [网站日志](references/site.md#11-获取网站日志) - 网站日志接口；面板日志使用 `get_panel_logs()`

## 许可证

MIT License
