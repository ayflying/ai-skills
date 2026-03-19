---
name: baota-panel
description: 通过宝塔 (BT) 面板 API 管理服务器资源。支持创建网站、管理 Docker、数据库操作和文件浏览。当用户要求管理服务器、网站、Docker 容器或数据库时，请使用此技能。服务器地址为 192.168.50.243。
---

# 宝塔面板管理专家

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill baota-panel
```

## 核心功能
- **网站管理**：列出、创建、删除和管理站点。详见 [site.md](references/site.md)。
- **Docker 管理**：监控容器与管理 Compose。详见 [docker.md](references/docker.md)。
- **数据库管理**：管理 MySQL 数据库及用户。详见 [database.md](references/database.md)。
- **文件管理**：读写、上传、下载、压缩及回收站。详见 [files.md](references/files.md)。
- **系统与安全**：资源状态、软件安装更新、防火墙放行。详见 [system.md](references/system.md) 和 [security.md](references/security.md)。

## 使用指南
该技能依赖 Python 脚本 `scripts/bt_api.py` 处理 API 签名。

### 常用命令
通过 bash 执行辅助脚本：
- `python scripts/bt_api.py` - 获取系统概览
- `python scripts/bt_api.py sites` - 列出网站
- `python scripts/bt_api.py docker` - 容器状态
- `python scripts/bt_api.py read_file <路径>` - 读取文件

详见 [common.md](references/common.md) 了解 API 规范。

## 安全与最佳实践
- **强制确认**：**严禁擅自执行任何删除操作**。在执行删除或清空操作前，必须先告知用户并获得明确授权。
- **路径检查**：在管理文件时，确保路径正确，避免误删系统文件。
- **SSL 警告**：针对内网 IP 禁用了 SSL 验证。
