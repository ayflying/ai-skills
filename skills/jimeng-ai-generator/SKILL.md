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

## 准备工作 (Prerequisites)

1. **安装后端依赖**：
   ```bash
   pip install -r requirements.txt
   ```
2. **加载浏览器插件**：
   - 打开浏览器扩展管理页面 (`edge://extensions/` 或 `chrome://extensions/`)。
   - 开启 **开发者模式**。
   - 点击 **加载解压缩的扩展程序**，选择 `skills/jimeng-ai-generator/assets/extension` 目录。

## ⚠️ 开发者红线 (Mandatory Rules)

1. **版本强制对齐**：修改 `assets/extension/` 下的代码后，必须同步更新 `manifest.json`、`content.js` 和 `scripts/task_server.py` 中的版本号。
2. **原子分发**：任务下发必须发出即删，严禁重复生成。

## 核心能力

- **环境免检**：完全继承真实用户 Session 和硬件指纹，完美避开 AI 检测。
- **CORS 通畅**：内置 PNA 协议头处理，支持 HTTPS 页面调用本地服务。
- **全自动循环**：从获取任务、切换模型、上传素材到监控结果，全流程闭环。

## 使用流程

### 1. 准备素材 (针对图生图)
将素材图片放入 `resources/` 目录。

### 2. 启动任务服务器
```bash
python scripts/task_server.py
```
服务器默认监听 `18542` 端口。

### 3. 开启即梦 AI 页面
访问 [即梦 AI 生成页](https://jimeng.jianying.com/ai-tool/image/generate)。插件会自动识别并开始认领任务。

## 文件结构

```
jimeng-ai-generator/
├── SKILL.md                    # 核心文档
├── requirements.txt            # Python 依赖
├── assets/
│   └── extension/              # 浏览器插件源码
├── scripts/
│   ├── task_server.py          # 任务分发服务端
│   └── agent_jimeng.py         # 任务处理逻辑
└── outputs/                    # 结果输出目录
```
