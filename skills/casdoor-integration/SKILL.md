---
name: casdoor-integration
description: |
  通用的 Casdoor SSO/IAM 集成指南。支持跨语言 OAuth2/OIDC 认证逻辑。
  Use when: (1) 需要集成 Casdoor 单点登录 (2) 需要实现 OAuth2/OIDC 认证 (3) 需要用户组和组织架构同步 (4) 需要处理 Session 管理和权限映射 (5) 需要解决 OAuth 回调 401 错误
---

# Casdoor 全功能通用集成指南

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill casdoor-integration
```

## 1. OAuth2 登录流程 (手动模式)

### 第一步：生成登录跳转

手动构建 URL，不依赖后端插件：

```
GET <CASDOOR_ENDPOINT>/login/oauth/authorize
  ?client_id=<ID>
  &response_type=code
  &redirect_uri=<已登记的可信回调地址>
  &scope=read:users+openid+profile+email
  &state=<随机字符串>
  &nonce=<绑定当前登录事务的随机值>
```

**重要**：使用密码学安全随机数生成 `state` 和 OIDC `nonce`，按登录事务保存在服务端会话中，绑定浏览器会话、选定的回调地址和短有效期。构造查询参数时使用 URL 编码，不手工拼接用户输入。

**回调地址必须来自可信配置**：

在 Casdoor 后台逐一登记允许的完整回调 URL（包括协议、域名、端口和路径），不要用通配符放宽边界。多域名部署仅从服务端白名单选择，不直接信任 `Host`、`Referer` 或 `X-Forwarded-*`。确需代理头时，只接受已配置可信代理覆盖的值，再做完整白名单校验。

```python
CALLBACK_URLS = {
    "production": "https://app.example.com/auth/casdoor/callback",
    "development": "http://localhost:8000/auth/casdoor/callback",
}


def get_callback_url(deployment: str) -> str:
    # deployment 来自服务端部署配置，不是浏览器参数或请求头
    return CALLBACK_URLS[deployment]
```

### 第二步：回调处理 (Code Exchange)

1. 接收 `code` 和 `state`；在交换 Token 前，核对 `state` 与当前会话内登录事务一致、未过期且未使用。用原子操作一次性消费，拒绝缺失、失配、过期和重放；并发登录按事务分别保存，不用一个全局值覆盖。
2. 交换 Token：`POST <ENDPOINT>/api/login/oauth/access_token`，使用事务中保存的同一 `redirect_uri`。支持 PKCE 的部署同时校验并传递对应 `code_verifier`。
3. 建立会话前验证 ID Token：仅允许服务端配置的签名算法，使用可信 issuer 的公钥验签，强制校验 `iss`、`aud`、`exp`、`nonce`，并按协议检查 `nbf`、`iat`、多受众时的 `azp`。普通签名 JWT（JWS）是验签而非“解密”，不能只做 Base64 解码。
4. 使用 `access_token` 调用可信的 `<ENDPOINT>/api/get-account` 获取资料，核对账号主体与已验证的 OIDC `sub` 的服务端映射、组织及启用状态；不得用前端提交的用户资料创建身份。
5. 完成账号归属和租户授权检查后轮换 Session ID，再注入本地用户。任何验证失败都不建立登录态。

**请求正文**:
```json
{
  "grant_type": "authorization_code",
  "client_id": "...",
  "client_secret": "...",
  "code": "...",
  "redirect_uri": "<与授权请求完全一致的可信回调URL>"
}
```

### 第三步：解析用户信息（重要）

从已验证的响应提取用户信息，使用 `(issuer, organization, sub)` 作为外部身份键。`uid` / `id` 仅在当前 Casdoor 版本已确认与 `sub` 的可信映射后使用，禁止仅凭 email、用户名或跨系统同编号自动认定身份：

- `sub` - 已验签 Token 中的主体标识；与 issuer、组织共同确定外部身份
- `uid` / `id` - 用户资料编号，不是可独立证明身份的凭证
- `name` - 用户名
- `email` - 邮箱（可能为空），**禁止用作登录标识**
- `avatar` - 头像 URL
- `groups` - 用户组列表

## 2. 账户关联 (Account Linking)

当系统已有内置用户体系时，遵循"身份合并"原则：

### 工作流

1. **外部身份查找**：按 `(issuer, organization, sub)` 查找已有绑定，并检查对应本地账号仍可登录。
2. **验证已有账号归属**：未绑定时，要求用户重新认证本地账号并确认绑定；仅可使用经管理员审核、可审计的可信迁移映射替代此步骤。不能凭相同 `uid`、用户名或邮箱静默合并。
3. **原子建立绑定**：校验租户归属，为外部身份键设置唯一约束；已绑定其他账号时拒绝覆盖并人工核查。
4. **按策略创建**：无绑定且允许该组织用户注册时创建低权限本地账号；否则拒绝登录或进入审批。

### 字段映射

| Casdoor 字段 | 内部字段 | 说明 |
| :--- | :--- | :--- |
| `iss` + 组织 + `sub` | 外部身份关联键 | 经验证的主体；本地 `user_id` 独立生成，不按同号合并 |
| `name` | `username` | 用户名（可变更） |
| `email` | `email` | **非必填**。联系方式，不用于身份判断。如果项目不使用邮箱，直接忽略不进行同步 |
| `displayName` | `nickname` | 前端显示名称 |
| `avatar` | `avatar_url` | 头像链接 |

### 无邮箱用户处理与可选同步 (重要)

由于 Casdoor 中的用户（尤其是来自微信、钉钉等第三方认证源的用户）**可能没有填写邮箱**，在集成时必须遵守以下原则：

1. **邮箱必须是非必填项**：在系统的用户表、注册校验、同步逻辑中，`email` 字段必须允许为空（Nullable），切勿强制校验邮箱。
2. **按需同步**：如果当前项目本身不需要使用邮箱功能，在接入和同步用户数据时，**不需要同步邮箱**到项目中，直接丢弃该字段即可。
3. **数据库兜底（仅限遗留系统强制非空限制）**：如果项目底层数据库遗留了强制邮箱非空的限制且难以修改结构，首次注册时才自动生成占位邮箱进行兜底：

```python
def generate_fallback_email(local_user_id: str) -> str:
    # 本地唯一 ID；占位邮箱不用于绑定或找回密码
    return f"user_{local_user_id}@placeholder.invalid"
```

## 3. 用户组与权限映射

### 结构映射

- **Organization** → 系统的"租户"或"顶级企业实例"
- **Group** → 系统的"部门"、"团队"或"空间"（支持父子层级）
- **Role** → 系统的"功能权限集"

### 用户组匹配

Casdoor 用户组格式为 `组织/用户组名`（如 `MyOrg/Engineering`）：

匹配必须保留 `(issuer, organization, group)` 作用域，并先验证组织是否属于当前本地租户。不得删除组织前缀后按同名组匹配，也不默认取第一个组作为主组。具体白名单示例见 [用户组映射](references/group-mapping.md)。

### 权限同步模式

- **全量同步**：仅替换当前租户内由该外部身份源管理的角色，经显式映射后写入，不重置其他来源角色。
- **增量补丁**：仅增加允许映射的角色，保留本地角色；此模式不会自动撤销上游移除的权限，需另设回收与禁用检查，不能默认把外部角色名当作管理员授权。

## 4. Session 存储冲突解决

### 问题

OAuth 跳转前报错：`Cannot read properties of undefined (reading 'user')`

### 原因

某些框架的 Session 存储层强制要求 `session.user` 存在，但 OAuth 初始化阶段用户尚未登录。

### 解决方案

必须放宽 Session 存储校验：

```python
def save_session(sid, session_data):
    passport = session_data.get("passport") or {}
    user = passport.get("user") or session_data.get("user") or {}
    user_id = user.get("id")

    if user_id:
        update_user_session_cache(user_id, sid)

    # 必须保证 OAuth state 能被存储
    commit_to_database(sid, session_data)
```

## 5. 回调 401 错误排查清单

1. **可信回调一致**：授权、Token 交换及后台登记使用相同的完整回调 URL；域名只从服务端白名单选择，不能为排错而接受任意请求头或通配域名。检查会话 Cookie 能否回传、`state` 是否已过期或被消费，以及 Token 的 issuer、受众和 nonce 是否正确。
2. **容器内网络**: 确保后端容器能访问 Casdoor 服务器
3. **Secret 转义**: 检查 `clientSecret` 是否包含特殊字符导致转义错误
4. **协议匹配**: `http` 与 `https` 必须与 Casdoor 后台配置完全匹配

## 6. 前端构建陷阱

### 问题

容器运行期配置了环境变量，但前端 SSO 按钮不显示。

### 原因

前端项目在 `npm run build` 期间固化环境变量，构建时缺失会导致逻辑被永久禁用。

### 解决方案

- 不依赖环境变量判断 SSO 是否启用
- 通过后端接口（如 `/api/auth/config`）动态获取支持的认证方式

## 7. 混合认证设计

- **多源登录**: 前端同时提供"内置账户登录"和"SSO 登录"入口
- **权限隔离**：保留各来源的角色归属，只在当前租户和显式映射策略内合并权限；外部禁用与撤权必须及时生效，不默认叠加高权限。

## 详细资源

- [认证逻辑与 Session 稳定性](references/auth-logic.md)
- [账户关联与无邮箱处理](references/account-linking.md)
- [用户组与权限映射](references/group-mapping.md)
- [前端构建与环境变量](references/frontend-traps.md)
- [手动 OAuth 实现细节](references/logic.md)
- [跨语言集成详解](references/implementation-logic.md)
- [Session 陷阱详解](references/session-pitfalls.md)
