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

## 8. 获取网站域名列表
- **URL**: `/data?action=getData&table=domain`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `p` | int | 页码 |
  | `limit` | int | 每页数量 |

## 9. 添加网站域名
- **URL**: `/site?action=AddDomain`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `domain` | string | 要添加的域名 |
  | `port` | string | 端口（默认 "80"） |

## 10. 删除网站域名
- **URL**: `/site?action=DelDomain`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `domain` | string | 要删除的域名 |
  | `port` | string | 端口 |

## 11. 获取网站日志
- **URL**: `/site?action=GetSiteLogs`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 12. 获取 SSL 状态
- **URL**: `/site?action=GetSSL`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 13. 设置 SSL 证书
- **URL**: `/site?action=SetSSL`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `cert` | string | 证书内容 |
  | `key` | string | 私钥内容 |

## 14. 强制 HTTPS
- **URL**: `/site?action=HttpToHttps`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 15. 关闭强制 HTTPS
- **URL**: `/site?action=CloseToHttps`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 16. 设置网站防盗链
- **URL**: `/site?action=SetSecurity`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `open` | string | 状态 ("true"/"false") |
  | `rules` | string | 规则 |

## 17. 设置网站防盗链
> ⚠️ 注意：获取防盗链状态接口被防火墙阻止，此接口可能无法正常工作。

- **URL**: `/site?action=SetSecurity`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `open` | string | 状态 ("true"/"false") |
  | `rules` | string | 规则 |

## 18. 获取网站流量限制
- **URL**: `/site?action=GetLimitNet`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 19. 设置网站流量限制
- **URL**: `/site?action=SetLimitNet`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `port` | string | 限制端口 |

## 20. 关闭流量限制
- **URL**: `/site?action=CloseLimitNet`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 21. 获取 301 重定向
- **URL**: `/site?action=Get301Status`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 22. 设置 301 重定向
- **URL**: `/site?action=Set301Status`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `toDomain` | string | 目标域名 |
  | `open` | string | 是否开启 ("true"/"false") |

## 23. 创建网站反代
- **URL**: `/site?action=CreateProxy`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `proxy_url` | string | 反代地址 |
  | `host` | string | 目标主机 |
  | `toPath` | string | 目标路径 |

## 24. 修改网站反代
> ⚠️ 注意：获取反代列表接口被防火墙阻止，此接口可能无法正常工作。

- **URL**: `/site?action=ModifyProxy`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `proxy_url` | string | 反代地址 |
  | `host` | string | 目标主机 |
  | `toPath` | string | 目标路径 |

## 25. 获取子目录绑定
- **URL**: `/site?action=GetDirBinding`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 26. 添加子目录绑定
- **URL**: `/site?action=AddDirBinding`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `domain` | string | 域名 |
  | `dir` | string | 子目录路径 |
  | `port` | string | 端口 |

## 27. 删除子目录绑定
- **URL**: `/site?action=DelDirBinding`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `domain` | string | 域名 |
  | `dir` | string | 子目录路径 |

## 28. 获取子目录伪静态规则
- **URL**: `/site?action=GetDirRewrite`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `dir` | string | 子目录路径 |

## 29. 获取可选伪静态列表
- **URL**: `/site?action=GetRewriteList`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 30. 获取网站默认文件
- **URL**: `/site?action=GetIndex`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 31. 设置网站默认文件
- **URL**: `/site?action=SetIndex`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `index` | string | 默认文件列表 |

## 32. 获取网站几项开关
- **URL**: `/site?action=GetDirUserINI`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |

## 33. 开启网站密码访问
- **URL**: `/site?action=SetHasPwd`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
  | `has_pwd` | string | 密码 |

## 34. 关闭网站密码访问
- **URL**: `/site?action=CloseHasPwd`
- **Method**: `POST`
- **参数**:
  | 参数名 | 类型 | 说明 |
  |----------|------|------|
  | `siteName` | string | 网站域名 |
