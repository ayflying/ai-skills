# 技能标准化安装说明

## 概述

这是我编写的 AI 技能集合仓库，遵循 [Agent Skills 规范](https://agentskills.io)，支持使用 `skills` CLI 进行标准化安装。

## 快速开始

### 1. 安装 skills CLI

如果你还没有安装 `skills` CLI，首先安装它：

```bash
npm install -g skills-cli
# 或者使用 npx（无需安装）
```

### 2. 安装技能

#### 安装所有技能
```bash
npx skills add ayflying/ai-skills
```

#### 安装特定技能（推荐）
```bash
npx skills add ayflying/ai-skills --skill dingtalk-agent
```

#### 列出可用技能
```bash
npx skills add ayflying/ai-skills --list
```

### 3. 支持的 Agent

- OpenCode
- Claude Code
- Cursor
- 以及其他 39+ 个 Agent

## dingtalk-agent 技能详细安装指南

### 前置要求

1. **Go 1.24.1+** - 用于运行 Go 程序
2. **钉钉企业应用** - 需要开启 Stream 模式
3. **OpenCode 服务器** - 运行在端口 9090

### 安装步骤

#### 步骤 1: 安装技能
```bash
npx skills add ayflying/ai-skills --skill dingtalk-agent
```

#### 步骤 2: 配置环境变量
技能安装后，会创建 `skills/dingtalk-agent/.env.example` 文件。复制并配置：

```bash
cd skills/dingtalk-agent
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

#### 步骤 3: 获取钉钉配置
1. 登录 [钉钉开放平台](https://open.dingtalk.com)
2. 进入"应用开发" → "企业内部应用"
3. 创建或选择你的应用
4. 在"应用信息"中查看 `Client ID` 和 `Client Secret`
5. 在"权限管理"中开通"Stream模式"

#### 步骤 4: 安装依赖并运行
```bash
# 安装 Go 依赖
go mod tidy

# 构建程序
go build -o dingtalk-agent.exe main.go

# 运行程序
./dingtalk-agent.exe
```

### 使用方式

安装并配置完成后，在钉钉群中发送以下命令：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/status` | 查看当前模式和状态 |
| `/opencode <任务>` | 进入 OpenCode 模式并执行任务 |
| `/exit` | 退出 OpenCode 模式 |

## 技能结构

每个技能必须包含 `SKILL.md` 文件，格式如下：

```yaml
---
name: skill-name
description: 技能描述
---

# 技能内容...

## 使用说明
...
```

## 当前技能

| 技能名称 | 描述 | 路径 |
|----------|------|------|
| dingtalk-agent | 钉钉机器人集成 OpenCode AI | `skills/dingtalk-agent/` |

## 开发新技能

1. 在 `skills/` 目录下创建新技能目录
2. 添加 `SKILL.md` 文件（遵循 YAML frontmatter 格式）
3. 更新 `SKILL_INSTALL.md` 中的技能列表
4. 提交到 GitHub

## 故障排除

### "No skills found" 错误
- 确保仓库中包含有效的 `SKILL.md` 文件
- 检查 `SKILL.md` 是否包含 `name` 和 `description` 字段

### 技能未加载
- 验证技能已安装到正确路径
- 检查 Agent 的文档了解技能加载要求

### 权限错误
- 确保有写入目标目录的权限

## 参考资料

- [Agent Skills 规范](https://agentskills.io)
- [Skills CLI 文档](https://skills.sh)
- [Vercel Labs Skills 仓库](https://github.com/vercel-labs/skills)