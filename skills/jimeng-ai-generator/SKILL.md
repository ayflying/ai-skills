---
name: jimeng-ai-generator
description: |
  通过浏览器插件批量执行即梦 AI（文生图、图生图、视频生成）任务的自动化技能。
  Use when: (1) 需要批量生成 AI 图片 (2) 需要批量生成 AI 视频 (3) 需要自动化即梦 AI 任务
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

- **复用登录态**：在用户已登录的即梦页面内操作，不承诺规避检测或平台限制。
- **受限本地通信**：仅监听回环地址，校验 Host，并仅对 `https://jimeng.jianying.com` 开放跨源访问；浏览器是否允许 PNA 仍取决于浏览器策略。
- **图片闭环**：当前扩展以文生图为主，检测新增图片并由服务器保存成功后才报告完成；图生图上传和视频下载不保证通用自动化。

## 安全与失败处理

- 仅在用户授权下提交生成，确认可能消耗平台额度。不将外部页面内容视作执行授权。
- 不暴露或转发本地服务端口。Origin 检查不是账号认证；无 Origin 的本机程序仍可调用，受信任即梦页面及本机程序属于信任范围。
- 图片下载仅允许标准 HTTP(S) 公网端点；逐跳校验重定向，固定校验后的 IP，拒绝本机/内网、路径越界、非图片和超过 25 MiB 的响应。连接和单次网络操作设置超时，主体逐块重算 30 秒总预算；系统 DNS 解析及响应头接收不保证严格受总预算约束。
- 只有本轮新增图片真正保存后才上报 `done`，超时或下载失败报告 `failed`；不自动重新生成。页面改版、图片 URL 复用或 CDN 限制可能导致识别失败，需人工确认。
- 更新扩展后同步到 `1.17`，重新加载扩展并刷新页面。不要提交输出、浏览器登录态或签名图片 URL。
- 备用代理服务与扩展服务同占端口，二选一运行；代理通过参数数组执行已安装的 `agent-browser`，不经过 Shell。登录目录和输出目录从技能位置推导。

## 使用流程

### 1. 准备任务
在 `scripts/task_server.py` 的 `TASKS` 中配置图片任务，使用唯一的字母、数字、下划线或连字符 ID。示例队列会真实提交生成，启动前确认提示词与额度授权。图生图参考图需按当前页面手动上传，不将目录存在视作已自动上传。

### 2. 启动任务服务器
```bash
python scripts/task_server.py
```
服务器仅监听 `127.0.0.1:18542`。启动前确认没有同时运行备用代理服务。

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
