# AI Skills

一个收集各种 AI 技能的仓库，包含多个独立的技能模块。遵循 [Agent Skills 规范](https://agentskills.io)，支持使用 `skills` CLI 进行标准化安装。

## 快速安装

### 安装 dingtalk-agent 技能

```bash
npx skills add ayflying/ai-skills --skill dingtalk-agent
```

### 安装所有技能

```bash
npx skills add ayflying/ai-skills
```

### 列出可用技能

```bash
npx skills add ayflying/ai-skills --list
```

## 技能列表

| 技能名称 | 描述 | 路径 |
|----------|------|------|
| [dingtalk-agent](skills/dingtalk-agent/README.md) | 钉钉机器人集成 OpenCode AI | `skills/dingtalk-agent/` |

## 详细安装说明

请查看 [SKILL_INSTALL.md](SKILL_INSTALL.md) 获取详细的安装步骤和配置指南。

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