---
name: baota-panel
description: |
  通过宝塔 (BT) 面板 API 管理服务器资源。支持网站管理、Docker 编排、数据库运维及文件管理。支持经授权的计划任务代理和面板登录态接口。
  Use when: (1) 需要管理宝塔面板上的网站 (2) 需要管理 Docker 容器和编排 (3) 需要管理数据库 (4) 需要远程操作服务器文件
---

# 宝塔面板管理专家

通过宝塔面板 API 实现对服务器的全面自动化管理。

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill baota-panel
```

## 准备工作 (Prerequisites)

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```
2. **配置认证**：
   - 复制 `.env.example` 为 `.env`。
   - 在宝塔面板中开启 API 接口，获取密钥并填入 `.env`。
   - 将当前 IP 加入宝塔 API 的 IP 白名单。

## 核心亮点

- **计划任务代理**：Shell 空响应且显式授权 `allow_crontab_fallback=True` 时，才尝试创建、执行并清理临时计划任务。空响应不等于防火墙拦截，代理不保证成功。
- **登录态接口**：部分 Docker 接口依赖 `x-http-token`。默认不读服务器登录态；取得用户授权后才设置 `allow_session_access=True`。受面板版本、权限和会话有效期限制。
- **全能管理**：覆盖网站、FTP、数据库、Docker、文件系统及系统监控。

## 常用命令示例

### 1. 系统信息
```bash
python scripts/bt_api.py
```

### 2. Docker Compose 部署
```python
from scripts.bt_api import BTPanelAPI
api = BTPanelAPI(url, key)

# 确认目标、部署影响与授权后执行；默认不使用计划任务代理
api.docker_compose("/www/docker/myapp", "up")
```

### 3. 删除容器编排
```python
# 确认项目 ID、删除影响并取得用户明确授权后执行删除
api.delete_compose_project(1)
```

## 内部文档
- [API 规范与认证](references/common.md)
- [网站管理接口](references/site.md)
- [Docker 与 Compose 管理](references/docker.md)
- [数据库与 FTP](references/database.md)
- [文件系统操作](references/files.md)
- [系统与安全](references/system.md)

## 安全红线
- **严禁擅自执行删除操作**。在删除站点、数据库、编排项目或清空回收站前，必须获得用户明确授权。

- 执行 Shell、部署、读取登录态或改变安全策略前确认授权范围；接口拒绝时不得自行绕过安全策略。
- API Key、会话及业务响应不得写入日志或提交仓库。
