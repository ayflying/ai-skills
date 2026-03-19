# 日志接口

## 1. 获取面板操作日志
- **URL**: `/config?action=get_logs`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `p` | int | 页码 |
  | `limit` | int | 每页数量 |

## 2. 获取网站运行日志
- **URL**: `/site?action=GetSiteLogs`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
