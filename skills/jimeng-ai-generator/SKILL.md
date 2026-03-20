---
name: jimeng-ai-generator
description: 通过浏览器插件接管原生 Edge/Chrome 窗口，批量执行即梦 AI（文生图、图生图、视频生成）任务的高级自动化技能。
---

# Jimeng AI Universal Generator (即梦 AI 全能生成)

一个通过浏览器插件接管原生 Edge/Chrome 窗口，批量执行即梦 AI（文生图、图生图、视频生成）任务的高级自动化技能。

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill jimeng-ai-generator
```

## ⚠️ 开发者红线 (Mandatory Rules)

1. **版本强制对齐**：**任何时候**修改 `assets/extension/` 下的插件代码，必须**同步递增**以下三个位置的版本号：
   - `manifest.json` 中的 `"version"`。
   - `content.js` 中的 `const VERSION` 变量。
   - `scripts/task_server.py` 中的 `VERSION` 变量。
   - **严禁**不更新版本直接交付，否则会导致 CORS 拦截失效、逻辑死循环或重复生成。
2. **跨标签页锁定**：必须维持插件内的 `localStorage` 锁定逻辑，确保多标签页环境下任务认领的唯一性。
3. **原子分发**：服务器下发任务必须采用弹出（Pop）模式，发出即删，严禁重复下发。

## 核心能力

- **环境免检**：基于原生浏览器插件运行，完全继承用户登录状态、真实硬件指纹，完美避开所有机器人检测。
- **CORS 权限通畅**：内置私有网络访问（Private Network Access）头处理，支持 HTTPS 网页直接调用本地回环接口。
- **全模式支持**：支持文生图、图生图（全自动上传）、文生视频、图生视频。
- **智能模型锁定**：自动识别并强制切换至“图片 4.0”或指定模型，杜绝误用昂贵的 Agent 模式。
- **资产监控判定**：不依赖不稳定的 UI 按钮文字，通过实时比对页面图片 URL 变更或 UI 状态复位判定生成结束。

## 使用流程

### 1. 安装与同步插件
1. 在浏览器（推荐 Edge）中打开扩展程序页面 `edge://extensions/`。
2. 开启“开发人员模式”，点击“加载解压缩的扩展”，选择本技能下的 `assets/extension` 目录。
3. **重要**：每当技能逻辑更新或提示版本不符时，必须在扩展页面点击 **“刷新”** 图标。

### 2. 准备资源 (图生图)
将需要作为素材的本地图片放入工作目录下的 `resources/` 文件夹。插件会自动通过本地静态服务器获取并模拟拖拽上传。

### 3. 启动任务服务器
由 AI 代理运行 `scripts/task_server.py`。该服务将监听 `18542` 端口，并管理任务队列。

### 4. 自动接管
刷新你的即梦 AI 页面（`https://jimeng.jianying.com/ai-tool/image/generate`）。
- 插件将自动检测环境。
- 获取任务 -> 切换模型 -> 自动填词 -> 模拟 Enter 提交 -> 监控结果 -> 反馈并认领下一单。

## 内部资源

- **插件目录**: `assets/extension/`
- **服务器脚本**: `scripts/task_server.py`
- **通信端口**: `18542` (Access-Control-Allow-Private-Network: true)
- **输出目录**: `outputs/`

## 文件结构

```
jimeng-ai-generator/
├── SKILL.md                    # 技能文档
├── README.md                   # 技能介绍
├── assets/
│   └── extension/
│       ├── manifest.json       # 插件配置
│       └── content.js          # 插件逻辑
├── scripts/
│   ├── task_server.py          # 任务服务器
│   ├── agent_jimeng.py         # 任务代理类
│   └── agent_jimeng_server.py  # 代理服务端
└── outputs/                    # 生成的图片输出目录
```
