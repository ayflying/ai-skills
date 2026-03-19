# DingTalk AI Agent (钉钉AI助手)

```yaml
name: dingtalk-agent
description: |
  钉钉AI助手，通过钉钉机器人接收用户消息并执行任务。
  支持专注模式：被@一次后进入专注模式，10分钟内无需重复@。
  集成 opencode-api 技能执行 OpenCode 任务。
  集成 jimeng-ai-generator 技能生成AI图片。
```

## 功能说明
1. **专注模式**：
   - 被@一次后自动进入专注模式
   - 10分钟内无需重复@即可继续对话
   - 发送 `/exit` 退出专注模式
   - 10分钟无活动自动退出

2. **OpenCode 集成**：
   - 通过 opencode-api 技能执行代码任务
   - 默认使用 MiMo V2 Omni Free 模型

3. **即梦AI集成**：
   - 发送 `/jimeng <提示词>` 生成AI图片
   - 通过 jimeng-ai-generator 技能执行

## 支持的命令
| 命令 | 说明 |
|------|------|
| /help | 显示帮助信息 |
| /opencode | 进入专注模式 |
| /exit | 退出专注模式 |
| /status | 查看当前状态 |
| /jimeng <提示词> | 生成AI图片 |

## 会话命名规则
- **私聊**：`昵称-ID后8位`（如：`安阳-3764874`）
- **群聊**：`群聊-群组ID后8位`（如：`群聊-bNYC2YaxJdPp4=`）

## 依赖技能
- **opencode-api**: 执行 OpenCode AI 任务
- **jimeng-ai-generator**: 生成AI图片

## 环境变量
| 变量名 | 说明 |
|--------|------|
| OPENCODE_SERVER_PASSWORD | OpenCode 服务器密码（必须） |
| OPENCODE_MODEL | 默认模型（默认：opencode/mimo-v2-omni-free） |
| OPENCODE_SERVER_URL | OpenCode 服务器地址（默认：http://127.0.0.1:9091） |

## 文件结构
```
dingtalk-agent/
├── SKILL.md              # 技能文档
├── main.go               # 主程序（仅消息处理，调用 opencode-api 技能）
├── dingtalk-bot.exe      # 编译后的可执行文件
├── sessions.json         # 用户会话状态（自动生成）
└── group_contexts.json   # 群组上下文（自动生成）
```

## 注意事项
1. 确保 OpenCode 服务器正在运行
2. 确保环境变量 `OPENCODE_SERVER_PASSWORD` 已正确设置
3. 钉钉应用需开启 Stream 模式
4. 重启机器人后会自动加载上次的会话状态
