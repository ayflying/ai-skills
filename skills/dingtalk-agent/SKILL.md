# dingtalk-agent

```yaml
name: dingtalk-agent
description: |
  钉钉机器人集成 OpenCode AI。通过钉钉发送任务消息，AI 执行完成后结果推回钉钉。
  支持群聊共享上下文和用户独立模式开关，适合团队协作开发。
  必须调用此技能来处理钉钉机器人的启动和配置。
```

## 功能说明
此技能提供以下功能：
1. 钉钉群聊机器人集成
2. 通过 `@机器人` 发送任务消息
3. OpenCode AI 执行任务并将结果推回钉钉群
4. 使用 Go 语言实现，稳定高效

## 使用方式

### 基本调用
```
启动钉钉机器人
```

### 配置说明
在 `main.go` 中配置：
- `ClientID`: 钉钉应用 Client ID
- `ClientSecret`: 钉钉应用 Client Secret
- `Model`: 默认模型配置为 `opencode/minimax-m2.5-free` (MiniMax M2.5 Free)
- `Stream Mode`: 使用 JSON 流式输出格式，实时返回 AI 响应

### 命令格式
在钉钉群中发送：
| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/status` | 查看当前模式和状态 |
| `/opencode <任务>` | 进入 OpenCode 模式并执行任务 |
| `/exit` | 退出 OpenCode 模式 |
| 任意消息 | 在 OpenCode 模式下会自动执行任务，否则回复收到 |

### OpenCode 专注模式说明
1. **自动进入**：在群聊中只需 `@机器人` 发送消息，机器人将自动进入专注模式。
2. **直接响应**：进入模式后，后续发送的任何消息（需符合钉钉消息接收规则）都会被当作任务执行。
3. **快速退出**：发送 `/exit` 立即退出模式。
4. **自动回收**：1 分钟无消息交互，机器人会自动退出专注模式，释放资源。
5. **群聊与私聊模式区别**：
   - **群聊**：所有群成员共享对话上下文（Context），但模式开关按用户独立。
   - **私聊**：用户上下文和模式均完全独立。

### 持久化机制
机器人支持会话状态持久化，重启后不会丢失上下文：
- `sessions.json`：存储每个用户的模式开关状态（`IsInOpenCodeMode`）
- `group_contexts.json`：存储群组的共享 OpenCode 上下文（`OpenCodeSessionID`）
- 这两个文件会自动忽略（.gitignore），不会上传到 Git

## 技术实现
- 使用 WebSocket 长连接接收钉钉消息
- 调用钉钉 SDK 的 `SimpleReplyMarkdown` 方法发送富文本回复
- 通过 `opencode-cli.exe` 执行 OpenCode 任务
- 使用 JSON 流式输出格式，实时返回 AI 响应
- 支持消息去重（基于 `MsgId`），避免钉钉重试导致重复执行
- 异步任务处理，避免钉钉超时重试

## 文件结构
```
.agents/skills/dingtalk-agent/
├── main.go                 # Go 主程序
├── main_test.go            # Go 单元测试
├── go.mod                  # Go 模块定义
├── go.sum                  # Go 依赖锁定
├── SKILL.md                # 技能文档
├── sessions.json           # 用户模式开关（自动生成，忽略）
├── group_contexts.json     # 群组共享上下文（自动生成，忽略）
├── chat.log                # 运行日志（自动生成，忽略）
└── dingtalk-agent.exe      # 编译后的可执行文件（忽略）

## 环境变量
| 变量名 | 说明 | 是否必填 |
|--------|------|----------|
| OPENCODE_SERVER_PASSWORD | OpenCode 服务器密码 | 否 |

## 注意事项
1. 确保 OpenCode 服务器正在运行（端口 9090）
2. 钉钉应用需开启 Stream 模式
3. 需配置正确的 Client ID 和 Client Secret
4. 群聊中多个用户同时使用时，共享同一个 OpenCode 对话上下文
5. 重启机器人后，会自动加载上次的会话状态（需确保 `sessions.json` 和 `group_contexts.json` 文件存在）
6. 消息去重机制会忽略 10 分钟内重复的消息 ID，避免钉钉重试导致重复执行
