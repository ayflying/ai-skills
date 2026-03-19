# 安全与防火墙接口

## 1. 获取防火墙列表
列出所有开放的端口及放行规则。

- **URL**: `/firewall?action=GetList`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `p` | int | 页码 |
  | `limit` | int | 每页数量 |

## 2. 添加防火墙规则 (放行端口)
- **URL**: `/firewall?action=AddAcceptPort`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `port` | string | 端口或端口范围 (如 "80" 或 "8000:9000") |
  | `ps` | string | 备注说明 |
  | `protocol` | string | 协议类型 ("tcp" 或 "udp") |

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

## 5. 设置 SSH 状态 (开启/关闭)
- **URL**: `/firewall?action=OpenSSH` 或 `/firewall?action=CloseSSH`
- **Method**: `POST`
- **备注**: 无需额外参数。
