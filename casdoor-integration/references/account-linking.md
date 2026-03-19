# 内置用户系统兼容性与账户关联指南

当系统已存在内置用户（如通过 Email/密码注册的用户）时，集成 Casdoor 需要遵循账户关联逻辑，确保用户身份的唯一性。

## 1. 识别唯一标识 (Identity Resolver)
通常使用 **Email** 或 **手机号** 作为跨系统的唯一识别符。

### 推荐关联逻辑 (伪代码):
```pseudo
function handleCasdoorCallback(casdoorUser) {
  // 1. 首先尝试查找已绑定的外部身份 (provider + providerId)
  let localUser = db.findUserByProvider('casdoor', casdoorUser.id);
  
  if (localUser) {
    return localUser; // 已绑定，直接登录
  }

  // 2. 如果未绑定，尝试通过 Email 查找内置用户
  localUser = db.findUserByEmail(casdoorUser.email);

  if (localUser) {
    // 关键步骤：执行自动关联
    db.linkProvider(localUser.id, 'casdoor', casdoorUser.id);
    log.info(`Account linked for ${localUser.email} via Casdoor`);
    return localUser;
  }

  // 3. 如果都不存在，则执行自动注册 (Auto-provisioning)
  return db.createUser(casdoorUser);
}
```

## 2. 混合认证模式 (Hybrid Auth)
- **并存机制**: 登录页面应同时保留“内置登录”和“Casdoor 按钮”。
- **单向同步**: 建议以 Casdoor 为准更新显示名和头像，但保留本地的密码认证能力（除非在 Casdoor 中强制禁用）。

## 3. 用户组与权限冲突 (Conflicts)
- **合并原则**: 如果内置系统已有 `Admin` 权限，但 Casdoor 返回的是 `Editor`：
  - **覆盖模式**: 强制以 Casdoor 返回的最新角色为准（推荐企业级内网场景）。
  - **累加模式**: 取本地权限与外部权限的并集。
- **持久化建议**: 在本地数据库的 `User` 表中增加 `auth_source` 字段，记录用户是“本地创建”还是“SSO 导入”。

## 4. 迁移建议
对于存量用户，建议在第一次登录 Casdoor 时弹窗提示：“检测到您的 Email 已注册，是否关联到 Casdoor 账户？”以提升安全性。
