# Casdoor 集成逻辑与手动 OAuth 模式

此文档描述了如何避开复杂的 Passport 插件，手动实现最稳健的 Casdoor 登录流。

## 1. 生成登录跳转
不要依赖后端插件自动跳转，手动构建 URL 以完全控制 `state`。回调来自服务端精确白名单，不从 Host、Referer 或任意代理头拼接。随机 state、nonce 绑定服务端会话、独立事务及短有效期。
`GET <ENDPOINT>/login/oauth/authorize?client_id=<ID>&response_type=code&redirect_uri=<URL>&scope=read:users+openid+profile+email&state=<STATE>&nonce=<NONCE>`

## 2. 后端回调处理 (手动模式)
在您的回调接口中：
1. **校验并消费 state**：核对当前会话事务的一致性、有效期及未使用状态并原子消费；缺失、失配和重放拒绝。
2. **交换 Token**：POST 到可信 `<ENDPOINT>/api/login/oauth/access_token`，使用事务内同一 redirect_uri，启用 PKCE 时传对应 code_verifier。
3. **验证身份**：强制验签及校验 ID Token 的 iss、aud、exp、nonce 等 claims，再核对可信账号接口主体和组织，不能只解码 JWT。详见 [跨语言实现](implementation-logic.md)。
4. **注入 Session**：按 (issuer, organization, sub) 查找绑定；关联已有账号前证明本地账号归属，通过租户授权后轮换 Session ID，再调用 req.login() 或设置会话。

## 3. 回调 401 错误排查清单
1. **Redirect URI 严格匹配**: 代码中的 `callbackURL` 必须与 Casdoor 后台配置的 `Redirect URLs` 字符串完全一致（包括 http/https 和端口号）。
2. **容器内网络**: 确保后端容器能够访问 Casdoor 服务器。可以在容器内执行 `curl -I <Casdoor_URL>` 验证。
3. **Secret 泄露或错误**: 检查 `clientSecret` 是否包含特殊字符导致转义错误。
4. **手动模式优势**: 遇到黑盒 401 时，切换到手动 `axios.post` 模式可记录脱敏错误码（如 `invalid_code` 或 `invalid_client`），不打印授权码、Token、Secret 或原始请求/响应全文。
