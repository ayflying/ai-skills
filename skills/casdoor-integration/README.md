# Casdoor Integration (SSO/IAM 集成指南)

通用的 Casdoor SSO/IAM 集成专家级指南。涵盖跨语言 OAuth2/OIDC 认证逻辑、账户关联、组织同步及生产环境避坑指南。

## 安装

### 标准化安装 (推荐)

使用 `skills` CLI 将此集成指南添加到你的 Agent：

```bash
npx skills add ayflying/ai-skills --skill casdoor-integration
```

## 核心能力

- ✅ **OAuth2/OIDC 深度集成**: 手动令牌交换与认证流控制。
- ✅ **账户关联 (Account Linking)**: 兼容内置用户系统的平滑绑定逻辑。
- ✅ **组织架构同步**: 深度映射 Casdoor Organization 和 Group。
- ✅ **避坑指南**: 解决 Session 竞争、静态构建环境变量注入等实战陷阱。

## 详细资源

此技能包含以下模块化文档：

- [认证逻辑与 Session 稳定性修复](references/auth-logic.md)
- [内置系统兼容性与账户关联](references/account-linking.md)
- [用户组与权限系统映射指南](references/group-mapping.md)
- [前端构建陷阱与环境变量处理](references/frontend-traps.md)

## 使用方式

安装后，你可以要求 Agent 参考此指南来执行 Casdoor 集成任务，例如：
> "帮我实现 Go 后端的 Casdoor OAuth2 登录逻辑，参考 casdoor-integration 技能中的账户关联规范。"

## 许可证

MIT License
