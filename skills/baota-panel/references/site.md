# 网站管理接口

## 1. 获取网站列表
- **URL**: `/data?action=getData&table=sites`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `p` | int | 页码（默认 1） |
  | `limit` | int | 每页数量（默认 20） |

## 2. 创建网站
- **URL**: `/site?action=AddSite`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `webname` | string | 网站域名 |
  | `path` | string | 网站根目录 |
  | `type` | string | 类型（"PHP"） |
  | `version` | string | PHP 版本（如 "74", "80", "00"） |
  | `port` | string | 端口 |
  | `ps` | string | 备注 |
  | `ftp` | string | 是否开通 FTP ("true"/"false") |
  | `sql` | string | 是否开通 SQL ("true"/"false") |

## 3. 删除网站
- **URL**: `/site?action=DeleteSite`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `id` | int/string | 网站 ID |
  | `webname` | string | 网站主域名 |

## 4. 停止网站
- **URL**: `/site?action=SiteStop`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `id` | int/string | 网站 ID |
  | `webname` | string | 网站主域名 |

## 5. 启动网站
- **URL**: `/site?action=SiteStart`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `id` | int/string | 网站 ID |
  | `webname` | string | 网站主域名 |

## 6. 修改 PHP 版本
- **URL**: `/site?action=SetPHPVersion`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `version` | string | PHP 版本号 |

## 7. 申请 SSL 证书 (Let's Encrypt)
- **URL**: `/ssl?action=ApplyLetSSL`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `domains` | string | 域名列表的 JSON 字符串, 如 `["example.com"]` |
  | `id` | int/string | 网站 ID |
  | `auth_type` | string | 验证类型 ("http" 或 "dns") |
  | `auth_to` | string | 验证路径或域名 |
