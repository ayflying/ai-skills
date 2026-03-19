# Docker 管理接口

所有 Docker 相关接口均使用公共 URL。

- **URL**: `/project/docker/model`
- **Method**: `POST`
- **公共 Docker 参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `url` | string | Docker 套接字路径, 通常为 `unix:///var/run/docker.sock` |

## 1. 获取容器列表
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | "container" |
  | `dk_def_name` | string | "get_list" |

## 2. 操作 Docker 容器
对指定容器执行启动、停止、重启或删除操作。

- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | "container" |
  | `dk_def_name` | string | 操作指令: "start", "stop", "restart", "remove" |
  | `container_id` | string | 容器 ID |

## 3. 获取 Docker 容器日志
优先通过宝塔 API 获取，若 API 失败则回退到 `docker logs` shell 命令。

- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | "container" |
  | `dk_def_name` | string | "get_logs" |
  | `container_id` | string | 容器 ID |

## 4. Docker Compose 稳健执行 (极力推荐)
由于宝塔面板不同版本 Docker 插件内部模型名称（如 `dk_compose`, `compose`）存在差异，直接调用插件 API 极易报错。
推荐通过 `ExecShell` 直接调用系统 `docker-compose` 命令。

- **URL**: `/files?action=ExecShell`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `command` | string | `cd <路径> && docker-compose <指令>` |
  
**常用场景**:
- `cd /www/wwwroot/proj && docker-compose up -d` - 启动项目
- `cd /www/wwwroot/proj && docker-compose down` - 停止并删除
- `cd /www/wwwroot/proj && docker-compose logs --tail 100` - 查看日志

## 5. 添加 Docker Compose 模板
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | "compose" |
  | `dk_def_name` | string | "add_template" |
  | `name` | string | 模板名称 |
  | `data` | string | YAML 内容 |
  | `env` | string | 环境配置内容 |
