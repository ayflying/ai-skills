# Jimeng AI Universal Generator (即梦 AI 全能生成)

通过浏览器扩展辅助操作已登录的即梦 AI 页面，分发生成任务并保存图片。当前扩展自动闭环以文生图为主；图生图上传和视频下载需按页面实际能力处理，不保证通用自动化。

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
- **复用登录态**：扩展在即梦页面内操作，不承诺规避检测或平台限制。
- **任务分发**：任务认领后从队列移除，失败不自动重试，避免重复消耗额度。
- **完成校验**：只接受本轮新增图片，服务器确认保存后才能标记完成；界面变化可能导致识别失败，需要人工确认。

## 本地信任与安全边界

- 服务仅监听 `127.0.0.1:18542`，扩展通过 `http://localhost:18542` 调用。不要用反向代理或端口转发暴露服务。
- 检查本机 `Host`，浏览器跨源请求仅允许 `https://jimeng.jianying.com`，不使用通配 CORS。无 Origin 的本机 CLI 仍允许访问；这不是用户身份认证，其他本机程序和受信任即梦页面脚本仍属于信任范围。
- 图片仅允许标准端口的 HTTP(S) 公网地址；每次重定向重新校验地址并固定校验后的 IP 连接，拒绝内网、本机及 `file://`。最多 3 次重定向、25 MiB；连接和单次网络操作设置超时，响应主体按块读取并重算 30 秒总预算，防止持续慢速主体拖延；系统 DNS 解析和响应头接收不保证严格受总预算约束。
- 任务 ID 不能含路径，输出位于技能目录的 `outputs/`；失败下载只清理本次创建的文件。不要共享登录态或签名图片地址。
- 扩展、服务版本均为 `1.17`。更新后在扩展管理页重新加载扩展并刷新即梦页面；旧版本会被拒绝。
- `agent_jimeng_server.py` 是另一种执行入口，与扩展任务服务使用同一端口，不能同时启动。使用它之前安装 `agent-browser` 并加入 PATH；不自动调用 `npx` 下载代码。Windows npm 安装使用标准 Node 入口，找不到时明确报错，不退回 Shell。

## 离线验证

从仓库根目录执行，不调用线上生成或浏览器：

```bash
python -m unittest discover -s skills/jimeng-ai-generator/scripts -p "test_local_services.py"
node --check skills/jimeng-ai-generator/assets/extension/content.js
node skills/jimeng-ai-generator/scripts/test_extension.cjs
```

详情请参阅 [SKILL.md](./SKILL.md)。
