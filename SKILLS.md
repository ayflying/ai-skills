# AI Skills 技能列表

## 技能目录结构

```
ai-skills/
├── README.md              # 主仓库说明
├── SKILLS.md              # 技能列表（本文件）
├── .gitignore             # Git 忽略文件
└── skills/
    └── dingtalk-agent/    # 钉钉机器人技能
        ├── README.md      # 技能说明
        ├── SKILL.md       # 技能文档
        ├── main.go        # Go 主程序
        ├── main_test.go   # 单元测试
        ├── go.mod         # Go 模块定义
        └── go.sum         # Go 依赖锁定
```

## 技能详情

### dingtalk-agent

**描述**: 钉钉机器人集成 OpenCode AI

**功能**:
- 钉钉群聊机器人集成
- 通过 `@机器人` 发送任务消息
- OpenCode AI 执行任务并将结果推回钉钉群
- 群聊共享上下文和用户独立模式开关
- 适合团队协作开发

**使用方式**:
```bash
cd skills/dingtalk-agent
go mod tidy
go build -o dingtalk-agent.exe main.go
./dingtalk-agent.exe
```

**详细说明**: 查看 `skills/dingtalk-agent/README.md`

## 如何添加新技能

1. 在 `skills/` 目录下创建新的技能目录
2. 添加技能代码和文档
3. 更新本文件（SKILLS.md）
4. 提交 Pull Request

## 许可证

MIT License