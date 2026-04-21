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

## 3. 无邮箱用户处理与可选同步 (重要)

由于 Casdoor 中的用户（尤其是来自微信、钉钉等第三方认证源的用户）**可能没有填写邮箱**，集成 Casdoor 时必须遵守以下原则，绝不能因为邮箱为空导致登录或同步失败。

### 3.1 邮箱必须为非必填项
在系统的用户表（Database Schema）、注册校验逻辑、数据同步逻辑中，`email` 字段**必须允许为空（Nullable）**。切勿在代码中强制校验邮箱格式或要求邮箱必填。

### 3.2 按需同步（推荐）
如果当前集成项目本身**不需要使用邮箱功能**（例如不需要发邮件通知），在接入和同步用户数据时，**完全不需要同步邮箱字段**。直接在数据映射阶段丢弃 Casdoor 返回的 email 字段即可，保持本地系统简洁。

### 3.3 数据库兜底（仅限遗留系统强制非空限制）
如果项目底层数据库遗留了强制邮箱非空的限制（如旧版系统的 `NOT NULL` 约束）且短期内难以修改表结构，**仅在此种情况下**，首次注册时才自动生成唯一的占位邮箱进行兜底：

```python
def generate_fallback_email(user_id: str, provider: str) -> str:
    """
    仅用于遗留系统强制要求邮箱非空时的兜底方案
    格式: {provider}_{user_id}@placeholder.local
    """
    FALLBACK_EMAIL_DOMAIN = "placeholder.local"
    return f"{provider}_{user_id}@{FALLBACK_EMAIL_DOMAIN}"

def process_casdoor_user(user_info: dict) -> dict:
    """
    处理 Casdoor 用户信息
    用户编号 (uid) 是唯一标识，邮箱仅作联系用途（如不需要可直接丢弃）
    """
    uid = user_info.get("uid") or user_info.get("id")
    email = user_info.get("email")

    if not uid:
        raise ValueError("用户编号 (uid) 是必填字段")

    # 如果系统强制要求邮箱，且当前用户无邮箱，则生成兜底邮箱
    if not email or email.strip() == "":
        user_info["email"] = generate_fallback_email(uid, user_info.get("type", "unknown"))

    return user_info
```

## 4. 字段映射标准

| 外部字段 (Casdoor) | 内部字段 | 说明 |
| :--- | :--- | :--- |
| `uid` | `user_id` | **用户唯一标识**，用于登录判断 |
| `name` | `username` | 用户名（可变更） |
| `email` | `email` | **非必填**。联系方式，千万不能用于身份判断。如果项目不使用邮箱，直接忽略不进行同步。 |
| `displayName` | `nickname` | 前端显示的友好名称 |
| `avatar` | `avatar_url` | 用户的头像链接 |

## 5. 混合认证设计建议

- **多源登录**: 前端登录界面应同时提供"内置账户登录"和"SSO 登录"入口。
- **权限继承**: 关联后的用户应同时拥有其在内置系统中原有的权限以及根据 Casdoor 角色新同步的权限。
