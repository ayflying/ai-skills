# Casdoor 跨语言集成逻辑详解

此参考文档描述了如何在您的后端系统中，无论使用何种编程语言，实现 Casdoor 的核心身份认证逻辑。

## 1. 生成登录跳转 URL

用户点击“使用 Casdoor 登录”按钮后，前端应重定向到：
`GET <CASDOOR_ENDPOINT>/login/oauth/authorize`

**参数清单：**
- `client_id`: 必填。
- `response_type`: 必填，固定为 `code`。
- `redirect_uri`: 必填，从服务端精确白名单选择并在 Casdoor 后台登记，不从 Host、Referer 或任意代理头拼接。
- `scope`: 必填，推荐 `read:users+openid+profile+email`。
- `state`: 必填，密码学安全随机值，绑定服务端会话、独立事务、回调地址及短有效期。
- `nonce`: OIDC 登录时生成并保存在同一事务，用于校验 ID Token。

---

## 2. 后端回调处理 (Code Exchange)

Casdoor 成功后会重定向回您的 `redirect_uri`，并携带 code 和 state。交换前强制核对当前会话事务中的 state、一致性、有效期及未使用状态并原子消费；缺失、失配、过期和重放均拒绝。

### 交换令牌 (Server-to-Server)
向端点发送 **POST** 请求：`<CASDOOR_ENDPOINT>/api/login/oauth/access_token`

**请求正文 (Form-encoded / JSON)：**
```json
{
  "grant_type": "authorization_code",
  "client_id": "...",
  "client_secret": "...",
  "code": "...",
  "redirect_uri": "<与授权请求完全一致的可信回调URL>"
}
```

---

## 3. 解析用户信息 (Identity Sync)

使用标准 OIDC 库，验证成功后才同步身份与建立会话：
1. **强制验签**：普通签名 JWT（JWS）需要验签而非解密。固定允许算法，拒绝 none，使用可信 issuer 配置的证书或 JWKS；不接受 Token 指定的任意密钥 URL。若部署使用加密 JWT（JWE），解密后仍须完成签名与 claims 校验。
2. **校验 claims**：iss 精确匹配配置，aud 包含本应用 client ID，多受众时校验 azp；exp 必须有效，按协议检查 nbf、iat 并限制时钟偏差；nonce 必须匹配已消费事务内保存的值。必要字段缺失即拒绝。
3. **核对资料**：用 access token 调用可信账号接口，验证启用状态、组织及资料与已验证 sub 的服务端映射；name、email、avatar 不是身份凭证。
4. **关联并授权**：外部身份键为 (issuer, organization, sub)。已有账号需重新认证证明归属或使用审核过的迁移映射，不凭同号/同邮箱静默绑定。只映射当前租户白名单权限，成功后轮换 Session ID。

启用 PKCE 时，授权阶段保存 verifier 并发送 challenge，交换时提交对应 code_verifier；它不替代 state 和 nonce 校验。

---

## 4. 异常处理建议

- **网络连接超时**: 设置合理的超时时间，建议 5-10 秒。
- **证书验证**：所有环境均开启 HTTPS 证书校验，自签名部署配置可信 CA；ID Token 签名验证是建立会话前的强制步骤，不能只解析载荷。
- **重定向回跳保护**: 验证 `redirect_uri` 与 Casdoor 后台配置是否完全匹配。
