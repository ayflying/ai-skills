# 安全与防火墙接口

## 1. 获取防火墙规则列表
- **URL**: `/firewall?action=GetList`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `p` | int | 页码 |
  | `limit` | int | 每页数量 |

## 2. 添加防火墙规则
- **URL**: `/firewall?action=AddAcceptPort`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `port` | string | 端口号 |
  | `ps` | string | 规则描述 |
  | `protocol` | string | 协议 ("tcp"/"udp"/"both") |

## 3. 删除防火墙规则
- **URL**: `/firewall?action=DelAcceptPort`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `id` | int | 规则 ID |
  | `port` | string | 端口号 |

## 4. 获取 SSH 状态
- **URL**: `/firewall?action=GetSSHStatus`
- **Method**: `POST`
- **说明**: 获取 SSH 服务当前状态

## 5. 设置 SSH 状态
- **URL**: `/firewall?action=OpenSSH` 或 `/firewall?action=CloseSSH`
- **Method**: `POST`
- **说明**: 开启或关闭 SSH 服务
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `status` | int | 1=开启, 0=关闭 |
