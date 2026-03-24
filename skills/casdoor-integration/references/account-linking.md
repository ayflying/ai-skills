# 内置用户系统兼容与账户关联逻辑

当目标系统已拥有自身的用户体系时，集成 Casdoor 应遵循"身份合并"原则，而非直接创建冗余账号。

## 1. 自动关联工作流 (Account Linking)
系统在处理 Casdoor 登录成功的回调后，应执行以下级联查找逻辑：

1. **外部 ID 查找**: 检查本地数据库中是否已存在关联此 `Casdoor Provider + ProviderID` 的记录。
2. **唯一标识符匹配**: 如果未找到外部绑定，尝试通过 `Email` 或 `手机号` 查找系统现有的内置用户。
3. **静默绑定**: 如果找到同 Email 用户，将其本地 ID 与 Casdoor ID 建立关联关系。
4. **自动创建**: 仅当上述两步都失败时，才创建全新的本地用户记录。

## 2. 无邮箱用户的兜底处理

某些 Casdoor 认证源（如企业微信、钉钉等）可能不提供邮箱字段。若直接创建无邮箱用户，可能导致下游系统（如邮件服务、通知系统）出现 NPE 或逻辑异常。

**解决方案**: 首次注册时自动生成唯一占位邮箱。

```python
import uuid

def generate_fallback_email(user_id: str, provider: str) -> str:
    """
    为无邮箱用户生成唯一占位邮箱
    格式: {provider}_{user_id}@{FALLBACK_EMAIL_DOMAIN}
    """
    FALLBACK_EMAIL_DOMAIN = "placeholder.local"
    return f"{provider}_{user_id}@{FALLBACK_EMAIL_DOMAIN}"

def process_casdoor_user(user_info: dict) -> dict:
    email = user_info.get("email")
    
    if not email or email.strip() == "":
        # 生成唯一占位邮箱，防止下游系统 NPE
        user_info["email"] = generate_fallback_email(
            user_info.get("id", str(uuid.uuid4())),
            user_info.get("type", "unknown")
        )
        user_info["is_fallback_email"] = True  # 标记为自动生成
    
    return user_info
```

**生成的邮箱示例**: `wechat_abc123@placeholder.local`

**后续处理建议**:
- 允许用户在个人中心补充真实邮箱
- 识别此类邮箱时不发送营销类邮件
- 管理员可按需清理长期未激活的占位账号

## 3. 字段映射标准
集成时建议遵循以下映射准则：

| 外部字段 (Casdoor) | 通用映射含义 | 说明 |
| :--- | :--- | :--- |
| `name` | `Login Name` | 唯一系统标识符。 |
| `email` | `Primary Contact` | 用于账户自动关联的关键字段。 |
| `displayName` | `Nickname / Name` | 前端显示的友好名称。 |
| `avatar` | `Avatar URL` | 用户的头像链接。 |
| `id` | `External Identity` | 用于唯一确定外部来源身份的 ID。 |

## 4. 混合认证设计建议
- **多源登录**: 前端登录界面应同时提供“内置账户登录”和“SSO 登录”入口。
- **权限继承**: 关联后的用户应同时拥有其在内置系统中原有的权限以及根据 Casdoor 角色新同步的权限。
