# AGENTS.md - AI Skills 仓库开发指南

## 1. 项目概述

本仓库是 **AI Skills** 集合，包含多个独立的 AI 技能模块，遵循 [Agent Skills 规范](https://agentskills.io)。每个技能都是一个模块化的、自包含的包，旨在为 AI 代理提供专业领域知识、工作流和工具集成。

### 核心路径
- **主仓库**: `D:\git\ai-skills`
- **技能目录**: `skills/`
- **标准化安装文档**: `SKILL_INSTALL.md`

---

## 2. 技能结构规范 (Skill Anatomy)

每个技能目录必须严格遵循以下结构，严禁添加任何与 AI 任务执行无关的辅助文件（如 README.md, CHANGELOG.md 等）。

```
skills/skill-name/
├── SKILL.md (必填)
│   ├── YAML frontmatter (必需: name, description)
│   └── Markdown 指令 (必需: 核心工作流)
└── Bundled Resources (选填)
    ├── scripts/          - 可执行代码 (Python/Go/Bash 等)
    ├── references/       - 供 AI 代理按需加载的参考文档 (API 规格、架构说明)
    └── assets/           - 输出中使用的文件 (模板、图标、静态资源)
```

### 2.1 SKILL.md 规范
- **Frontmatter**: 必须包含 `name` 和 `description`。`description` 是触发技能的关键，必须描述“这是什么”以及“什么时候使用”。
- **精简原则**: `SKILL.md` 保持在 500 行以内。将复杂的细节（如 API 列表）移至 `references/` 目录。
- **渐进披露**: 在 `SKILL.md` 中引用 `references/` 中的文件，并说明在什么情况下需要阅读它们。

---

## 3. 构建、测试与运行命令

### 3.1 Go 技能 (如 dingtalk-agent)
**路径**: `skills/dingtalk-agent/scripts/` (推荐将源代码及测试移入 scripts)
- **依赖安装**: `go mod tidy`
- **运行测试**: `go test -v ./...`
- **编译运行**: `go run main.go`

### 3.2 Python 技能 (如 baota-panel)
**路径**: `skills/baota-panel/scripts/`
- **环境配置**: 配置 `.env` (基于 `.env.example`)
- **依赖安装**: `pip install requests urllib3`
- **运行脚本**: `python scripts/<name>.py`

---

## 4. 开发核心红线 (Mandatory Rules)

1. **禁止冗余文档**：技能目录下严禁出现 `README.md`。AI 代理所需的信息应全部在 `SKILL.md` 或 `references/` 中。
2. **安装说明要求**：必须在 `SKILL.md` 顶部的 YAML Frontmatter 下方包含标准安装命令。
3. **删除操作确认**：**所有涉及删除、清空或破坏性的操作**，必须在执行前明确告知用户并获得授权。
4. **安全第一**：严禁提交敏感信息，必须使用 `.env.example`。
5. **路径引用**：在 `SKILL.md` 中引用参考文件时，使用相对路径，例如 `See [api.md](references/api.md)`。

---

## 5. Git 工作流
... (保持不变) ...


### 5.1 提交规范

**提交信息格式**:
```
类型: 简短描述

详细描述（可选）
```

**类型**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

### 5.2 分支管理

- `main`: 主分支，稳定版本
- 功能分支: `feature/功能名称`
- 修复分支: `fix/问题描述`

---

## 6. 安全规范

### 6.1 敏感信息

**禁止**:
- 硬编码敏感信息 (如 Client ID, Secret)
- 提交 `.env` 文件到 Git
- 在日志中记录敏感信息

**必须**:
- 使用 `.env` 文件存储配置
- `.gitignore` 忽略 `.env`
- 使用环境变量作为备选方案

### 6.2 依赖安全

- 定期更新依赖 (`go get -u`)
- 检查已知漏洞 (`go vet`, `gosec`)

---

## 7. 开发工具

### 7.1 推荐工具

- **GoLand**: Go IDE
- **VS Code**: 配合 Go 扩展
- **Git**: 版本控制
- **GitHub CLI**: GitHub 操作

### 7.2 VS Code 配置

推荐安装扩展:
- Go (Microsoft)
- Go Nightly (可选)

---

## 8. 常见问题

### Q: 如何运行单个测试?
A: 使用 `go test -v -run TestFunctionName`

### Q: 如何更新依赖?
A: 使用 `go get -u ./...` 然后 `go mod tidy`

### Q: 如何检查代码格式?
A: 使用 `go fmt ./...` 和 `go vet ./...`

### Q: 如何添加新技能?
A: 
1. 在 `skills/` 目录创建新目录
2. 添加 `SKILL.md` (遵循 YAML frontmatter 格式)
3. 更新 `SKILL_INSTALL.md` 和 `README.md`
4. 提交到 GitHub
