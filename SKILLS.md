# AI Skills 技能列表

## 技能目录结构

```
ai-skills/
├── README.md              # 主仓库说明
├── SKILLS.md              # 技能列表（本文件）
├── .gitignore             # Git 忽略文件
└── skills/
    └── dingtalk-agent/    # 钉钉机器人技能
        ├── SKILL.md       # 技能核心文档
        └── scripts/       # Go 源代码与编译
    └── opencode-api/      # OpenCode API 技能
        ├── SKILL.md       # 技能核心文档
        └── scripts/       # Python 脚本
    └── baota-panel/       # 宝塔面板管理技能
        ├── SKILL.md       # 技能核心文档
        ├── docs/          # 模块化技术文档
        └── scripts/       # API 脚本
    └── casdoor-integration/ # Casdoor SSO 集成指南
        ├── SKILL.md       # 技能核心文档
        └── references/    # 集成指南资源
    └── wechat-bot/        # 微信机器人技能
        ├── SKILL.md       # 技能核心文档
        ├── scripts/       # Python 脚本
        └── .env.example   # 配置模板
```

## 技能详情

### dingtalk-agent

**描述**: 钉钉机器人集成 OpenCode AI

**功能**:
- 钉钉群聊机器人集成
- 通过 `@机器人` 发送任务消息
- OpenCode AI 执行任务并将结果推回钉钉群
- 群聊共享上下文和用户独立模式开关

**使用方式**:
详见 `skills/dingtalk-agent/SKILL.md`

### opencode-api

**描述**: 连接 OpenCode 服务器执行 AI 任务

**功能**:
- 连接到运行中的 OpenCode 服务器
- 执行 AI 驱动的任务指令
- 返回执行结果（支持 JSON 格式）

**使用方式**:
详见 `skills/opencode-api/SKILL.md`

### baota-panel

**描述**: 通过宝塔面板 API 管理服务器资源

**功能**:
- 网站管理、Docker 监控、数据库运维
- 远程文件系统读写、压缩与回收站
- 系统资源状态检查与安全管理

**使用方式**:
详见 `skills/baota-panel/SKILL.md`

### casdoor-integration

**描述**: 通用的 Casdoor SSO/IAM 集成指南

**功能**:
- OAuth2/OIDC 认证逻辑与 Session 稳定性处理
- 内置系统兼容性与账户关联规范
- 组织架构绑定与权限角色映射
- 前端构建陷阱与环境变量注入方案

**使用方式**:
详见 `skills/casdoor-integration/README.md`

### wechat-bot

**描述**: 微信机器人技能，基于wxpy实现个人微信自动化

**功能**:
- 消息收发（文本、图片、语音、视频、文件）
- 自动回复配置
- 媒体文件自动保存
- 消息数据收集和统计
- 内置命令支持（help、status、stats、export）

**使用方式**:
详见 `skills/wechat-bot/SKILL.md`

## 如何添加新技能

1. 在 `skills/` 目录下创建新的技能目录
2. 添加技能代码和文档
3. 更新本文件（SKILLS.md）
4. 提交 Pull Request

## 许可证

MIT License