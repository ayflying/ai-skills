---
name: multi-agent
description: |
  OpenCode 多代理并行协作配置。支持多个代理同时工作，实现流水线开发模式。
  Use when: (1) 需要多个代理并行工作 (2) 需要 master 调度各代理协同工作
  (3) 需要实现设计→开发→验收→测试的规范化流程 (4) 需要配置 OpenCode 的多代理协作能力
---

# 多代理并行协作

## 安装与初始化

1. **安装技能**：
   ```bash
   npx skills add ayflying/ai-skills --skill multi-agent
   ```

2. **初始化 IDE 代理（首次或更新时执行）**：
   ```bash
   python .agents/skills/multi-agent/scripts/setup.py
   ```

## 自定义代理名称

安装后会在项目根目录生成 `.env` 文件。编辑 `_NAME` 变量自定义名称，重新运行 setup.py 使配置生效。

## 核心原则

**任务分配权唯一**：只有 ${MASTER_NAME} 能分配任务，其他代理不能私自接受或分配任务。

## 职责分层

| 角色 | 职责 | 任务来源 |
|------|------|---------|
| ${MASTER_NAME} | 唯一任务分配者 | 用户指令 |
| ${PLANNER_NAME} | 功能设计 + 功能验收 | 接收 ${MASTER_NAME} 分配 |
| ${LEAD_PROGRAMMER_NAME} | 架构设计 + 程序分配（唯一） | 只能接收 ${MASTER_NAME} 分配 |
| ${ARTIST_NAME} | UI/UX设计 | 接收 ${MASTER_NAME} 分配 |
| @build | 代码实现（可多个并发） | 只能接收 ${LEAD_PROGRAMMER_NAME} 分配 |
| @test-writer | 功能测试 | 接收 ${MASTER_NAME} 分配 |

## 标准工作流程

```
用户需求
    ↓
[MASTER] 判断需求是否明确
    ↓
┌─ 需求不明确 → [PLANNER] 功能设计 → 交回 [MASTER] 分配
│
└─ 需求明确 → [MASTER] 任务分配
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
   [LEAD-PROGRAMMER] [ARTIST]     ...
        ↓             
   分配给多个@build并发开发
        ↓
   汇总完成结果
        ↓
[MASTER] → [PLANNER] 功能验收
        ↓ 不满意
    交回 [MASTER] 重新分配
        ↓ 通过
[MASTER] → [TEST-WRITER] 功能测试
        ↓
    汇总向用户反馈
```

## Bug处理流程

```
发现Bug → [MASTER]判断问题根源
              ↓
    ┌─ 设计问题 → [PLANNER] 重新设计
    │
    └─ 程序问题 → [LEAD-PROGRAMMER] 修复
```

## 禁止行为

- 任何代理不能私自接受或分配任务
- 程序任务禁止跳过 [LEAD-PROGRAMMER] 直接分配给 @build
- 禁止跳过 [PLANNER] 验收直接测试
- [LEAD-PROGRAMMER] 只能有一个

## 代理列表

| 代理 | 默认名称 | 职责 |
|------|---------|------|
| master | 总调度 | 唯一任务分配者，不执行具体工作 |
| lead-programmer | 主程 | 程序任务唯一入口，可分配给多个@build并发 |
| planner | 策划 | 功能设计+验收，不能分配任务 |
| artist | 美术 | UI/UX设计 |
| build | 构建 | 代码实现（可多个并发） |
| test-writer | 测试 | 功能测试 |
| code-reviewer | 审查 | 代码审查 |
| security-auditor | 安全 | 安全审计 |
| docs-writer | 文档 | 编写技术文档 |
| performance-optimizer | 性能 | 性能优化 |
