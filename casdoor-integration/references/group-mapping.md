# Casdoor 用户组与权限映射指南

在集成 Casdoor 时，系统需要将 Casdoor 的外部身份标识（Groups/Roles）转换为应用内部可识别的权限标识。

## 1. 数据来源：Casdoor 用户对象
通过 `accessToken` 调用 `/api/get-account` 或解析 `id_token` (JWT) 时，重点关注：
- `groups`: 用户所属的组路径数组 (例如 `["/Org/Dept/Team"]`)。
- `roles`: 用户拥有的角色数组 (例如 `["admin", "editor"]`)。

## 2. 映射策略 (Mapping Patterns)

### A. 静态前缀映射 (Simple)
适用于系统内部权限名与 Casdoor 角色名一致的情况。
- **逻辑**: 如果用户在 Casdoor 有 `teable_admin` 角色，登录后自动授予本地 `Admin` 权限。

### B. 映射配置表 (Flexible - 推荐)
在系统数据库中维护一张 `external_mapping` 表。
| 外部标识 (Casdoor Group/Role) | 内部角色 (Local Role) |
| :--- | :--- |
| `dev-team` | `Developer` |
| `marketing-dept` | `Viewer` |
| `super-admin` | `SystemAdmin` |

### C. 组织架构同步 (Advanced)
利用 Casdoor 的 `groups` 层次结构映射内部的“空间”或“部门”权限。
- **递归同步**: 每次登录时，检查用户所属的 `groups`，并动态增删用户在本地系统的部门归属。

## 3. 实现时机 (Timing)

### 场景一：登录即同步 (JIT - Just-In-Time)
在 OAuth 回调的 `validate` 逻辑中：
1. 交换得到用户信息。
2. **清除旧权限**: 清空该用户在本地系统的旧角色关联。
3. **注入新权限**: 根据 Casdoor 返回的最新 `roles/groups` 重新分配本地角色。
- **优点**: 权限变更实时生效（随下次登录）。

### 场景二：基于 Hook 的实时更新
- **逻辑**: 在系统后台开启一个 Webhook 监听 Casdoor 的 `User Update` 事件。
- **优点**: 无需用户重新登录即可更新权限。

## 4. 健壮性建议
- **默认权限**: 如果 Casdoor 没有返回任何匹配的角色，应分配一个最小权限的 `DefaultUser` 角色。
- **手动覆盖**: 系统应提供一个开关，决定是否允许管理员在本地手动修改通过 Casdoor 同步过来的用户权限。
