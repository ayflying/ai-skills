# 技能标准化安装说明

## 1. 概述

本仓库是遵循 [Agent Skills 规范](https://agentskills.io)的独立技能集合。技能安装用于让支持该规范的 Agent 加载任务说明和资源，不等于已安装 Python 依赖、配置账号或启动外部服务。

## 2. 安装技能

需要本机可运行 Node.js、npm 和 `npx`。使用 `npx skills` 即可，无需预先全局安装 CLI。

```bash
# 列出仓库可用技能
npx skills add ayflying/ai-skills --list

# 安装一个技能
npx skills add ayflying/ai-skills --skill opencode-api

# 安装全部技能
npx skills add ayflying/ai-skills
```

按 CLI 提示选择目标 Agent 和安装范围。OpenCode、Claude Code、Cursor 等工具的支持情况及加载路径以当前 [Skills CLI 文档](https://skills.sh)和目标 Agent 文档为准。

## 3. 当前技能

以下 12 个技能均以各自 `SKILL.md` 为安装和使用入口：

| 技能 | 用途 |
|------|------|
| [opencode-api](skills/opencode-api/SKILL.md) | 连接 OpenCode 服务器执行 AI 任务 |
| [minimax-api](skills/minimax-api/SKILL.md) | MiniMax 文本、语音、图像、视频与音乐 API |
| [baota-panel](skills/baota-panel/SKILL.md) | 宝塔面板资源管理 |
| [casdoor-integration](skills/casdoor-integration/SKILL.md) | Casdoor 单点登录与权限集成 |
| [wechat-bot](skills/wechat-bot/SKILL.md) | 微信个人机器人 |
| [jimeng-ai-generator](skills/jimeng-ai-generator/SKILL.md) | 即梦批量生成任务自动化 |
| [gpt-image](skills/gpt-image/SKILL.md) | GPT Image 图片生成与编辑 |
| [ollama](skills/ollama/SKILL.md) | Ollama 本地模型调用 |
| [gitea-weekly-report](skills/gitea-weekly-report/SKILL.md) | Gitea 项目工作周报 |
| [teambition-bug](skills/teambition-bug/SKILL.md) | Teambition 缺陷查询与处理 |
| [image-recognition](skills/image-recognition/SKILL.md) | 图片识别、OCR 与截图理解 |
| [website-function-mapper](skills/website-function-mapper/SKILL.md) | 网站功能侦察与复刻验收 |

详细能力和目录说明见 [SKILLS.md](SKILLS.md)。技能增减时同步维护本表与 [README.md](README.md)。

## 4. 安装后的准备

先读取所选技能的 `SKILL.md`，再按其要求准备运行环境。各技能独立，不存在适用于全部技能的统一启动命令。

### Python 依赖

Python 技能通常要求 Python 3.10+，具体要求以技能说明为准。有 `requirements.txt` 的技能，在对应目录运行：

```bash
python -m pip install -r requirements.txt
```

没有依赖清单时按技能说明安装，不能假定 `requests` 足以运行所有技能。浏览器类技能还可能需要扩展、Playwright 或浏览器安装步骤。

### 配置与服务

- 仅在提供 `.env.example` 且技能说明要求时复制为 `.env`，填入本机配置。
- `image-recognition` 使用系统环境变量，不统一改成 `.env`。
- OpenCode、Ollama、宝塔等技能需准备对应的服务地址和授权。
- 仅文档型技能不一定需要执行脚本。
- 不把凭证、浏览器登录态或真实业务数据写入可提交的模板，详见 [SECURITY.md](SECURITY.md)。

## 5. 开发新技能

```text
skills/<skill-name>/
├── SKILL.md          # 必须：触发条件、执行规则与安装说明
├── README.md         # 可选：已有则同步维护
├── scripts/          # 可选：脚本与测试
├── references/       # 可选：参考资料
└── assets/           # 可选：模板和资源
```

SKILL 必须有 YAML frontmatter：

```yaml
---
name: skill-name
description: |
  描述技能做什么。
  Use when: (1) 触发条件一 (2) 触发条件二
---
```

正文写明实际技能名对应的安装命令：

```bash
npx skills add ayflying/ai-skills --skill <skill-name>
```

开发后同步仓库清单，核对链接、命令和测试。完整规范见 [AGENTS.md](AGENTS.md)。

## 6. 故障排除

### 找不到技能

- 检查 `skills/<skill-name>/SKILL.md` 是否存在。
- 检查 frontmatter 的 `name`、`description` 和技能名。
- 用 `--list` 核对可用名称，不使用不存在的历史技能名。

### 已安装但未加载

- 检查 CLI 所选 Agent 和安装范围。
- 根据目标 Agent 文档确认技能加载路径和是否需要重启会话。
- 安装成功不代表依赖和外部服务已经配置完成。

### 脚本运行失败

- 核对 Python 版本、依赖、参数、环境变量及服务连通性。
- 权限错误时确认目标目录和账号权限，不盲目提升权限。
- 分享报错前移除 Token、密码、登录态和私人业务数据。

## 7. 参考资料

- [Agent Skills 规范](https://agentskills.io)
- [Skills CLI 文档](https://skills.sh)
- [Vercel Labs Skills 仓库](https://github.com/vercel-labs/skills)
