# AGENTS.md - AI Skills 仓库开发指南

## 1. 项目概述

本仓库是 **AI Skills** 集合，包含多个独立的 AI 技能模块，遵循 [Agent Skills 规范](https://agentskills.io)。

### 核心路径
- **主仓库**: `D:\git\ai-skills`
- **技能目录**: `skills/`
  - `dingtalk-agent`: 钉钉机器人集成 OpenCode AI
- **文档**: `SKILL_INSTALL.md` (标准化安装说明)

---

## 2. 构建、测试与代码检查命令

### 2.1 DingTalk Agent 技能 (Go 项目)

**前提条件**:
- Go 1.24.1+
- 配置 `.env` 文件 (基于 `.env.example`)

**构建与运行**:
```bash
# 进入技能目录
cd skills/dingtalk-agent

# 安装依赖
go mod tidy

# 构建可执行文件
go build -o dingtalk-agent.exe main.go

# 运行程序
./dingtalk-agent.exe
```

**测试命令**:
```bash
# 运行所有测试
cd skills/dingtalk-agent
go test -v

# 运行单个测试 (例如 TestParseCommand)
go test -v -run TestParseCommand

# 运行特定测试用例
go test -v -run "TestParseCommand|TestOnChatBotMessageReceived"
```

**代码质量检查**:
```bash
# 格式化代码
go fmt ./...

# 检查代码风格
go vet ./...
```

### 2.2 标准化技能安装

**使用 skills CLI**:
```bash
# 安装所有技能
npx skills add ayflying/ai-skills

# 安装特定技能
npx skills add ayflying/ai-skills --skill dingtalk-agent

# 列出可用技能
npx skills add ayflying/ai-skills --list
```

---

## 3. 代码风格指南

### 3.1 Go 语言规范 (DingTalk Agent)

**命名规范**:
- **包名**: 全小写 (`main`)
- **函数名**: PascalCase (导出) 或 camelCase (未导出)
- **变量名**: camelCase
- **常量**: SCREAMING_SNAKE_CASE (导出) 或 camelCase (未导出)
- **结构体**: PascalCase

**示例**:
```go
// 包名
package main

// 导出结构体 (PascalCase)
type UserSession struct {
    IsInOpenCodeMode bool      `json:"is_in_opencode_mode"`
    LastActiveTime   time.Time `json:"last_active_time"`
}

// 未导出变量 (camelCase)
var userSessions map[string]*UserSession

// 导出函数 (PascalCase)
func LoadConfig() {}

// 未导出函数 (camelCase)
func loadConfig() {}
```

**类型提示**:
- Go 是静态类型语言，必须显式声明类型
- 使用具体类型而非 `interface{}` 除非必要
- 结构体字段使用 `json` 标签进行序列化

**错误处理**:
- 必须检查所有错误返回值
- 使用 `if err != nil` 模式
- 错误信息使用英文，日志可以使用中文

```go
file, err := os.Open(envFile)
if err != nil {
    fmt.Printf("警告: 无法打开 %s 文件: %v\n", envFile, err)
    return
}
defer file.Close()
```

**导入规范**:
- 标准库在前，第三方库在后
- 使用分组导入，标准库和第三方库分开
- 按字母顺序排序

```go
import (
    "bufio"
    "context"
    "encoding/json"
    "fmt"
    "os"
    "os/exec"
    "regexp"
    "strings"
    "sync"
    "time"

    "github.com/open-dingtalk/dingtalk-stream-sdk-go/chatbot"
    "github.com/open-dingtalk/dingtalk-stream-sdk-go/client"
    "github.com/open-dingtalk/dingtalk-stream-sdk-go/logger"
)
```

**格式化**:
- 使用 `go fmt` 自动格式化
- 缩进使用 Tab
- 行长度不超过 120 字符

**注释**:
- 导出函数/类型必须有注释
- 注释以函数名开头
- 使用英文注释

```go
// LoadConfig loads configuration from .env file and environment variables
func LoadConfig() {
    // Implementation
}
```

### 3.2 配置管理

**环境变量**:
- 使用 `.env` 文件存储敏感配置
- `.env.example` 作为模板
- `.gitignore` 忽略 `.env` 文件

**配置变量**:
- 配置变量使用大写 (`CLIENT_ID`, `CLIENT_SECRET`)
- 提供默认值
- 支持环境变量覆盖

```go
var (
    ClientID     string
    ClientSecret string
    CurrentModel string
)
```

### 3.3 测试规范

**测试文件**:
- 文件名: `*_test.go`
- 包名: 与被测试包相同 (`package main`)

**测试函数**:
- 函数名: `TestXxx`
- 参数: `*testing.T`
- 使用 `t.Errorf` 报告错误

```go
func TestParseCommand(t *testing.T) {
    testCases := []struct {
        input    string
        expected string
    }{
        {"  /help  ", "/help"},
    }

    for _, tc := range testCases {
        // 测试逻辑
        if result != tc.expected {
            t.Errorf("输入 '%s': 期望 '%s', 得到 '%s'", tc.input, tc.expected, result)
        }
    }
}
```

**测试最佳实践**:
- 使用表驱动测试 (Table-Driven Tests)
- 测试覆盖边界情况
- 测试文件操作时使用临时文件
- 清理测试产生的文件

### 3.4 错误处理规范

**基本原则**:
1. 检查所有错误返回值
2. 不忽略错误 (`_`)
3. 提供有意义的错误信息
4. 在适当层级处理错误

**错误模式**:
```go
// 1. 简单错误检查
if err != nil {
    return fmt.Errorf("操作失败: %w", err)
}

// 2. 多步操作错误处理
result, err := operation1()
if err != nil {
    return fmt.Errorf("operation1 failed: %w", err)
}

result2, err := operation2(result)
if err != nil {
    return fmt.Errorf("operation2 failed: %w", err)
}

// 3. 资源清理 (使用 defer)
file, err := os.Open(filename)
if err != nil {
    return err
}
defer file.Close()
```

### 3.5 并发处理

**使用 Go 原生并发**:
- 使用 `sync.Mutex` 保护共享数据
- 使用 `sync.RWMutex` 读多写少场景
- 使用 `sync.Map` 高并发场景

```go
var (
    userSessions   = make(map[string]*UserSession)
    userSessionsMu sync.RWMutex
)

// 读操作
userSessionsMu.RLock()
session := userSessions[userID]
userSessionsMu.RUnlock()

// 写操作
userSessionsMu.Lock()
userSessions[userID] = session
userSessionsMu.Unlock()
```

---

## 4. 项目结构规范

### 4.1 目录结构

```
ai-skills/
├── SKILL_INSTALL.md       # 标准化安装说明
├── README.md              # 主仓库说明
├── LICENSE                # MIT 开源协议
├── SECURITY.md            # 安全说明
├── SKILLS.md              # 技能列表
├── .gitignore             # Git 忽略文件
└── skills/
    └── dingtalk-agent/
        ├── main.go        # Go 主程序
        ├── main_test.go   # 单元测试
        ├── go.mod         # Go 模块定义
        ├── go.sum         # Go 依赖锁定
        ├── SKILL.md       # 技能文档 (标准化格式)
        ├── README.md      # 技能说明
        ├── .env.example   # 环境变量模板
        ├── .env           # 环境变量 (被忽略)
        └── evals/         # 评估目录
```

### 4.2 文件命名

- **Go 文件**: `lowercase_with_underscores.go` (如 `main.go`, `utils.go`)
- **测试文件**: `*_test.go` (如 `main_test.go`)
- **配置文件**: `.env`, `.env.example`, `.gitignore`
- **文档文件**: `UPPERCASE.md` (如 `README.md`, `SKILL.md`)

### 4.3 SKILL.md 规范

**必须包含 YAML frontmatter**:
```yaml
---
name: skill-name
description: 技能描述
---
```

**可选字段**:
- `allowed_tools`: 允许使用的工具列表
- `metadata`: 元数据信息

---

## 5. Git 工作流

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

**示例**:
```
feat: 支持从 .env 文件读取配置

- 添加 loadConfig() 函数
- 创建 .env.example 模板
- 更新文档说明
```

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