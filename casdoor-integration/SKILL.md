---
name: casdoor-integration
description: 全能型 Casdoor SSO/IAM 集成指南。支持跨语言 OAuth2/OIDC 认证逻辑。核心能力包括：(1) 兼容内置用户系统的账户关联 (Account Linking)，(2) 深度用户组与组织架构同步，(3) 自动化权限映射与冲突处理，(4) 复杂框架下的 Session 与构建期环境变量避坑指南。
---

# Casdoor 全功能集成指南 (生产级实战版)

本技能集成了在复杂企业级架构中对接 Casdoor 的完整生命周期管理。

## 1. 核心集成模式
- **手动 OAuth2 模式 (推荐)**: 绕过 Passport 等插件的黑盒 Session 限制，通过 `axios/fetch` 手动处理 `code` 交换，稳定性最高。
- **混合认证兼容**: 确保 Casdoor 能够与系统原有的“邮箱/密码”登录方式平滑并存。

## 2. 深度同步与绑定
- **用户同步**: 支持按需同步头像、昵称及自定义字段。
- **组织架构绑定**: 将 Casdoor 的 `Organization` 和 `Group` (支持树形结构) 映射为本地系统的部门或空间。
- **权限映射**: 将外部 `Roles` 映射为本地系统的角色权限集。

## 3. 实战避坑参考 (深度复盘)
- **Session 存储逻辑修复**: 解决“尚未登录导致无法保存状态”的崩溃问题。
- **前端构建变量固化**: 解决 Next.js 等框架在 Docker 构建期丢失环境变量导致按钮不显示的陷阱。

## 4. 详细资源
- [认证逻辑与 Session 修复](references/auth-logic.md)
- [内置系统兼容与账户关联](references/account-linking.md)
- [用户组与权限深度映射](references/group-mapping.md)
- [前端构建与环境变量陷阱](references/frontend-traps.md)
