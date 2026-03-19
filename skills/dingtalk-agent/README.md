# DingTalk Agent

钉钉机器人集成 OpenCode AI，支持群聊共享上下文和用户独立模式开关。

## 安装

### 标准化安装 (推荐)

使用 `skills` CLI 一键安装：

```bash
npx skills add ayflying/ai-skills --skill dingtalk-agent
```

### 手动安装

1. **克隆仓库**:
   ```bash
   git clone https://github.com/ayflying/ai-skills.git
   cd ai-skills/skills/dingtalk-agent
   ```

2. **配置环境**:
   参考 `.env.example` 创建 `.env` 文件并配置 `CLIENT_ID` 和 `CLIENT_SECRET`。

3. **运行**:
   ```bash
   go mod tidy
   go run main.go
   ```

## 功能特性

- 钉钉群聊机器人集成。
- 支持 OpenCode AI 任务执行。
- 消息去重与异步处理。

## 许可证

MIT License
