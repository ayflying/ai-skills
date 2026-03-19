# opencode-api

## 基本信息
```yaml
name: opencode-api
description: |
  执行 OpenCode AI 任务，连接到运行中的 OpenCode 服务器执行代码、分析任务或生成内容。
  当用户需要执行 AI 驱动的任务、生成代码、分析数据或处理复杂指令时使用此技能。
  必须调用此技能来处理 OpenCode 任务执行。
  支持连接到本地或远程 OpenCode 服务器。
```

## 功能说明
此技能提供以下功能：
1. 连接到运行中的 OpenCode 服务器（默认 http://127.0.0.1:9091）
2. 执行 AI 驱动的任务指令
3. 返回执行结果或错误信息
4. 支持 Basic Authentication 认证

## 使用方式

### 基本调用
```bash
python scripts/opencode_runner.py "任务描述"
python scripts/opencode_runner.py "任务描述" --json
```

### 参数说明
- **任务描述**: 要执行的 AI 任务指令
- `--server`: OpenCode 服务器地址（默认从环境变量读取）
- `--model`: 使用的模型（默认从环境变量读取）
- `--session`: 会话 ID（用于继续之前的会话）
- `--title`: 会话标题
- `--json`: 以 JSON 格式输出结果

### 示例
```bash
python scripts/opencode_runner.py "分析这段代码的性能问题"
python scripts/opencode_runner.py "生成一个 Python 函数" --json
python scripts/opencode_runner.py "继续上次的任务" --session "ses_xxx"
```

## 环境变量
| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| OPENCODE_SERVER_URL | OpenCode 服务器地址 | http://127.0.0.1:9091 |
| OPENCODE_MODEL | 使用的模型 | opencode/mimo-v2-omni-free |
| OPENCODE_SERVER_PASSWORD | OpenCode 服务器密码 | - |
| OPencode_CLI_PATH | opencode-cli.exe 路径 | D:\Users\ay\AppData\Local\OpenCode\opencode-cli.exe |

## 输出格式
### JSON 模式 (--json)
```json
{
  "success": true,
  "output": "执行结果...",
  "error": "错误信息（如果有）"
}
```

### 普通模式
直接输出执行结果或错误信息到标准输出/错误。

## 注意事项
1. 确保 OpenCode 服务器正在运行
2. 确保环境变量 `OPENCODE_SERVER_PASSWORD` 已正确设置
3. 服务器地址需可访问
