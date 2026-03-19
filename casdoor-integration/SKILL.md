---
name: casdoor-integration
description: 通用的 Casdoor SSO/IAM 集成指南。包含跨语言 OAuth2/OIDC 逻辑。**特别支持：内置用户系统兼容性（账户关联）、Session 存储冲突解决、手动回调稳健模式。** 适用于需要在现有用户体系上平滑扩展 SSO 的场景。
---

# Casdoor 通用集成指南 (实战增强版)

本技能专注于在复杂业务场景下，如何稳健地将 Casdoor 集成到包含**内置用户系统**的应用中。

## 核心集成原则
- **账户关联 (Account Linking)**: 优先通过 Email 或手机号将 Casdoor 身份与内置账户绑定，避免重复创建。
- **手动 OAuth2 模式**: 推荐手动处理 Token 交换，以实现更精细的账户合并逻辑。
- **权限对接**: 支持 Casdoor 角色与本地权限系统的深度绑定。

## 核心工作流
1. **登录初始化**: 支持多种认证源并存。
2. **账户识别与合并**: 详见 [内置用户系统兼容性指南](references/account-linking.md)。
3. **用户组与权限同步**: 详见 [权限映射指南](references/group-mapping.md)。

## 实战避坑指南 (必读)
- [Session 崩溃深度修复](references/session-pitfalls.md)
- [前端构建与环境变量陷阱](references/frontend-traps.md)
- [手动 OAuth 逻辑与 401 排查](references/logic.md)
