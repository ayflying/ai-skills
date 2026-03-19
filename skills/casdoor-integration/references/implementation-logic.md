# Casdoor 跨语言集成逻辑详解

此参考文档描述了如何在您的后端系统中，无论使用何种编程语言，实现 Casdoor 的核心身份认证逻辑。

## 1. 生成登录跳转 URL

用户点击“使用 Casdoor 登录”按钮后，前端应重定向到：
`GET <CASDOOR_ENDPOINT>/login/oauth/authorize`

**参数清单：**
- `client_id`: 必填。
- `response_type`: 必填，固定为 `code`。
- `redirect_uri`: 必填，您的应用回调地址。
- `scope`: 必填，推荐 `read:users+openid+profile+email`。
- `state`: 推荐，随机字符串，用于防止 CSRF。

---

## 2. 后端回调处理 (Code Exchange)

Casdoor 成功后会重定向回您的 `redirect_uri`，并携带 `code`。

### 交换令牌 (Server-to-Server)
向端点发送 **POST** 请求：`<CASDOOR_ENDPOINT>/api/login/oauth/access_token`

**请求正文 (Form-encoded / JSON)：**
```json
{
  "grant_type": "authorization_code",
  "client_id": "...",
  "client_secret": "...",
  "code": "..."
}
```

---

## 3. 解析用户信息 (Identity Sync)

推荐使用标准 OIDC (JWT) 解析方式：
1. **解密 ID Token**: 获取 `id_token` 并进行 JWT 解密。
2. **提取标识符**:
   - `sub`: JWT 中的唯一身份标识。
   - `name`: 用户名。
   - `email`: 电子邮箱。
   - `avatar`: 用户头像 URL。

---

## 4. 异常处理建议

- **网络连接超时**: 设置合理的超时时间，建议 5-10 秒。
- **证书验证**: 推荐在生产环境下使用 Casdoor 提供的 `certificate` (X509) 进行公钥签名验证。
- **重定向回跳保护**: 验证 `redirect_uri` 与 Casdoor 后台配置是否完全匹配。
