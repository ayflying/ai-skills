---
name: gitea-weekly-report
description: |
  获取一个或多个 Gitea 组织内项目的工作日志，遍历仓库全部分支提交，过滤技术噪音，并转换成用户能看懂的功能周报。
  Use when: (1) 获取XX组织的项目工作日志 (2) 生成一个或多个 Gitea 组织的周报 (3) 查看团队上周的工作内容 (4) 将技术提交转换为业务功能点
---

# Gitea 周报生成技能

## 功能说明

通过 Gitea API 获取一个或多个组织下所有仓库、所有分支的提交记录，按时间范围筛选、按 commit SHA 去重、过滤技术噪音，并生成按项目分组的用户可读周报。

## 安装指南

```bash
npx skills add ayflying/ai-skills --skill gitea-weekly-report
```

## 输入要求

- 支持单组织或多组织输入，例如 `esm`、`game_server`，也支持完整组织 URL，例如 `https://gitea.example.com/esm`、`https://gitea.example.com/game_server`。
- 多个组织必须逐个抓取，最后合并为一份周报。
- 从完整 URL 中提取 Gitea base URL 和组织名；如果用户只给组织名，沿用当前已知或用户提供的 Gitea base URL。
- 认证优先使用 HTTP Basic Auth（用户名:token）或访问令牌，不要在输出中暴露 token。

```bash
curl.exe -s -u "username:token" "https://gitea.example.com/api/v1/..."
```

## 时间口径

- 默认“上周”按自然周计算：上周一 `00:00:00` 到本周一 `00:00:00`，结束时间不包含。
- 输出正式周报前必须明确告知实际日期范围，例如：`本次周报范围：2026-05-11 00:00:00 ~ 2026-05-18 00:00:00`。
- 如用户指定 `since` 和 `until`，使用用户指定范围，并同样在输出前说明。
- 所有 API 查询使用 ISO 8601 / RFC3339 时间，例如 `2026-05-11T00:00:00%2B08:00`。

## 抓取流程

1. **解析组织输入**：得到组织列表和对应 base URL。
2. **获取仓库列表**：先调用 `/api/v1/orgs/{org}/repos?limit=50&page={page}`。
3. **仓库列表 fallback**：如果组织仓库接口因 token scope、权限或 401/403 失败，改用 `/api/v1/repos/search?limit=50&page={page}`，再按 `owner.login == org` 过滤。
4. **读取分支列表**：每个仓库必须先调用 `/api/v1/repos/{org}/{repo}/branches`。
5. **遍历全部分支**：对每个分支调用 commits 接口，不要只查默认分支。
6. **按 SHA 去重**：同一 commit 出现在多个分支时，只保留一条。
7. **统计提交数量**：正式生成前内部统计每个仓库提交数，例如 `ad-insight: 3, auto-ad: 25`。
8. **执行 lookback 检查**：除正式时间范围外，额外扫描正式开始时间之前 7 天，用于发现可能遗漏。
9. **生成周报**：只将正式时间范围内的有效功能提交写入周报。

## API 端点

### 获取组织仓库列表

```http
GET /api/v1/orgs/{org}/repos?limit=50&page={page}
```

### 仓库列表 fallback

```http
GET /api/v1/repos/search?limit=50&page={page}
```

对搜索结果只保留 `owner.login == org` 的仓库。

### 获取仓库分支

```http
GET /api/v1/repos/{org}/{repo}/branches
```

### 获取分支提交

```http
GET /api/v1/repos/{org}/{repo}/commits?sha={branch_name}&since={start_date}&until={end_date}&limit=100&page={page}
```

如当前 Gitea 版本使用 `branch` 参数，则改用：

```http
GET /api/v1/repos/{org}/{repo}/commits?branch={branch_name}&since={start_date}&until={end_date}&limit=100&page={page}
```

## lookback 检查

- 正式周报范围之外，额外扫描 `正式开始时间 - 7 天` 到 `正式开始时间`。
- lookback 结果只用于排查，不要擅自混入正式周报。
- 如果 lookback 中发现大量功能提交，输出前提醒用户确认是否并入口径。
- 用户确认并入后，直接合并进同一项目功能点，不要输出“建议补入的前置成果”等单独标题。

## 提交过滤规则

默认不输出以下技术噪音：

- `docs:`、`chore:`、`merge:` 开头的提交。
- `bump version`、版本号升级、纯依赖更新、锁文件更新。
- Codex 技能提交、OpenCode 技能提交。
- 暂时提交、临时提交、WIP、表更新、格式化、重命名、目录整理。
- 纯技术实现细节，例如生成 DAO、调整 request 拦截器、修改内部字段名。

如果提交虽然是 `fix:` 或中文短句，但能反映用户可感知的问题，必须转换成功能点输出。

## 面向用户语言转换

- 不要复述技术实现，输出用户、运营、业务方能理解的结果。
- 不要写“修复 request 拦截器 res.data”，要写“接口请求结果解析更稳定”。
- 不要写“model_flag 解耦”，要写“渠道模型配置更灵活，减少不同模型接入时的适配成本”。
- 不要只写“优化”“增强”“调整”，要说明具体改善了什么。
- 多条相近 commit 合并成一个功能点，避免流水账。

## 输出规则

- 仓库标题默认只写 `## ad-insight`，不要写 `## esm / ad-insight`。
- 如果多个组织存在同名仓库，再在标题中加组织区分，例如 `## esm / ad-insight`、`## game_server / ad-insight`。
- 无有效功能提交的仓库不展开内容。
- 输出前先说明正式日期范围；如发现提交数量异常少或 lookback 异常多，先提示用户确认，不要直接生成可能失真的正式周报。

```markdown
# Gitea 上周功能更新

本次周报范围：{start_date} 00:00:00 ~ {end_date} 00:00:00

## {repo_name}

- {用户可读功能点}
- {用户可读功能点}

## {repo_name_2}

- {用户可读功能点}
```

## 提交数量校验

- 正式生成前必须内部统计每个仓库正式范围内的去重提交数。
- 如果用户预期的重点项目提交数异常少，主动提示：`{repo} 本周只查到 X 条提交，是否需要扩大日期范围或检查分支权限？`
- 不要把内部统计表默认放进正式周报，除非用户要求排查明细。

## 原始结果留存

可选保存 `gitea-weekly-raw.json`，方便追溯和复查。字段至少包含：

```json
[
  {
    "org": "esm",
    "repo": "ad-insight",
    "branch": "main",
    "sha": "commit-sha",
    "date": "2026-05-12T10:30:00+08:00",
    "author": "author-name",
    "message": "commit message"
  }
]
```

## 转换示例

| 技术描述 | 用户可读功能点 |
|---------|----------------|
| `修复资源中心刷新列表问题` | `资源中心列表刷新后可以及时显示最新内容` |
| `新增 Google Ads 接口 CreateOrUpdateAdGroup 方法` | `支持创建和更新 Google Ads 广告组` |
| `使用 gf gen dao 自动生成 DAO 层代码` | 不输出 |
| `request interceptor unwrap res.data` | `接口请求结果解析更稳定` |
| `model_flag 解耦` | `渠道模型配置更灵活，减少不同模型接入时的适配成本` |
