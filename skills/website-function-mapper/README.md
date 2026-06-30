# website-function-mapper

用 Playwright 模拟浏览器安全侦察指定网站，提取页面功能、表单字段、动态表单分支、按钮流程、接口线索、手册和 API 文档，帮助 AI 一比一复刻网站功能。

## 安装

```bash
npx skills add ayflying/ai-skills --skill website-function-mapper
```

## 依赖

```bash
cd skills/website-function-mapper
pip install -r requirements.txt
python -m playwright install chromium
```

## 使用

```bash
python scripts/map_site.py https://example.com
python scripts/map_site.py https://example.com --wait-login
python scripts/map_site.py https://example.com --cookies cookies.json
python scripts/map_site.py https://example.com --storage-state storageState.json --out outputs/example
python scripts/map_site.py https://example.com --fail-under-acceptance --min-acceptance-score 85
python scripts/accept_site.py --reference-url https://old.example.com --replica-url https://new.example.com --headless
python scripts/accept_site.py --reference-report outputs/reference/report.json --replica-report outputs/replica/report.json
```

## 常用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 目标网址 | 必填 |
| `--out` | 输出目录 | `outputs/<host>-<timestamp>` |
| `--storage-state` | Playwright 登录态文件 | `storageState.json` |
| `--cookies` | cookie JSON 文件 | 无 |
| `--wait-login` | 等待用户手动登录 | 关闭 |
| `--headless` | 使用无头浏览器 | 关闭 |
| `--max-pages` | 最大页面数 | `20` |
| `--max-depth` | 最大同域链接深度 | `2` |
| `--branch-limit` | 每个动态表单控件最多尝试选项数 | `8` |
| `--min-acceptance-score` | 验收最低分 | `80` |
| `--fail-under-acceptance` | 验收低于最低分时返回退出码 `2` | 关闭 |

## 输出

- `report.md`：面向 AI 和人工阅读的复刻说明。
- `report.json`：结构化数据，包含页面、字段、约束、按钮、流程、文档、接口线索。
- `acceptance.json`：验收结果，包含评分、通过项、缺口、补扫建议和覆盖指标。
- `replica-acceptance.md`：复刻系统验收报告，说明新系统相对参考系统缺什么、错什么。
- `replica-acceptance.json`：复刻系统验收结构化数据，可用于自动化流水线或继续修复。
- `storageState.json`：登录态文件，包含敏感信息，禁止提交。

## 扫描质量验收

脚本默认生成验收结果，并把摘要写入 `report.md` 顶部。验收项覆盖页面、表单、字段、约束、动态分支、文档/API、危险动作标记和覆盖说明。低于最低分时状态为 `needs_review`，并给出补扫建议。

## 复刻系统验收

复刻完成后使用 `scripts/accept_site.py` 对照参考系统和新系统。它会分别访问两个系统，或读取两份 `report.json`，比较页面、按钮、表单、字段、约束、动态表单分支、文档和接口形状。

```bash
python scripts/accept_site.py --reference-url https://old.example.com --replica-url https://new.example.com --headless --min-score 95 --fail-under
```

输出状态为 `passed` 才代表功能复刻验收通过；否则查看 `replica-acceptance.md` 的缺失项、不一致项和修复建议。

## 安全边界

脚本默认不会提交表单，不执行删除、支付、发布、发送、清空等危险动作。它会记录这些动作的入口、按钮文案、上下文和可能接口，但不会替用户点击。
