# 用户组与组织架构映射指南

## 1. 组对象结构 (JSON)
重点处理 Casdoor 的 `groups` 数组，其单体结构通常为：
- `name`: 唯一 ID。
- `displayName`: 部门名。
- `parentId`: 父组 ID（用于实现树形组织架构同步）。

## 2. 映射模式 (Binding)
- **多对多同步**: 用户登录时，根据 Casdoor 返回的 `groups` 列表，实时更新本地系统的“部门归属”或“空间成员”。
- **角色转换**: `casdoorUser.roles` -> 内部系统的 `LocalRole`。

## 3. 冲突与优先级策略
- **Casdoor 优先 (企业强制同步)**: 用户每次登录，其本地权限都会被 Casdoor 返回的角色强制重置。
- **本地补丁模式 (推荐)**: 本地管理员可以为用户添加 Casdoor 之外的额外权限，同步时仅增量更新。

## 4. 实现建议
在本地系统建立 `external_role_mapping` 配置表，允许 UI 界面配置 `Casdoor Role A` 对应 `System Permission B`。
