# OpenCode API

连接到运行中的 OpenCode 服务器执行 AI 任务（代码执行、任务分析、内容生成）。

## 功能特性

- **跨平台连接**：支持连接到本地或远程 OpenCode 服务器。
- **任务执行**：通过 Python 脚本直接发送 AI 任务。
- **结构化输出**：支持 JSON 格式返回执行结果。
- **会话管理**：支持通过 Session ID 继续对话。

## 安装

### 标准化安装（推荐）

使用 `skills` CLI 安装：

```bash
npx skills add ayflying/ai-skills --skill opencode-api
```

### 手动安装

#### 前置要求

- Python 3.10+
- 正在运行的 OpenCode 服务器 (默认端口 9091)

#### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/ayflying/ai-skills.git
   cd ai-skills/skills/opencode-api
   ```

2. **配置环境**
   复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```
   并填写 `OPENCODE_SERVER_PASSWORD`。

## 使用方式

在项目目录下运行：

```bash
python scripts/opencode_runner.py "请帮我写一个快速排序算法"
```

### 常用参数

| 参数 | 说明 |
|------|------|
| `任务描述` | 必需。要执行的 AI 指令。 |
| `--json` | 以 JSON 格式输出结果。 |
| `--session` | 指定会话 ID。 |
| `--model` | 指定使用的模型。 |

## 配置说明

支持通过 `.env` 或环境变量进行配置：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENCODE_SERVER_URL` | 服务器地址 | `http://127.0.0.1:9091` |
| `OPENCODE_MODEL` | AI 模型 | `opencode/mimo-v2-omni-free` |
| `OPENCODE_SERVER_PASSWORD` | 服务器密码 | (必填) |

## 许可证

MIT License
