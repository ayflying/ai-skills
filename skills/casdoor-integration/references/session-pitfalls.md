# Session 存储冲突与 OAuth 初始化崩溃

## 问题描述
在集成 Casdoor（或任何 OIDC/OAuth2）时，系统可能会在点击“登录”按钮跳转到 Casdoor 之前报如下错误：
`TypeError: Cannot read properties of undefined (reading 'user')` 或 `Cannot set headers after they are sent to the client`。

## 根本原因
许多企业级框架（如 Teable 的 `SessionStoreService`）为了安全性或统计，在 `set(sid, session)` 时会强制读取 `session.user.id`。
但在 OAuth 初始化阶段，后端会将 `state` 和 `nonce` 暂存到 Session 中，此时用户**尚未登录**，`session.user` 是 `undefined`，导致存储层抛出异常，进而导致整个重定向逻辑中断。

## 解决方案 (程序化逻辑)
您必须修改 Session 存储层的验证逻辑，使其支持“匿名会话”：

1. **防御性检查**: 在读取用户信息前，先检查 `session.passport` 或 `session.user` 是否存在。
2. **逻辑分离**:
   - 如果有用户信息，执行用户相关的缓存更新（如 `userSessions` 计数）。
   - 如果没有用户信息，**依然允许保存 Session**，以确保 OAuth 的 `state` 能够被存储和后续验证。

## 伪代码示例
```pseudo
function saveSession(sid, sessionData) {
  const userId = sessionData?.passport?.user?.id;
  
  if (userId) {
    // 处理已登录用户的特殊逻辑
    updateUserSessionCache(userId, sid);
  }
  
  // 必须保证这一步始终执行，否则 OAuth 跳转将失败
  commitToDatabase(sid, sessionData);
}
```
