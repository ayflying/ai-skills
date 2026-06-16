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

- `TEAMBITION_USER_TOKEN`: 个人账号 token，权限与当前 Teambition 登录账号一致。登录 [Teambition User MCP](https://open.teambition.com/user-mcp) 后创建或查看 `userToken`。
- `TEAMBITION_TENANT_ID`: 企业 ID，例如企业链接 `/organization/<id>/my` 中的 `<id>`。
- 当前用户 ID 不需要手动配置，脚本会用 `TEAMBITION_USER_TOKEN` 调用 `GET /users/me` 自动获取，并用于只读取和处理第一执行者为自己的任务。
- 默认网关是 `https://open.teambition.com/api`，不用写入 `.env`。
- 产品/项目 ID 不写入全局环境变量。不同对话可能对应不同产品；如果缺少产品 ID，让用户复制 Teambition 产品/项目分享链接给 AI，AI 可用 `parse-url` 从链接里的 `/project/<id>` 提取 `projectId`。
- 其他设备使用时，只需要安装技能、安装 Python 依赖，并填入自己的 `TEAMBITION_USER_TOKEN` 和 `TEAMBITION_TENANT_ID`。

## 示例

```bash
python scripts/teambition_bug.py parse-url --url "https://www.teambition.com/project/6a292e9b13e121404ffea8c5/tasks/view/6a292e9b8e598fd9e0fb2515"
python scripts/teambition_bug.py project --project-id "<projectId>"
python scripts/teambition_bug.py search --project-id "<projectId>" --tql "content CONTAIN \"登录\""
python scripts/teambition_bug.py context --task-id "<taskId>"
python scripts/teambition_bug.py download-images --task-id "<taskId>"
python scripts/teambition_bug.py render-rich-text --rtf-fields "<taskId>:note"
python scripts/teambition_bug.py comments --task-id "<taskId>"
python scripts/teambition_bug.py reply --task-id "<taskId>" --reply-to "<activityId>" --content "我已开始排查。" --yes
python scripts/teambition_bug.py ask --task-id "<taskId>" --question "请先说明如何复现：页面入口、具体操作步骤、账号/数据/环境、期望结果和实际结果。"
python scripts/teambition_bug.py quick-reply --task-id "<taskId>" --template need-info
python scripts/teambition_bug.py list-status --task-id "<taskId>"
python scripts/teambition_bug.py audit-task --task-id "<taskId>"
python scripts/teambition_bug.py start --task-id "<taskId>" --status-name "修改中" --yes
python scripts/teambition_bug.py claim-context --task-id "<taskId>" --status-name "修改中" --yes
python scripts/teambition_bug.py finish --task-id "<taskId>" --verification "远程容器编排启动并验证通过" --expect-tasklist-id "<待验收列表ID>" --expect-custom-field "类型=Bug" --yes
python scripts/teambition_bug.py finish --task-id "<taskId>" --verification "写明实际自测/构建/远程验证结果" --yes
```

如果工作流没有"修改中"，先用 `list-status` 查看可用状态/标签状态，再用 `update-status --status-name "<状态名>" --yes` 更新，或只用 `comment/quick-reply` 留言同步进展。

如果运行 `search`、`list-bug-groups` 或 `create-bug-group` 时没有 `projectId`，先让用户发产品/项目分享链接，再执行 `parse-url --url "<链接>"` 获取。

批量处理 bug 时先过滤第一执行者为自己的任务，再按紧急程度从高到低推进。**确认要处理某个任务后，立即执行 `claim-context --task-id "<taskId>" --status-name "修改中" --yes`，它会先抢占到处理中状态，再返回完整上下文。** 如果只需要单独抢占，也可以执行 `start --task-id "<taskId>" --status-name "修改中" --yes`。脚本会发起 Teambition 状态更新请求，识别响应里的业务错误，并在更新后回读任务状态；只有输出中 `verifiedTask.statusId` 等于 `targetStatus.id` 才算抢占成功。命令报错或没有 `verifiedTask` 时，必须停止处理并如实说明状态未变，不能继续声称任务已在修改中；不要把本地推断的工作流字段当成最终结论。Teambition 的看板列、任务列表、卡片类型可能不是 `taskflowstatusId`，还可能由 `stageId`、`sfcId`、`tasklistId` 或 `customfields` 决定；遇到“还在未开始/未完成/类型乱”时先运行 `audit-task --task-id "<taskId>"`，已知道正确字段时在 `start/claim-context/update-status/finish` 上传 `--expect-stage-id`、`--expect-sfc-id`、`--expect-tasklist-id` 或 `--expect-custom-field "字段=值"`，复核失败就不能声称已拖到目标列。不要先读取完整详情再改状态，读取期间任务可能被其他人认领。遇到需求不明确的任务，必须先问清楚如何复现，包括页面入口、具体操作步骤、账号/数据/环境、期望结果和实际结果；留言追问后继续下一个任务，完成后再回头检查已追问任务是否有新回复。明确修复并验证完成后，运行 `finish --task-id "<taskId>" --verification "<实际验证结果>" --yes` 推进到"待验收"；如果产品工作流没有精确名称，脚本会匹配待验证、待测试、待确认、待审核等近义状态。`finish` 不允许省略验证结果，也不能推进到“已完成/关闭”等终态。

回复要简单明了，让策划、测试、运营等非技术人员也能看懂。读取上下文时如果有截图，必须下载并识别图片内容。脚本会用官方 `GET /v3/task/rtf/render` 渲染 `taskId:note`、`taskId:trace:<traceId>` 和可识别的 `taskId:cf:<cfId>`，再从 `rtfValueToken.attachments` 提取真实图片/附件下载链接；如果仍然只有 `[图片]` 占位但没有可访问图片链接，才留言请用户补充可访问截图或把截图关键信息转成文字。

更多说明见 `SKILL.md`。
