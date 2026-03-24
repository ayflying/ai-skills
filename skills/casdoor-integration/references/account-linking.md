# 内置用户系统兼容与账户关联逻辑

当目标系统已拥有自身的用户体系时，集成 Casdoor 应遵循"身份合并"原则，而非直接创建冗余账号。

## 1. 核心原则

**用户编号是登录的唯一标识**，邮箱仅作为联系方式，不作为用户身份判断依据。

## 2. 自动关联工作流 (Account Linking)

系统在处理 Casdoor 登录成功的回调后，应执行以下级联查找逻辑：

1. **外部 ID 查找 (最高优先级)**: 检查本地数据库中是否已存在关联此 `Casdoor Provider + ProviderUserID` 的记录。
2. **用户编号匹配**: 如果未找到外部绑定，尝试通过 Casdoor 返回的 `uid` (用户编号) 查找系统现有的内置用户。
3. **静默绑定**: 如果找到同编号用户，将其本地 ID 与 Casdoor ID 建立关联关系。
4. **自动创建**: 仅当上述两步都失败时，才创建全新的本地用户记录。

**重要**: 不再使用邮箱作为用户关联判断依据，邮箱仅用于展示和通知。

## 3. 无邮箱用户的兜底处理

某些 Casdoor 认证源（如企业微信、钉钉等）可能不提供邮箱字段。若直接创建无邮箱用户，可能导致下游系统（如邮件服务、通知系统）出现 NPE 或逻辑异常。

**解决方案**: 首次注册时自动生成唯一占位邮箱（但不作为用户标识）。

```python
import uuid

def generate_fallback_email(user_id: str, provider: str) -> str:
    """
    为无邮箱用户生成唯一占位邮箱
    格式: {provider}_{user_id}@{FALLBACK_EMAIL_DOMAIN}
    注意: 此邮箱仅作为联系方式，不作为用户标识
    """
    FALLBACK_EMAIL_DOMAIN = "placeholder.local"
    return f"{provider}_{user_id}@{FALLBACK_EMAIL_DOMAIN}"

def process_casdoor_user(user_info: dict) -> dict:
    """
    处理 Casdoor 用户信息
    用户编号 (uid) 是唯一标识，邮箱仅作联系用途
    """
    uid = user_info.get("uid") or user_info.get("id")
    email = user_info.get("email")

    if not uid:
        raise ValueError("用户编号 (uid) 是必填字段")

    # 邮箱兜底（仅作为联系方式，不影响用户身份）
    if not email or email.strip() == "":
        user_info["email"] = generate_fallback_email(uid, user_info.get("type", "unknown"))
        user_info["is_fallback_email"] = True  # 标记为自动生成

    return user_info
```

**生成的邮箱示例**: `wechat_abc123@placeholder.local`

**后续处理建议**:
- 允许用户在个人中心补充真实邮箱
- 识别此类邮箱时不发送营销类邮件
- 管理员可按需清理长期未激活的占位账号

## 4. 字段映射标准

| 外部字段 (Casdoor) | 内部字段 | 说明 |
| :--- | :--- | :--- |
| `uid` | `user_id` | **用户唯一标识**，用于登录判断 |
| `name` | `username` | 用户名（可变更） |
| `email` | `email` | 联系方式，不用于身份判断 |
| `displayName` | `nickname` | 前端显示的友好名称 |
| `avatar` | `avatar_url` | 用户的头像链接 |

## 5. 混合认证设计建议

- **多源登录**: 前端登录界面应同时提供"内置账户登录"和"SSO 登录"入口。
- **权限继承**: 关联后的用户应同时拥有其在内置系统中原有的权限以及根据 Casdoor 角色新同步的权限。
