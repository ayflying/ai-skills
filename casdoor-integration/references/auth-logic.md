# Casdoor 认证逻辑与 Session 稳定性指南

## 1. 登录流实现 (手动模式)
不建议使用全自动 Passport 插件，推荐手动控制以获得最佳日志和稳定性：
- **跳转**: `GET <ENDPOINT>/login/oauth/authorize?...&state=<STATE>`
- **回调**: 
  1. 接收 `code` 和 `state`。
  2. POST `access_token` 端点获取令牌。
  3. 调用 `/api/get-account` 获取详细 User 对象。

## 2. 核心 Bug 修复：Session 冲突
**场景**: 系统报 `Cannot read user of undefined`。
**原因**: 系统 Session 存储层强制要求 UserID，但 OAuth 初始化时用户未登录。
**修复逻辑**: 
修改 Session 存储服务的 `set` 方法，允许在 `session.passport.user` 为空时依然保存会话（仅存储 `state` 等 OAuth 元数据）。

## 3. 401 错误排查清单
- **Redirect URI**: 必须与 Casdoor 后台配置的 URL 字符级匹配（包括 `http/https`）。
- **容器网络**: 确保后端容器能访问到 `casdoor.adesk.com`。
- **AccessToken 获取**: 检查 Client Secret 是否被错误转义。
