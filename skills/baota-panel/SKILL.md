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
- **网站管理**：列出、创建、删除和管理 PHP/HTML 站点。
- **Docker 管理**：监控和控制 Docker 容器（容器列表、启动、停止）。
- **数据库管理**：管理 MySQL/MariaDB 数据库及用户。
- **文件管理**：浏览、读取和管理服务器上的文件。
- **系统状态**：检查服务器资源使用情况和运行状态。

## 使用指南
该技能依赖 Python 辅助脚本 `scripts/bt_api.py` 来处理复杂的 API 签名。

### 常用命令
通过 bash 执行辅助脚本：
- `python scripts/bt_api.py` - 获取系统概览信息
- `python scripts/bt_api.py sites` - 列出所有网站
- `python scripts/bt_api.py add_site <域名> <路径>` - 创建网站
- `python scripts/bt_api.py del_site <ID> <域名>` - 删除网站
- `python scripts/bt_api.py stop_site <ID> <域名>` - 停止网站
- `python scripts/bt_api.py ssl <域名> <ID>` - 申请 SSL 证书
- `python scripts/bt_api.py docker` - 列出 Docker 容器
- `python scripts/bt_api.py databases` - 列出所有数据库
- `python scripts/bt_api.py files <路径>` - 列出指定目录下的文件
- `python scripts/bt_api.py read_file <路径>` - 读取文件内容
- `python scripts/bt_api.py upload <本地路径> <远程路径>` - 上传文件
- `python scripts/bt_api.py download <远程路径> <本地路径>` - 下载文件

## 安全与最佳实践
- **操作确认**：在执行删除网站或数据库等破坏性操作前，请务必先征得用户同意。
- **路径检查**：在管理文件时，请确保路径正确，避免误删系统文件。
- **SSL 警告**：脚本针对内网 IP 禁用了 SSL 验证，请确保运行环境允许此操作。
