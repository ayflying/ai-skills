# 技能标准化安装说明

## 概述

本仓库遵循 [Agent Skills 规范](https://agentskills.io)，支持使用 `skills` CLI 进行标准化安装。

## 安装方式

### 1. 使用 skills CLI 安装

```bash
# 安装所有技能
npx skills add ayflying/ai-skills

# 安装特定技能
npx skills add ayflying/ai-skills --skill dingtalk-agent

# 列出可用技能
npx skills add ayflying/ai-skills --list
```

### 2. 支持的 Agent

- OpenCode
- Claude Code
- Cursor
- 以及其他 39+ 个 Agent

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

## 参考资料

- [Agent Skills 规范](https://agentskills.io)
- [Skills CLI 文档](https://skills.sh)
- [Vercel Labs Skills 仓库](https://github.com/vercel-labs/skills)