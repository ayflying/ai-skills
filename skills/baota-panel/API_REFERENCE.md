# Baota Panel API 接口文档

本文档列出了 `baota-panel` 技能中已实现的所有宝塔面板 API 接口。

## 1. 系统管理

### 获取系统概览信息
获取服务器资源使用情况（CPU、内存、负载、磁盘等）。
- **方法**: `get_system_info()`
- **辅助脚本命令**: `python scripts/bt_api.py`

### 获取插件/软件列表
列出宝塔面板安装的所有软件及其状态。
- **方法**: `get_plugins()`
- **辅助脚本命令**: `python scripts/bt_api.py plugins`

## 2. 网站管理

### 获取网站列表
- **方法**: `get_sites(page=1, limit=20)`
- **辅助脚本命令**: `python scripts/bt_api.py sites`
- **参数**:
  - `page`: 页码（默认 1）
  - `limit`: 每页数量（默认 20）

### 创建网站
- **方法**: `create_site(webname, path, ...)`
- **参数**:
  - `webname`: 网站域名
  - `path`: 网站根目录
  - `type`: 类型（默认 "PHP"）
  - `version`: PHP 版本（默认 "00" 表示静态）
  - `port`: 端口（默认 "80"）
  - `ps`: 备注
  - `ftp`: 是否开通 FTP（"true"/"false"）
  - `sql`: 是否开通 SQL 数据库（"true"/"false"）

### 删除网站
- **方法**: `delete_site(site_id, webname)`
- **辅助脚本命令**: `python scripts/bt_api.py del_site <ID> <域名>`
- **参数**:
  - `site_id`: 网站 ID
  - `webname`: 网站主域名

### 停止网站
- **方法**: `set_site_status(site_id, webname, 0)`
- **辅助脚本命令**: `python scripts/bt_api.py stop_site <ID> <域名>`

### 启动网站
- **方法**: `set_site_status(site_id, webname, 1)`
- **辅助脚本命令**: `python scripts/bt_api.py start_site <ID> <域名>`

### 修改 PHP 版本
- **方法**: `set_php_version(webname, version)`
- **参数**:
  - `webname`: 网站域名
  - `version`: PHP 版本（如 "74", "80", "00"）

### 申请 SSL 证书 (Let's Encrypt)
- **方法**: `apply_let_ssl(domain, site_id, auth_type="http")`
- **辅助脚本命令**: `python scripts/bt_api.py ssl <域名> <ID>`
- **参数**:
  - `domain`: 网站域名
  - `site_id`: 网站 ID

## 3. 数据库管理

### 获取数据库列表
- **方法**: `get_databases(page=1, limit=20)`
- **辅助脚本命令**: `python scripts/bt_api.py databases`
- **参数**:
  - `page`: 页码
  - `limit`: 每页数量

## 4. Docker 管理

### 获取容器列表
- **方法**: `get_docker_containers()`
- **辅助脚本命令**: `python scripts/bt_api.py docker`

### 添加 Docker Compose 模板
- **方法**: `add_compose_template(name, compose_content, env_content="")`
- **参数**:
  - `name`: 模板名称
  - `compose_content`: YAML 内容
  - `env_content`: 环境配置文件内容

### 获取 Compose 模板列表
- **方法**: `get_compose_templates()`

### 创建 Compose 项目
- **方法**: `create_compose_project(project_name, template_id)`
- **参数**:
  - `project_name`: 项目名称
  - `template_id`: 模板 ID

## 5. 文件与终端管理

### 获取目录列表
- **方法**: `get_files(path)`
- **辅助脚本命令**: `python scripts/bt_api.py files <路径>`
- **参数**:
  - `path`: 绝对路径

### 创建目录
- **方法**: `create_dir(path)`
- **参数**:
  - `path`: 要创建的绝对路径

### 写入文件
- **方法**: `write_file(path, content)`
- **参数**:
  - `path`: 绝对文件路径
  - `content`: 文件文本内容

### 读取文件内容
- **方法**: `get_file_content(path)`
- **辅助脚本命令**: `python scripts/bt_api.py read_file <路径>`

### 上传文件
- **方法**: `upload_file(local_path, remote_path)`
- **辅助脚本命令**: `python scripts/bt_api.py upload <本地路径> <远程路径>`

### 执行 Shell 命令
在服务器上执行 bash 命令。
- **方法**: `exec_shell(command)`
- **辅助脚本命令**: `python scripts/bt_api.py exec_shell "<命令>"`
- **参数**:
  - `command`: 要执行的 shell 指令
