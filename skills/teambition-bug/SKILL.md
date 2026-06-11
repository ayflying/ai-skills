---
name: teambition-bug
description: |
  Teambition Bug 管理技能，使用个人账号 userToken 直接调用官方 OpenAPI 读取、分析、留言和推进项目缺陷任务，不依赖 teambition_cli 或 MCP。
  Use when: (1) 需要读取 Teambition bug/缺陷任务详情、备注、图片附件和留言动态 (2) 需要对疑问信息自动留言追问 (3) 需要修改任务状态为修改中或更新标题、备注、执行人、优先级、截止时间 (4) 需要查询或创建缺陷分类
---

# Teambition Bug 管理

使用个人账号权限直连 Teambition 官方 OpenAPI，适合处理项目里的 bug、缺陷、任务状态推进和补充留言。

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill teambition-bug
```

## 准备工作

1. 进入技能目录并安装依赖：

```bash
cd skills/teambition-bug
pip install -r requirements.txt
```

2. 复制 `.env.example` 为 `.env`，填入个人 token 和企业 ID：

```bash
cp .env.example .env
```

必须配置：

- `TEAMBITION_TENANT_ID`: 企业 ID，对应请求头 `X-Tenant-Id`。
- `TEAMBITION_USER_TOKEN`: 个人账号 token，权限与当前 Teambition 登录账号一致。

真实 token 只能放在本地 `.env` 或当前 Shell 环境变量中，不能写入仓库文件。其他设备安装技能后，只要复制 `.env.example`、填入自己的 `TEAMBITION_USER_TOKEN` 和 `TEAMBITION_TENANT_ID`，即可按该账号的企业权限使用。

企业 ID 可从企业链接 `/organization/<id>/my` 中取得。产品/项目 ID 不写入全局环境变量；不同对话处理不同产品时，从用户在当前对话提供的 Teambition 产品/项目分享链接中解析。脚本默认使用 `https://open.teambition.com/api`，通常不需要配置网关地址。

## 常用命令

```bash
# 解析 Teambition 链接中的 projectId、taskId、viewId
python scripts/teambition_bug.py parse-url --url "https://www.teambition.com/project/6a292e9b13e121404ffea8c5/tasks/view/6a292e9b8e598fd9e0fb2515"

# 按项目 TQL 查询任务
python scripts/teambition_bug.py search --project-id "<projectId>" --tql "content CONTAIN \"登录\""

# 读取 bug 完整上下文：标题、备注、动态、进展、富文本图片/附件链接
python scripts/teambition_bug.py context --task-id "<taskId>"

# 只读取留言/动态记录
python scripts/teambition_bug.py activities --task-id "<taskId>"

# 从动态中过滤评论记录
python scripts/teambition_bug.py comments --task-id "<taskId>"

# 遇到疑问 bug 时留言追问
python scripts/teambition_bug.py ask --task-id "<taskId>" --question "请补充复现步骤、期望结果和实际结果，方便定位。"

# 回复任务，可引用某条动态或评论 ID
python scripts/teambition_bug.py reply --task-id "<taskId>" --reply-to "<activityId>" --content "我已开始排查。"

# 使用常用模板回复
python scripts/teambition_bug.py quick-reply --task-id "<taskId>" --template need-info

# 将任务状态改为“修改中”
python scripts/teambition_bug.py start --task-id "<taskId>" --status-name "修改中" --yes

# 或按当前工作流已有状态更新，例如待验收
python scripts/teambition_bug.py update-status --task-id "<taskId>" --status-name "待验收" --yes
```

## 操作规则

- 修改状态、执行人、优先级、截止时间或留言前，先读取任务详情确认目标任务。
- 用户只给产品/项目链接时，先用 `parse-url` 解析 `projectId`，后续项目级命令都显式传 `--project-id <projectId>`；`tasks/view/<id>` 是视图 ID，不当作任务 ID。
- 如果项目级命令缺少 `--project-id`，引导用户复制 Teambition 产品/项目分享链接给 AI，让 AI 从链接里的 `/project/<id>` 提取产品 ID 后重试。
- “修改中”不是固定 ID，必须先调用状态列表并按名称匹配。
- 如果当前工作流没有“修改中”，先向用户说明可用状态，再选择最接近的状态或只留言同步进展。
- 官方公开文档未提供单独“回复某条评论”的任务接口；`reply` 会引用动态/评论 ID 并创建一条新的任务评论。
- 疑问 bug 优先留言追问，不擅自推进状态；疑问通常包括缺少复现步骤、期望结果、实际结果、环境信息或截图无法访问。
- 图片和附件默认只提取链接和元信息，不批量下载。
- 删除、批量替换、移动到不可逆状态等破坏性操作必须获得用户明确授权。
- 个人 token 失效或权限不足时，让用户重新登录 Teambition 后刷新 token，或确认该账号是否已加入对应企业和项目。

## API 参考

需要接口细节时读取 `references/api.md`。脚本封装了常用路径，但 Teambition API 可能更新，遇到字段不匹配时先查官方文档再调整脚本。
