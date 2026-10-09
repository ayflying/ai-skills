# AI Skills

我编写的 AI 技能集合仓库，包含多个独立的技能模块。遵循 [Agent Skills 规范](https://agentskills.io)，支持使用 `skills` CLI 进行标准化安装。

## 技能列表

当前包含 **12 个独立技能**，以 Python 脚本、参考文档和浏览器资源为主，不存在统一的应用启动入口。点击技能名称查看详细说明和安装方法：

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
| [teambition-bug](skills/teambition-bug/SKILL.md) | 通过 Teambition 官方 OpenAPI 读取、留言、识别截图、推进状态并审计看板字段 | `skills/teambition-bug/` |
| [image-recognition](skills/image-recognition/SKILL.md) | 全局优先用于读图/OCR/截图理解，调用 OpenAI 兼容视觉模型只返回精简中文描述以节省 token | `skills/image-recognition/` |
| [website-function-mapper](skills/website-function-mapper/SKILL.md) | 用 Playwright 安全侦察网站功能、动态表单、接口线索和文档说明，输出复刻规格 | `skills/website-function-mapper/` |

## 使用方式

```bash
# 查看可用技能
npx skills add ayflying/ai-skills --list
# 安装指定技能
npx skills add ayflying/ai-skills --skill opencode-api
# 安装全部技能
npx skills add ayflying/ai-skills
```

安装后按各技能说明准备依赖、配置及外部服务；安装技能不等于已配置运行环境。完整流程见 [安装说明](SKILL_INSTALL.md)。

## 开发说明

- [技能清单](SKILLS.md)：目录结构与能力说明。
- [开发指南](AGENTS.md)：代码、测试、技能格式及文档同步规则。
- [安全说明](SECURITY.md)：凭证、登录态和高风险操作要求。

## 许可证

MIT License
