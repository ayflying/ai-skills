# Jimeng AI Universal Generator (即梦 AI 全能生成)

通过浏览器插件接管原生 Edge/Chrome 窗口，批量执行即梦 AI（文生图、图生图、视频生成）任务的高级自动化技能。

## 快速开始

### 1. 安装技能
```bash
npx skills add ayflying/ai-skills --skill jimeng-ai-generator
```

### 2. 加载浏览器插件
1. 进入 `edge://extensions/` (Edge) 或 `chrome://extensions/` (Chrome)。
2. 开启 **开发者模式**。
3. 点击 **加载解压缩的扩展程序**，选择本技能目录下的 `assets/extension`。

### 3. 运行服务器
```bash
python scripts/task_server.py
```

## 核心特性
- **真实环境**：由于运行在浏览器插件中，完全模拟真实用户操作。
- **批量处理**：全自动循环处理任务队列。
- **图生图支持**：自动处理本地素材上传。

详情请参阅 [SKILL.md](./SKILL.md)。
