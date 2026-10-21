# 宝塔面板 API 公共规范

所有接口调用都必须遵循以下公共规范。

## 1. 认证机制

宝塔面板 API 使用令牌 (Token) 认证。令牌由 API 密钥和时间戳生成。

### 令牌生成算法 (Python 示例)
```python
import hashlib
import time

api_key = "YOUR_API_KEY"
now_time = int(time.time())
token_str = str(now_time) + hashlib.md5(api_key.encode('utf-8')).hexdigest()
request_token = hashlib.md5(token_str.encode('utf-8')).hexdigest()
```

## 2. 公共请求参数

每个 POST 请求都必须包含以下参数：

| 参数名 | 类型 | 说明 |
|----------|------|------|
| `request_time` | int | 当前 Unix 时间戳 (秒) |
| `request_token` | string | 生成的 MD5 认证令牌 |

## 3. 请求方式

- **Method**: `POST`
- **Content-Type**: `application/x-www-form-urlencoded`

## 4. 通用响应结构

通常返回 JSON 格式数据。

### 成功响应
```json
{
  "status": true,
  "msg": "操作成功"
}
```

### 失败响应
```json
{
  "status": false,
  "msg": "错误描述信息"
}
```

## 5. 证书、错误与授权

默认校验 HTTPS 证书，可通过 `BT_CA_BUNDLE` 或构造器 `ca_bundle` 指定已核验的可信 CA 文件，不支持静默跳过校验。请求超时为 30 秒，非 2xx、网络错误及无效 JSON 返回 `status: false`；错误不回显原始响应或凭证。成功 JSON 保持上游结构。

`request()` 不修改调用方参数。登录态文件读取和计划任务代理分别要求 `allow_session_access=True`、`allow_crontab_fallback=True`，只能在取得对应授权后开启，不能绕过安全策略。
