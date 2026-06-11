# Teambition Bug 管理

通过个人账号 `userToken` 直连 Teambition 官方 OpenAPI，直接读取和推进项目 bug，不依赖 `teambition_cli` 或 MCP。

## 安装

```bash
npx skills add ayflying/ai-skills --skill teambition-bug
```

## 配置

```bash
cd skills/teambition-bug
cp .env.example .env
pip install -r requirements.txt
```

编辑 `.env`，填入个人账号 token 和企业 ID。不要把真实 `.env` 提交到 Git。

最小配置：

```env
TEAMBITION_USER_TOKEN=your_user_token
TEAMBITION_TENANT_ID=your_organization_id
```

- `TEAMBITION_USER_TOKEN`: 个人账号 token，权限与当前 Teambition 登录账号一致。
- `TEAMBITION_TENANT_ID`: 企业 ID，例如企业链接 `/organization/<id>/my` 中的 `<id>`。
- 默认网关是 `https://open.teambition.com/api`，不用写入 `.env`。
- 产品/项目 ID 不写入全局环境变量。不同对话可能对应不同产品；如果缺少产品 ID，让用户复制 Teambition 产品/项目分享链接给 AI，AI 可用 `parse-url` 从链接里的 `/project/<id>` 提取 `projectId`。
- 其他设备使用时，只需要安装技能、安装 Python 依赖，并填入自己的 `TEAMBITION_USER_TOKEN` 和 `TEAMBITION_TENANT_ID`。

## 示例

```bash
python scripts/teambition_bug.py parse-url --url "https://www.teambition.com/project/6a292e9b13e121404ffea8c5/tasks/view/6a292e9b8e598fd9e0fb2515"
python scripts/teambition_bug.py search --project-id "<projectId>" --tql "content CONTAIN \"登录\""
python scripts/teambition_bug.py context --task-id "<taskId>"
python scripts/teambition_bug.py comments --task-id "<taskId>"
python scripts/teambition_bug.py reply --task-id "<taskId>" --reply-to "<activityId>" --content "我已开始排查。" --yes
python scripts/teambition_bug.py ask --task-id "<taskId>" --question "请补充复现步骤、期望结果和实际结果。"
python scripts/teambition_bug.py quick-reply --task-id "<taskId>" --template need-info
python scripts/teambition_bug.py list-status --task-id "<taskId>"
python scripts/teambition_bug.py start --task-id "<taskId>" --status-name "修改中" --yes
```

如果工作流没有“修改中”，先用 `list-status` 查看可用状态/标签状态，再用 `update-status --status-name "<状态名>" --yes` 更新，或只用 `comment/quick-reply` 留言同步进展。

如果运行 `search`、`list-bug-groups` 或 `create-bug-group` 时没有 `projectId`，先让用户发产品/项目分享链接，再执行 `parse-url --url "<链接>"` 获取。

批量处理 bug 时按紧急程度从高到低推进。遇到需求不明确的任务，先留言追问并继续下一个任务；完成后再回头检查已追问任务是否有新回复。开始处理时优先把状态/标签状态改为“修改中”，没有则匹配“修复中、处理中、进行中、已认领、已领取”等表示正在处理的状态。

更多说明见 `SKILL.md`。
