# Teambition Bug OpenAPI 参考

默认网关是 `https://open.teambition.com/api`。本技能只使用个人账号 `userToken`，权限与当前 Teambition 登录账号一致。

所有业务接口都需要：

- `Authorization: Bearer <TEAMBITION_USER_TOKEN>`
- `X-Tenant-Id: <企业 ID>`
- `X-Tenant-Type: organization`

## 当前用户

| 能力 | 方法和路径 | 说明 |
| --- | --- | --- |
| 获取当前用户基本信息 | `GET /users/me` | 用 `userToken` 获取当前登录账号信息，响应中包含 `userId`，脚本用它判断第一执行者是否为自己 |

项目级接口的 `{projectId}` 来自当前对话提供的产品/项目分享链接，使用命令时显式传 `--project-id`。如果缺少产品 ID，先让用户复制分享链接给 AI，再用 `parse-url` 从 `/project/<id>` 提取。

## 任务查询与上下文

| 能力 | 方法和路径 | 说明 |
| --- | --- | --- |
| 查询项目/产品详情 | `GET /v3/project/query` | query 支持 `projectIds`，用于校验项目 ID 是否可访问 |
| 查询任务详情 | `GET /v3/task/query` | query 支持 `taskId`、`shortIds`、`parentTaskId` |
| 查询项目任务 | `GET /v3/project/{projectId}/task/query` | query 支持 `q`、`includeArchived`、`pageToken`、`pageSize` |
| 列出任务动态 | `GET /v3/task/{taskId}/activity/list` | query 支持 `pageSize`、`pageToken`、`actions`、`excludeActions`、`creatorIds`、`language`、`orderBy` |
| 获取任务进展 | `GET /v3/task/{taskId}/traces` | 用于读取任务进展富文本 |
| 富文本渲染 | `GET /v3/task/rtf/render` | 用 `rtfFields` 参数提取备注、自定义富文本字段、任务进展中的 HTML、图片和附件真实下载链接 |

富文本图片不能只看 `task.note` 里的 `[图片]` 降级文本。官方流程是调用 `GET /v3/task/rtf/render`：

- 任务备注：`<taskId>:note`
- 任务进展：`<taskId>:trace:<traceId>`，`traceId` 来自 `GET /v3/task/{taskId}/traces`
- 富文本自定义字段：`<taskId>:cf:<cfId>`，`cfId` 来自任务详情 `customfields`

接口返回的每项包含 `html`、`rtfField`、`rtfValueToken` 和 `taskId`。`rtfValueToken` 是 JSON 字符串，其中 `attachments` 字段保存富文本中的图片和附件真实下载地址；这些地址有有效期，长度与 `htmlExpireSeconds` 参数一致。脚本会自动解析 `rtfValueToken.attachments`，并额外递归扫描任务详情、动态和进展原始 JSON 中的 URL 字段。

下载 `rtfValueToken.attachments` 里的 OSS 签名直链时不要带 OpenAPI 的 `Authorization` 请求头；签名 URL 自身负责鉴权。`download-images` 已自动区分 OpenAPI 请求和图片直链下载。

如果 `context` 仍然只有 `[图片]` 占位且 `mediaResources.images` 为空，再让用户补充可访问截图或截图文字。

## 留言和状态

| 能力 | 方法和路径 | 请求体 |
| --- | --- | --- |
| 评论任务 | `POST /v3/task/{taskId}/comment` | `content`、`renderMode`、`fileTokens`、`mentionUserIds` |
| 查询可用状态 | `GET /v3/task/{taskId}/tfs` | 无 |
| 更新任务状态 | `PUT /v3/task/{taskId}/taskflowstatus` | `taskflowstatusId` 或 `tfsName`，可带 `tfsUpdateNote` |

公开文档未暴露单独“回复某条任务评论”的接口；如需回复某条动态，建议在 `POST /v3/task/{taskId}/comment` 的内容中引用动态或评论 ID。
本技能的 `reply` 命令采用该策略，`quick-reply` 命令则使用内置模板创建普通评论。

## 常用更新

| 能力 | 方法和路径 | 请求体 |
| --- | --- | --- |
| 更新标题 | `PUT /v3/task/{taskId}/content` | `content` |
| 更新备注 | `PUT /v3/task/{taskId}/note` | `note`、`renderMode` |
| 更新执行人 | `PUT /v3/task/{taskId}/executor` | `executorId` |
| 查询企业优先级 | `GET /v3/project/priority/list` | query 可传 `organizationId` |
| 更新优先级 | `PUT /v3/task/{taskId}/priority` | `priority` 或 `priorityName` |
| 更新截止时间 | `PUT /v3/task/{taskId}/dueDate` | `dueDate` |

## 缺陷分类

| 能力 | 方法和路径 | 参数 |
| --- | --- | --- |
| 获取缺陷分类列表 | `GET /v3/project/{projectId}/bug/commongroup` | query 支持 `commongroupIds`、`parentCommongroupId`、`pageSize`、`pageToken` |
| 创建缺陷分类 | `POST /v3/project/{projectId}/bug/commongroup/create` | body 需要 `name`，可传 `parentId`、`description` |

## 注意事项

- `tasks/view/<id>` 是视图 ID，不等于任务 ID。
- 任务链接通常是 `https://www.teambition.com/task/{taskId}`。
- 状态名称如“修改中”必须先查询当前任务所在工作流状态列表再匹配。
- 工作流状态不一定等于看板列或卡片类型。真实看板字段需要从任务详情中的 `stageId`、`sfcId`、`tasklistId`、`customfields`、`isDone` 等字段审计；脚本的 `audit-task` 会集中输出这些字段。
- 不同产品的状态名称不同，进入处理时可匹配“修改中、修复中、处理中、进行中、已认领、已领取”等正在处理语义状态。
- 确认要修复某个任务时，优先使用 `claim-context`，先调用 `PUT /v3/task/{taskId}/taskflowstatus` 抢占到处理中状态，再读取完整上下文；普通 `context/get` 只用于判断信息是否明确。
- 修复并验证完成后使用 `finish --verification "<实际验证结果>"` 推进到待验收类状态。若没有精确“待验收”，可匹配“待验证、待测试、待确认、待审核、验收中、提测”等近义状态；不要自动推进到“已完成、关闭、已解决、上线”等终态。已知目标看板字段时，要同时传 `--expect-stage-id`、`--expect-sfc-id`、`--expect-tasklist-id` 或 `--expect-custom-field "字段=值"`，让脚本在更新后回读校验，避免只改了工作流状态但卡片仍留在原列。
- 任务读取和写入前必须校验第一执行者：常见字段是 `executorId`，多执行者字段则取列表第一个；只有等于 `GET /users/me` 返回的当前 `userId` 才继续。
- 富文本资源接口需要根据任务详情、任务进展或自定义字段中的富文本 ID 拼接 `rtfFields`；多个值用英文逗号分隔，最多 50 个。
- 个人 token 过期或账号无项目权限时会返回鉴权或权限错误，需要用户重新获取 token 或确认项目成员权限。
