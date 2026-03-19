# 用户组与权限系统映射指南

在企业级集成中，Casdoor 的组织架构应自动化同步到目标系统的权限体系中。

## 1. 结构化数据映射模型
Casdoor 提供了三个维度的身份资源，建议按如下方式映射：

- **Organization (组织)**: 建议映射为系统的“租户 (Tenant)”或“顶级企业实例”。
- **Group (用户组)**: 建议映射为系统的“部门 (Department)”、“团队 (Team)”或“空间 (Workspace)”。Casdoor 支持父子组关系，系统应能递归重建此树形结构。
- **Role (角色)**: 建议映射为系统的“具体功能权限集 (Permission Set)”。

## 2. 权限同步模式
- **全量同步 (Full Sync)**: 用户登录时，系统会重置其在本地的所有角色归属，严格与 Casdoor 返回的 `roles` 数组一致。
- **增量补丁 (Patch Sync)**: 用户登录时，系统仅同步 Casdoor 显式返回的角色，保留用户在本地手动被赋予的其他扩展角色。

## 3. 冲突解决策略
- **冲突优先级**: 建议在配置中心预设冲突逻辑。例如：“如果用户在 Casdoor 中被禁用，则无论其在本地系统权限如何，一律禁止登录。”
- **默认组设置**: 对于新同步的用户，应分配一个默认的低权限组（Guest/Common），直至其 Casdoor 权限被上级更新。

## 4. 实现建议
建议建立一张 `external_identity_mapping` 配置表，允许系统管理员通过界面将 Casdoor 的 `Group Name` 或 `Role Name` 与本地系统的 `Internal Permission Tag` 建立动态绑定关系。
