# Casdoor 集成逻辑与手动 OAuth 模式

此文档描述了如何避开复杂的 Passport 插件，手动实现最稳健的 Casdoor 登录流。

## 1. 生成登录跳转
不要依赖后端插件自动跳转，手动构建 URL 以完全控制 `state`。
`GET <ENDPOINT>/login/oauth/authorize?client_id=<ID>&response_type=code&redirect_uri=<URL>&scope=read:users+openid+profile+email&state=<STATE>`

## 2. 后端回调处理 (手动模式)
在您的回调接口中：
1. **交换 Token**: 发起 POST 请求到 `<ENDPOINT>/api/login/oauth/access_token`。
2. **获取用户信息**: 使用 `access_token` 调用 `<ENDPOINT>/api/get-account`。
3. **手动注入 Session**: 将获取的用户同步到本地 DB，并手动调用 `req.login()` 或设置本地 Session。

## 4. 回调 401 错误排查清单
1. **Redirect URI 严格匹配**: 代码中的 `callbackURL` 必须与 Casdoor 后台配置的 `Redirect URLs` 字符串完全一致（包括 http/https 和端口号）。
2. **容器内网络**: 确保后端容器能够访问 Casdoor 服务器。可以在容器内执行 `curl -I <Casdoor_URL>` 验证。
3. **Secret 泄露或错误**: 检查 `clientSecret` 是否包含特殊字符导致转义错误。
4. **手动模式优势**: 遇到黑盒 401 时，切换到手动 `axios.post` 模式能打印出 Casdoor 返回的原始错误消息（如 `invalid_code` 或 `invalid_client`）。
