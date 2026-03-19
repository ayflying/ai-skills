---
name: casdoor-integration
description: 通用的 Casdoor SSO/IAM 集成指南。支持跨语言 OAuth2/OIDC 认证逻辑。核心能力包括：(1) 兼容内置用户系统的账户关联 (Account Linking)，(2) 深度用户组与组织架构同步，(3) 自动化权限映射与冲突处理，(4) 解决复杂框架下的 Session 竞争与构建期环境变量固化等实战陷阱。
---

# Casdoor 全功能通用集成指南

本技能提供了在任何现代化应用程序架构中对接 Casdoor 身份访问管理（IAM）系统的标准程序化知识。

## 1. 核心集成模式
- **手动 OAuth2 模式 (推荐)**: 避开特定框架插件的黑盒限制，通过标准 HTTP 请求手动处理令牌交换，以获得最佳的日志追踪和跨平台稳定性。
- **混合认证兼容 (Hybrid Auth)**: 确保 SSO 登录能与系统原有的内置登录方式（如邮箱/密码）平稳并存且逻辑统一。

## 2. 深度同步与绑定逻辑
- **用户档案同步**: 自动映射 Casdoor 的核心字段（头像、昵称、唯一标识）到内部系统。
- **组织架构绑定**: 支持将 Casdoor 的组织（Organization）和层级化用户组（Group）同步为系统内部的部门或空间。
- **权限角色映射**: 建立外部 Role 与内部权限集（Permissions/Roles）的动态对应关系。

## 3. 生产级避坑参考
- **Session 健壮性设计**: 解决在 OAuth 初始化阶段（用户尚未登录时）因存储层限制导致的会话保存崩溃。
- **静态构建环境变量注入**: 解决前端框架（如 Next.js, Vite）在构建期间因缺失变量导致 SSO 按钮被错误隐藏的问题。

## 4. 详细资源
- [认证逻辑与 Session 稳定性修复](references/auth-logic.md)
- [内置系统兼容性与账户关联](references/account-linking.md)
- [用户组与权限系统映射指南](references/group-mapping.md)
- [前端构建陷阱与环境变量处理](references/frontend-traps.md)
