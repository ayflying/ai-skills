---
name: opencode-api
description: |
  通过 HTTP API 与 OpenCode 服务器交互，执行 AI 任务、操作会话、发送消息。
  Use when: (1) 需要通过 API 控制 OpenCode (2) 需要创建/管理 OpenCode 会话 (3) 需要发送消息给 AI 并获取响应 (4) 需要获取项目/文件信息
---

# opencode-api

通过 HTTP API 与 OpenCode 服务器交互，无缝执行 AI 任务。

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill opencode-api
```

## 前提条件

1. 启动 OpenCode 服务器：
   ```bash
   opencode serve [--port 4096] [--hostname 127.0.0.1]
   ```

2. 配置环境变量（参考 `.env.example`）

## 使用方式

### 基本调用

```bash
python scripts/opencode_runner.py "任务描述"
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `prompt` | 要执行的 AI 任务指令 | - |
| `--server` | OpenCode 服务器地址 | `OPENCODE_SERVER_URL` |
| `--model` | 使用的模型 | `OPENCODE_MODEL` |
| `--session` | 会话 ID（继续已有会话） | - |
| `--title` | 会话标题 | - |
| `--json` | JSON 格式输出 | false |
| `--no-reply` | 发送消息但不等待响应 | false |

### API 端点映射

此技能封装了 OpenCode Server 的核心 API：

| 功能 | HTTP 方法 | 端点 |
|------|-----------|------|
| 健康检查 | GET | `/global/health` |
| 创建会话 | POST | `/session` |
| 发送消息 | POST | `/session/:id/message` |
| 中止会话 | POST | `/session/:id/abort` |
| 获取会话状态 | GET | `/session/status` |
| 获取项目信息 | GET | `/project` |
| 读取文件 | GET | `/file/content?path=<p>` |
| 搜索文件 | GET | `/find?pattern=<pat>` |
| TUI 控制 | POST | `/tui/*` |

### 示例

```bash
# 基本任务执行
python scripts/opencode_runner.py "分析代码性能问题"

# 继续特定会话
python scripts/opencode_runner.py "继续完成上次的重构" --session "ses_xxx"

# 指定模型
python scripts/opencode_runner.py "生成单元测试" --model "opencode/mimo-v2-omni-free"

# 异步发送（不等待响应）
python scripts/opencode_runner.py "执行代码重构" --no-reply

# JSON 输出
python scripts/opencode_runner.py "解释这段代码" --json
```

## 环境变量

```bash
OPENCODE_SERVER_URL=http://127.0.0.1:4096
OPENCODE_MODEL=opencode/mimo-v2-omni-free
OPENCODE_SERVER_PASSWORD=your-password
OPENCODE_SERVER_USERNAME=opencode
```

## 输出格式

### JSON 模式 (`--json`)

```json
{
  "success": true,
  "session_id": "ses_xxx",
  "output": "执行结果...",
  "error": null
}
```

### 普通模式

直接输出 AI 响应内容。

## 错误处理

| 错误类型 | 说明 |
|----------|------|
| `ConnectionError` | 无法连接到 OpenCode 服务器 |
| `AuthenticationError` | 认证失败 |
| `SessionError` | 会话不存在或已过期 |
| `TimeoutError` | 请求超时 |

## 注意事项

1. 确保 `opencode serve` 已启动
2. 认证密码通过 `OPENCODE_SERVER_PASSWORD` 环境变量设置
3. 服务器默认端口 `4096`，主机名 `127.0.0.1`
4. 消息发送默认等待响应，超时时间 120 秒