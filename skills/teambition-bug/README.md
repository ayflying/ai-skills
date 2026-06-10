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

如果工作流没有“修改中”，先用 `list-status` 查看可用状态，再用 `update-status --status-name "<状态名>" --yes` 更新，或只用 `comment/quick-reply` 留言同步进展。

更多说明见 `SKILL.md`。
