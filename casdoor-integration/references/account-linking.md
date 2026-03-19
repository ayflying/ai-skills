# 内置用户系统兼容与账户关联逻辑

## 1. 自动关联模式 (Email Binding)
当系统已有本地用户时，应遵循以下逻辑：
1. **查 Provider**: 检查 `db.findUserByProvider('casdoor', casdoor_id)`。
2. **查 Email**: 若未绑定，检查 `db.findUserByEmail(casdoor_email)`。
3. **绑定**: 若 Email 匹配，更新本地用户，添加 `casdoor_id` 作为其外部身份标识。
4. **降级**: 若都不存在，执行 `Auto-Signup` 创建新账户。

## 2. 详细用户字段映射参考
| Casdoor 字段 | 本地建议字段 | 说明 |
| :--- | :--- | :--- |
| `name` | `username` | 唯一系统标识。 |
| `email` | `email` | 核心联系方式，用于关联。 |
| `displayName` | `name` | 显示名。 |
| `avatar` | `avatarUrl` | 同步头像。 |
| `properties` | `metadata` | 处理自定义字段。 |
