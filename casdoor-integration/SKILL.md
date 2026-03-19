---
name: casdoor-integration
description: 通用的 Casdoor SSO/IAM 集成指南。包含跨语言 OAuth2/OIDC 逻辑。**特别包含：Session 存储冲突解决、Next.js 静态编译环境变量陷阱、手动回调稳健模式。** 适用于任何需要高性能、高稳定性 SSO 集成的场景。
---

# Casdoor 通用集成指南 (实战增强版)

本技能沉淀了大量在复杂 Monorepo 框架中集成 Casdoor 的实战经验。

## 核心集成模式
- **手动 OAuth2 模式 (强烈推荐)**: 避开 Passport 等自动化插件的黑盒逻辑，通过 `axios` 手动交换 Token，稳定性最高。
- **用户组与权限同步 (深度集成)**: 将 Casdoor 的组织架构映射为系统内部角色。参见 [权限映射指南](references/group-mapping.md)。

## 实战避坑指南 (必读)
1. **Session 存储冲突**: 解决“由于尚未登录而无法保存 OAuth State”导致的系统崩溃。参见 [Session 避坑参考](references/session-pitfalls.md)。
2. **构建期环境变量**: 解决 Next.js 等框架在 Docker 构建时因缺少变量导致登录按钮不显示的 Bug。参见 [前端构建陷阱](references/frontend-traps.md)。
3. **网络与回调路径**: 处理本地 `localhost` 与远程域名在容器环境下的重定向冲突。

## 详细资源
- [手动 OAuth 逻辑详解](references/logic.md)
- [Session 崩溃深度修复](references/session-pitfalls.md)
- [前端构建与环境变量陷阱](references/frontend-traps.md)
- [字段与组织架构映射](references/mapping.md)
