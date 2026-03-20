# Docker 管理接口

## 1. 获取容器列表
- **URL**: `/project/docker/model`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | `container` |
  | `dk_def_name` | string | `get_list` |

## 2. 操作容器 (启动/停止/重启)
- **URL**: `/project/docker/model`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | `container` |
  | `dk_def_name` | string | `start` / `stop` / `restart` |
  | `container_id` | string | 容器 ID |

## 3. Docker Compose 项目列表
- **URL**: `/project/docker/model`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | `compose` |
  | `dk_def_name` | string | `compose_project_list` |

## 4. 创建 Compose 模板 (Socket 模式)
> ⚠️ 注意：此接口需要 `x-http-token` 验证。
- **URL**: `/project/docker/model`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | `compose` |
  | `dk_def_name` | string | `add_template` |
  | `name` | string | 模板名称 |
  | `data` | string | YAML 内容 |

## 5. 部署 Compose 项目
- **URL**: `/project/docker/model`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | `compose` |
  | `dk_def_name` | string | `create` |
  | `project_name` | string | 项目名 |
  | `template_id` | int | 模板 ID |

## 6. 删除 Compose 项目
- **URL**: `/project/docker/model`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `dk_model_name` | string | `compose` |
  | `dk_def_name` | string | `remove` |
  | `project_id` | int | 项目 ID |
