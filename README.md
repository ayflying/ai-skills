# AI Skills

我编写的 AI 技能集合仓库，包含多个独立的技能模块。遵循 [Agent Skills 规范](https://agentskills.io)，支持使用 `skills` CLI 进行标准化安装。

## 技能列表

点击技能名称查看详细说明和安装方法：

| 技能名称 | 描述 | 路径 |
|----------|------|------|
| [opencode-api](skills/opencode-api/SKILL.md) | 连接 OpenCode 服务器执行 AI 任务 | `skills/opencode-api/` |
| [minimax-api](skills/minimax-api/SKILL.md) | MiniMax 多模态 AI API 集成 | `skills/minimax-api/` |
| [baota-panel](skills/baota-panel/SKILL.md) | 通过宝塔面板 API 管理服务器资源 | `skills/baota-panel/` |
| [casdoor-integration](skills/casdoor-integration/SKILL.md) | 通用的 Casdoor SSO/IAM 集成指南 | `skills/casdoor-integration/` |
| [wechat-bot](skills/wechat-bot/SKILL.md) | 微信机器人，基于wxpy实现个人微信自动化 | `skills/wechat-bot/` |
| [jimeng-ai-generator](skills/jimeng-ai-generator/SKILL.md) | 即梦 AI 批量生成任务自动化 | `skills/jimeng-ai-generator/` |
| [gpt-image](skills/gpt-image/SKILL.md) | OpenAI GPT Image 系列画图与图片编辑 | `skills/gpt-image/` |
| [ollama](skills/ollama/SKILL.md) | 调用 Ollama 本地模型 (qwen3.5:9b) | `skills/ollama/` |
| [gitea-weekly-report](skills/gitea-weekly-report/SKILL.md) | 生成一个或多个 Gitea 组织的周报，遍历全部分支并转换技术提交为业务功能点 | `skills/gitea-weekly-report/` |
| [teambition-bug](skills/teambition-bug/SKILL.md) | 通过 Teambition 官方 OpenAPI 读取、留言、识别截图并推进 bug 到修改中/待验收 | `skills/teambition-bug/` |

## 使用方式

每个技能都是独立的，可以单独使用。请点击上方技能名称查看详细的安装和使用说明。

## 开发说明

本仓库包含我编写的所有 AI 技能。详细开发说明请查看 [SKILL_INSTALL.md](SKILL_INSTALL.md)

## 许可证

MIT License
