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
  "msg": "操作成功",
  ... (其他数据)
}
```

### 失败响应
```json
{
  "status": false,
  "msg": "错误描述信息"
}
```
