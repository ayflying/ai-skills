# AI Skills

一个收集各种 AI 技能的仓库，包含多个独立的技能模块。遵循 [Agent Skills 规范](https://agentskills.io)，支持使用 `skills` CLI 进行标准化安装。

## 技能列表

| 技能名称 | 描述 | 路径 |
|----------|------|------|
| [dingtalk-agent](skills/dingtalk-agent/README.md) | 钉钉机器人集成 OpenCode AI | `skills/dingtalk-agent/` |

## 标准化安装

使用 `skills` CLI 安装技能：

```bash
# 安装所有技能
npx skills add ayflying/ai-skills

# 安装特定技能
npx skills add ayflying/ai-skills --skill dingtalk-agent

# 列出可用技能
npx skills add ayflying/ai-skills --list
```

详细说明请查看 [SKILL_INSTALL.md](SKILL_INSTALL.md)

## 使用方式

每个技能都是独立的，可以单独使用。请查看每个技能目录下的 `README.md` 了解详细使用方法。

## 贡献

欢迎提交新的技能！请遵循以下步骤：

1. Fork 本仓库
2. 在 `skills/` 目录下创建新的技能目录
3. 添加 `SKILL.md` 文件（遵循 YAML frontmatter 格式）
4. 添加技能代码和文档
5. 提交 Pull Request

详细开发说明请查看 [SKILL_INSTALL.md](SKILL_INSTALL.md)

## 许可证

MIT License