# Teambition Bug OpenAPI 参考

默认网关是 `https://open.teambition.com/api`。本技能只使用个人账号 `userToken`，权限与当前 Teambition 登录账号一致。

所有业务接口都需要：

- `Authorization: Bearer <TEAMBITION_USER_TOKEN>`
- `X-Tenant-Id: <企业 ID>`
- `X-Tenant-Type: organization`

项目级接口的 `{projectId}` 来自当前对话提供的产品/项目分享链接，使用命令时显式传 `--project-id`。如果缺少产品 ID，先让用户复制分享链接给 AI，再用 `parse-url` 从 `/project/<id>` 提取。

## 任务查询与上下文

| 能力 | 方法和路径 | 说明 |
| --- | --- | --- |
| 查询任务详情 | `GET /v3/task/query` | query 支持 `taskId`、`shortIds`、`parentTaskId` |
| 查询项目任务 | `GET /v3/project/{projectId}/task/query` | query 支持 `q`、`includeArchived`、`pageToken`、`pageSize` |
| 列出任务动态 | `GET /v3/task/{taskId}/activity/list` | query 支持 `pageSize`、`pageToken`、`actions`、`excludeActions`、`creatorIds`、`language`、`orderBy` |
| 获取任务进展 | `GET /v3/task/{taskId}/traces` | 用于读取任务进展富文本 |
| 富文本渲染 | `GET /v3/task/rtf/render` | 用 `rtfFields` 参数提取备注、自定义富文本字段、任务进展中的 HTML、图片和附件链接 |

脚本会额外递归扫描任务详情、动态和进展原始 JSON 中的 URL 字段，并用 `download-images` 下载可访问图片。Teambition 有时只返回 `[图片]` 占位且不暴露 URL，此时需要让用户补充可访问截图或截图文字。

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
- 不同产品的状态名称不同，进入处理时可匹配“修改中、修复中、处理中、进行中、已认领、已领取”等正在处理语义状态。
- 任务读取和写入前必须校验第一执行者：常见字段是 `executorId`，多执行者字段则取列表第一个；只有等于 `TEAMBITION_SELF_USER_ID` 才继续。
- 富文本资源接口需要根据任务详情、任务进展或自定义字段中的富文本 ID 拼接 `rtfFields`。
- 个人 token 过期或账号无项目权限时会返回鉴权或权限错误，需要用户重新获取 token 或确认项目成员权限。
