---
name: gitea-weekly-report
description: |
  获取 Gitea 组织内项目的工作日志，并自动将技术提交转换为用户能看懂的功能点。
  Use when: (1) 获取XX组织的项目工作日志 (2) 生成XX的周报 (3) 查看XX团队上周的工作内容 (4) 了解XX项目本周做了什么
---

# Gitea 周报生成技能

## 功能说明

通过 Gitea API 获取指定组织下所有仓库的提交记录，自动过滤代码细节，生成按项目分组的面向终端用户的周报日志。

## 安装指南

```bash
npx skills add ayflying/ai-skills --skill gitea-weekly-report
```

## 认证方式

优先使用 HTTP Basic Auth（用户名:密码）或访问令牌：
```bash
curl.exe -s -u "username:token" "https://gitea.example.com/api/v1/..."
```

## API 端点

### 1. 获取组织仓库列表
```
GET /api/v1/orgs/{org}/repos?limit=50
```

### 2. 获取仓库提交记录
```
GET /api/v1/repos/{org}/{repo}/commits?since={start_date}&until={end_date}&limit=100
```

**时间格式**：ISO 8601 / RFC3339，如 `2026-04-06T00:00:00%2B08:00`

**注意**：部分仓库（如 creative-center）可能存在非 master 主分支，需同时查询 `?branch={branch_name}`

### 3. 检查分支（可选）
```
GET /api/v1/repos/{org}/{repo}/branches
```

## 时间范围计算

上周时间范围：
- **开始**：上周一 00:00:00
- **结束**：本周一 00:00:00（不包含）

如需自定义，使用 `since` 和 `until` 参数。

## 输出格式（C端用户视角）

```
# {org} 组织上周功能更新 ({start_date} ~ {end_date})

---

## {repo_name}

- {功能点1}
- {功能点2}
- ...

## {repo_name_2}

- {功能点}
...
```

**规则**：
1. 按仓库分组，不区分开发者
2. **转换视角**：将技术 commit message 转换为 C 端用户可理解的功能描述
   - 去掉技术实现细节（如"修复 xxx API"、"优化 lazyParams"）
   - 用"用户可做什么"来描述功能
   - 描述具体的功能点，不要用"优化"、"增强"等笼统词汇
3. 多行 commit message 提取核心功能点
4. 无提交的仓库列出但不展开内容
5. 镜像库（mirror）可能无法获取提交记录

## 执行流程

1. **获取仓库列表**：调用 `/api/v1/orgs/{org}/repos`
2. **遍历仓库**：对每个仓库调用提交 API
3. **过滤时间**：使用 `since` 和 `until` 参数
4. **格式化输出**：按上述格式输出

## 特殊处理

- **creative-center**：需要检查 `refactoring-v1` 等分支，master 分支可能无新提交
- **镜像仓库**：Gitea API 可能返回空数组
- **大仓库**：使用 `limit=100` 限制，必要时增加

## Commit Message 转换示例

| 技术描述 | C端功能描述 |
|---------|------------|
| "修复资源中心刷新列表问题" | "资源中心列表刷新后自动更新" |
| "新增 Google Ads 接口 CreateOrUpdateAdGroup 方法" | "支持创建和更新 Google Ads 广告组" |
| "使用 gf gen dao 自动生成 DAO 层代码" | 不输出（技术实现细节） |
| "PrimeVue4 lazy 分页" | "列表加载自动加载下一页" |
| "媒体资源支持 ad 字段" | "资源可关联到具体广告" |

## 使用示例

```bash
# 获取 esm 组织上周日志
curl.exe -s -u "username:password" \
  "https://gitea.adesk.com/api/v1/orgs/esm/repos?limit=50"

curl.exe -s -u "username:password" \
  "https://gitea.adesk.com/api/v1/repos/esm/ad-insight/commits?since=2026-04-06T00:00:00%2B08:00&until=2026-04-13T00:00:00%2B08:00&limit=100"
```