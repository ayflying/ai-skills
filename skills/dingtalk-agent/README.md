# DingTalk Agent

一个集成钉钉机器人的 OpenCode AI 技能，支持群聊共享上下文和用户独立模式开关，适合团队协作开发。

## 功能特性

- **钉钉群聊机器人集成**：通过 `@机器人` 发送任务消息
- **OpenCode AI 执行**：AI 执行任务并将结果推回钉钉群
- **群聊共享上下文**：群组成员共享同一个对话上下文
- **用户独立模式**：每个用户的模式开关独立控制
- **消息去重**：避免钉钉重试导致重复执行
- **异步处理**：避免钉钉超时重试

## 安装

### 标准化安装（推荐）

使用 `skills` CLI 安装：

```bash
npx skills add ayflying/ai-skills --skill dingtalk-agent
```

安装后会自动创建技能目录并链接到你的 Agent。

### 手动安装

#### 前置要求

- Go 1.16 或更高版本
- 钉钉企业应用（需开启 Stream 模式）
- OpenCode 服务器（运行在端口 9090）

#### 安装步骤

##### 1. 克隆仓库

```bash
git clone https://github.com/ayflying/ai-skills.git
cd ai-skills/skills/dingtalk-agent
```

#### 2. 安装依赖

```bash
go mod tidy
```

#### 3. 配置钉钉应用

复制 `.env.example` 文件为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 钉钉应用配置
CLIENT_ID=your-client-id
CLIENT_SECRET=your-client-secret

# OpenCode 模型配置（可选）
CURRENT_MODEL=opencode/minimax-m2.5-free
```

**如何获取 Client ID 和 Client Secret：**

1. 登录钉钉开放平台：https://open.dingtalk.com
2. 进入"应用开发" → "企业内部应用"
3. 创建或选择你的应用
4. 在"应用信息"中查看 `Client ID` 和 `Client Secret`
5. 在"权限管理"中开通"Stream模式"

#### 4. 配置 OpenCode 服务器

确保 OpenCode 服务器正在运行：

```bash
# 启动 OpenCode 服务器（端口 9090）
opencode serve
```

#### 5. 编译运行

```bash
# 编译
go build -o dingtalk-agent.exe main.go

# 运行
./dingtalk-agent.exe
```



## 使用方式

### 基本命令

在钉钉群中发送以下命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/status` | 查看当前模式和状态 |
| `/opencode <任务>` | 进入 OpenCode 模式并执行任务 |
| `/exit` | 退出 OpenCode 模式 |
| 任意消息 | 在 OpenCode 模式下会自动执行任务 |

### OpenCode 模式说明

1. 发送 `/opencode` 进入 OpenCode 模式
2. 之后发送的任何消息都会被当作 OpenCode 任务执行
3. 发送 `/exit` 退出 OpenCode 模式
4. 1小时无消息自动退出 OpenCode 模式

**群聊与私聊模式区别**：
- **群聊**：所有群成员共享同一个对话上下文，但每个用户的模式开关独立
- **私聊**：每个用户完全独立，上下文和模式开关均独立

## 文件结构

```
dingtalk-agent/
├── main.go                 # Go 主程序
├── main_test.go            # Go 单元测试
├── go.mod                  # Go 模块定义
├── go.sum                  # Go 依赖锁定
├── SKILL.md                # 技能文档
├── README.md               # 本文件
├── .gitignore              # Git 忽略文件
├── .env.example            # 环境变量配置模板
├── .env                    # 环境变量配置（自动生成，忽略）
├── sessions.json           # 用户模式开关（自动生成，忽略）
├── group_contexts.json     # 群组共享上下文（自动生成，忽略）
├── chat.log                # 运行日志（自动生成，忽略）
└── dingtalk-agent.exe      # 编译后的可执行文件（忽略）
```

## 配置说明

### 从 .env 文件读取

技能会自动从 `.env` 文件读取以下配置：

| 变量名 | 说明 | 默认值 | 是否必填 |
|--------|------|--------|----------|
| CLIENT_ID | 钉钉应用 Client ID | 无 | ✅ 是 |
| CLIENT_SECRET | 钉钉应用 Client Secret | 无 | ✅ 是 |
| CURRENT_MODEL | OpenCode 模型 | opencode/minimax-m2.5-free | 否 |

### 环境变量

也可以通过环境变量配置：

| 变量名 | 说明 | 是否必填 |
|--------|------|----------|
| DINGTALK_CLIENT_ID | 钉钉应用 Client ID | ✅ 是 |
| DINGTALK_CLIENT_SECRET | 钉钉应用 Client Secret | ✅ 是 |
| OPENCODE_MODEL | OpenCode 模型 | 否 |
| OPENCODE_SERVER_PASSWORD | OpenCode 服务器密码 | 否 |

## 注意事项

1. 确保 OpenCode 服务器正在运行（端口 9090）
2. 钉钉应用需开启 Stream 模式
3. 需配置正确的 Client ID 和 Client Secret
4. 群聊中多个用户同时使用时，共享同一个 OpenCode 对话上下文
5. 重启机器人后，会自动加载上次的会话状态（需确保 `sessions.json` 和 `group_contexts.json` 文件存在）
6. 消息去重机制会忽略 10 分钟内重复的消息 ID，避免钉钉重试导致重复执行

## 技术实现

- 使用 WebSocket 长连接接收钉钉消息
- 调用钉钉 SDK 的 `SimpleReplyMarkdown` 方法发送富文本回复
- 通过 `opencode-cli.exe` 执行 OpenCode 任务
- 使用 JSON 流式输出格式，实时返回 AI 响应
- 支持消息去重（基于 `MsgId`），避免钉钉重试导致重复执行
- 异步任务处理，避免钉钉超时重试

## 开发

### 运行测试

```bash
go test -v
```

### 构建

```bash
go build -o dingtalk-agent.exe main.go
```

## GitHub 仓库

本技能的代码托管在 GitHub：https://github.com/yunloli/dingtalk-agent

### 如何贡献

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License