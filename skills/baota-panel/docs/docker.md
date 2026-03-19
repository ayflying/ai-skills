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
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | "container" |
  | `dk_def_name` | string | "get_logs" |
  | `container_id` | string | 容器 ID |

## 4. Docker Compose 稳健执行 (推荐)
通过 `ExecShell` 直接调用系统 `docker-compose` 命令，规避宝塔内部模型版本差异问题。

- **URL**: `/files?action=ExecShell`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `command` | string | `cd <路径> && docker-compose <指令>` |

## 5. 添加 Docker Compose 模板
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | "compose" |
  | `dk_def_name` | string | "add_template" |
  | `name` | string | 模板名称 |
  | `data` | string | YAML 内容 |
  | `env` | string | 环境配置内容 |
