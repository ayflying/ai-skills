# 用户组与权限系统映射指南

在企业级集成中，Casdoor 的组织架构应自动化同步到目标系统的权限体系中。

## 1. 结构化数据映射模型
Casdoor 提供了三个维度的身份资源，建议按如下方式映射：

- **Organization (组织)**: 建议映射为系统的"租户 (Tenant)"或"顶级企业实例"。
- **Group (用户组)**: 建议映射为系统的"部门 (Department)"、"团队 (Team)"或"空间 (Workspace)"。Casdoor 支持父子组关系，系统应能递归重建此树形结构。
- **Role (角色)**: 建议映射为系统的"具体功能权限集 (Permission Set)"。

## 2. 用户组匹配规则

Casdoor 用户组格式为 `组织/用户组名`（如 `MyOrg/Engineering`）。先验证组织属于当前本地租户，再按 (issuer, organization, group) 白名单匹配；不得忽略组织前缀，也不默认取数组首项。

```python
def match_user_groups(
    issuer: str,
    organization: str,
    casdoor_groups: list[str],
    allowed_mapping: dict[tuple[str, str, str], str],
) -> set[str]:
    # 映射由服务端为当前已授权租户加载，不来自浏览器请求
    matched = set()
    for value in casdoor_groups:
        owner, separator, group = value.partition("/")
        if not separator or owner != organization or not group:
            continue
        local_group = allowed_mapping.get((issuer, owner, group))
        if local_group is not None:
            matched.add(local_group)
    return matched
```

无组织前缀的值须根据所用版本的可信组织字段规范化，不能猜测组织。角色映射同样保留 issuer、组织和本地租户边界。

## 3. 权限同步模式
- **全量同步 (Full Sync)**: 仅替换当前租户内由该外部身份源管理的角色，并经过显式映射，不影响其他来源角色。
- **增量补丁 (Patch Sync)**: 仅增补白名单映射角色，保留本地角色；此模式不自动回收上游删除的权限，须另设撤权和禁用检查。

## 4. 冲突解决策略
- **冲突优先级**: 建议在配置中心预设冲突逻辑。例如："如果用户在 Casdoor 中被禁用，则无论其在本地系统权限如何，一律禁止登录。"
- **默认组设置**: 对于新同步的用户，应分配一个默认的低权限组（Guest/Common），直至其 Casdoor 权限被上级更新。

## 5. 实现建议
建议建立一张 `external_identity_mapping` 配置表，允许系统管理员通过界面将 Casdoor 的 `(issuer, organization, Group/Role Name)`（绑定当前本地租户） 与本地系统的 `Internal Permission Tag` 建立动态绑定关系。
