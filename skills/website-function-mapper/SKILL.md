---
name: website-function-mapper
description: |
  模拟浏览器安全侦察指定网站，提取页面功能、表单字段、动态表单分支、按钮流程、接口线索、手册和 API 文档，帮助 AI 一比一复刻网站功能。
  Use when: (1) 需要分析一个网站有哪些业务功能 (2) 需要完整读取表单字段、约束和联动规则 (3) 需要从网页、帮助文档和 API 说明中提炼复刻规格 (4) 需要在登录后保存浏览器状态继续扫描
---

# website-function-mapper

使用 Playwright 打开真实浏览器，安全侦察指定网站的功能、字段、流程、文档和接口线索，输出给 AI 复刻功能用的 `report.md` 和 `report.json`。复刻完成后，再用浏览器同时验收参考系统和新系统，判断是否一比一复刻。

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill website-function-mapper
```

## 前提条件

```bash
cd skills/website-function-mapper
pip install -r requirements.txt
python -m playwright install chromium
```

## 使用方法

```bash
# 默认安全侦察
python scripts/map_site.py https://example.com

# 需要用户手动登录后继续
python scripts/map_site.py https://example.com --wait-login

# 复用登录态
python scripts/map_site.py https://example.com --storage-state storageState.json

# 注入用户提供的 cookie
python scripts/map_site.py https://example.com --cookies cookies.json

# 指定输出目录和扫描上限
python scripts/map_site.py https://example.com --out outputs/example --max-pages 30 --max-depth 2

# 开启严格验收，低于最低分返回失败退出码
python scripts/map_site.py https://example.com --fail-under-acceptance --min-acceptance-score 85

# 复刻完成后，对照参考系统和新系统做验收
python scripts/accept_site.py --reference-url https://old.example.com --replica-url https://new.example.com --headless

# 也可以直接用两份扫描报告验收
python scripts/accept_site.py --reference-report outputs/reference/report.json --replica-report outputs/replica/report.json
```

## 必须遵守

1. 默认只做安全侦察，不提交会创建、修改、删除、支付、发送、发布数据的表单。
2. 遇到提交、删除、支付、发送、发布、确认、清空等高风险按钮，只记录入口和上下文，不点击。
3. 登录页必须等待用户手动登录；登录完成后保存 `storageState.json`，不要把登录态、cookie、token 写入报告。
4. 如果用户提供 cookie，只用于当前扫描，不在报告中输出原文。
5. 自动读取可访问的帮助、手册、文档、开发者、API、接口、Swagger、OpenAPI、Docs、Help 等入口。
6. 手册/API 文档可能过期，必须优先寻找带“最新、当前版本、更新日期、版本号、latest/current”等信号的文档；文档只作参考。
7. 如果文档说明与网站实际操作、真实表单、按钮、流程或接口行为不一致，必须以网站实际操作为准。
8. 多级表单、分步表单、Tab 表单、弹窗表单、抽屉表单、动态增删行都要逐层展开并记录。
9. 对会影响表单内容的选项，每个分支至少尝试一次；组合过多时记录覆盖范围和未穷尽组合。
10. 表单约束必须记录完整，包括必填、长度、范围、格式、文件类型、只读、禁用、默认值、隐藏字段、按钮启用条件和错误提示。
11. 每次扫描必须生成扫描质量验收结果，判断报告是否足够支撑功能一比一复刻；未达标时必须按补扫建议继续扫描或说明缺口。
12. 新系统复刻完成后，必须用 `accept_site.py` 同时访问参考系统和新系统做复刻验收，比较页面、按钮、表单、字段、约束、动态分支、文档和接口形状。

## 输出说明

- `report.md`：给人和 AI 直接阅读的功能复刻说明。
- `report.json`：结构化页面、流程、表单、字段、依赖、约束、按钮、接口、文档数据。
- `acceptance.json`：验收结果，包含评分、通过项、缺口、补扫建议和覆盖指标。
- `replica-acceptance.md`：复刻系统验收报告，说明新系统相对参考系统缺什么、错什么。
- `replica-acceptance.json`：复刻系统验收结构化数据，可用于自动化流水线或继续修复。
- `storageState.json`：登录态文件，包含敏感信息，只用于复用登录态，禁止提交。

## 信息优先级

网站实际操作是最高优先级。手册、帮助中心和 API 文档用于补充理解字段含义、状态码、权限和业务背景，但可能过期。扫描时应优先读取最新/当前版本文档，并在报告中标记文档新鲜度信号；只要文档与页面实际行为冲突，就按真实页面行为复刻。

## 扫描质量验收

脚本默认按 100 分制验收，最低分 `80`。验收项包括页面扫描、表单采集、字段采集、字段约束、动态表单分支、文档/API 线索、危险动作标记和覆盖说明。

如果用于自动化流水线，使用 `--fail-under-acceptance`，当分数低于 `--min-acceptance-score` 时脚本返回退出码 `2`。

## 复刻系统验收

复刻完成后运行 `accept_site.py`。它会分别扫描参考系统和新系统，或直接读取两份 `report.json`，再对比以下项目：

- 页面和导航入口是否一致。
- 按钮和危险动作入口是否一致。
- 表单数量、分组、字段、字段类型和选项是否一致。
- 必填、长度、范围、格式、文件类型、只读、禁用等约束是否一致。
- 多级表单和选项联动后的动态分支是否一致。
- 帮助文档、API 文档和 XHR/fetch 接口形状是否一致。

默认复刻验收最低分 `95`。使用 `--fail-under` 可在低于最低分时返回退出码 `2`。

## 推荐工作流

1. 首次扫描先使用 `--wait-login`，让用户登录后保存状态。
2. 第二次用 `--storage-state storageState.json` 扫描完整功能。
3. 读取 `report.md` 顶部的验收结果和 `acceptance.json`；必要时提高 `--max-pages`、`--max-depth` 或 `--branch-limit`。
4. 扫描质量验收通过后，将 `report.md`、`report.json` 和 `acceptance.json` 交给 AI，用于复刻后端接口、业务流程、字段校验和权限规则。
5. 新系统完成后运行 `accept_site.py` 做复刻验收，根据 `replica-acceptance.md` 修复缺口，直到状态为 `passed`。
