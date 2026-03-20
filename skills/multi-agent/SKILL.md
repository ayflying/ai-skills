---
name: multi-agent
description: |
  OpenCode 多代理并行协作配置。支持多个代理同时工作，实现流水线开发模式。
  Use when: (1) 需要多个代理并行工作，如开发写完一个功能后测试立即开始，开发继续下一个功能
  (2) 需要 master 调度 build、test-writer、code-reviewer 等代理协同工作
  (3) 需要实现开发+测试+审查的流水线模式
  (4) 需要配置 OpenCode 的多代理协作能力
---

# 多代理并行协作

## 安装与初始化

1. **安装技能**：
   ```bash
   npx skills add ayflying/ai-skills --skill multi-agent
   ```

2. **初始化 IDE 代理（首次或更新时执行）**：
   运行初始化脚本，将代理配置部署到项目根目录，以便 OpenCode 识别：
   ```bash
   python skills/multi-agent/scripts/setup.py
   ```

## 协作规范

**身份标识（Mandatory）**：所有代理在输出时必须首先声明其身份。格式为：`[身份名] 消息内容`。

示例：`[Master] 正在分配任务...`
示例：`[Lead Programmer] 架构设计已完成...`

## 代理列表

| 代理 | 职责 |
|------|------|
| master | **总调度**：负责多代理并行协作的整体控制与任务拆解 |
| lead-programmer | **主程**：架构设计、任务分配、解决代码冲突、技术栈决策 |
| planner | **策划**：系统详细设计、逻辑文档、配置文件管理（.env, config） |
| artist | **美术**：UI/UX 设计、视觉规范、CSS/样式实现、动效建议 |
| build | 编写和修改功能代码（受主程分配） |
| plan | 分析需求和初步技术设计方案 |
| test-writer | 编写测试用例并执行测试 |
| code-reviewer | 代码审查 |
| security-auditor | 安全审计 |
| docs-writer | 编写技术文档 |
| performance-optimizer | 性能优化 |


## 使用

启动 OpenCode 后按 Tab 选择 master，然后描述任务：

```
帮我实现用户模块，build 写完一个功能后 test-writer 立即测试，同时 build 继续下一个功能
```

## 并行调度规则

master 根据任务类型调度代理：

| 任务类型 | 调用代理 |
|---------|---------|
| 代码实现 | @build |
| 架构与任务分配 | @lead-programmer |
| 系统设计与配置 | @planner |
| UI/UX 设计 | @artist |
| 方案设计 | @plan |
| 代码审查 | @code-reviewer |
| 安全检查 | @security-auditor |
| 编写测试 | @test-writer |
| 编写文档 | @docs-writer |
| 性能优化 | @performance-optimizer |
