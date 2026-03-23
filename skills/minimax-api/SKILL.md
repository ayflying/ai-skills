---
name: minimax-api
description: |
  MiniMax 多模态 AI API 集成，支持文本生成、语音合成、语音克隆、视频生成、图像生成和音乐创作。
  Use when: (1) 调用 MiniMax API 进行文本生成或对话 (2) 语音合成 (TTS) 或语音克隆 (3) 生成视频或图像 (4) 音乐生成 (5) 使用 Anthropic/OpenAI 兼容 API
---

# minimax-api

MiniMax 多模态 AI API 集成，通过 HTTP 调用 MiniMax 平台能力。

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill minimax-api
```

## 前提条件

1. 注册 MiniMax API 平台：https://platform.minimaxi.com
2. 创建 API Key：https://platform.minimaxi.com/user-center/basic-information/interface-key
3. 在技能目录下创建 `.env` 文件（复制 `.env.example` 并填入 API Key）

## 环境变量

```bash
MINIMAX_API_KEY=your-api-key
MINIMAX_API_HOST=https://api.minimaxi.com  # 国内版
# 或 https://api.minimax.io  # 国际版
```

## 脚本使用方式

所有命令需要在技能目录下执行（因为脚本依赖 `.env` 文件）：

```bash
cd skills/minimax-api
```

### 文本对话

```bash
python scripts/minimax.py chat "你好"
```

### 文生图 (Text-to-Image)

```bash
# 默认下载到 output_0.jpg
python scripts/minimax.py image "一只可爱的猫咪" --download

# 指定输出文件
python scripts/minimax.py image "一只可爱的猫咪" -o cat.jpg

# 指定宽高比
python scripts/minimax.py image "一只可爱的猫咪" --ratio 16:9
```

### 图生图 (Image-to-Image)

图生图基于参考图生成新图，当前仅支持**人物主体**参考（`subject_reference`）。

```bash
# 使用参考图生成（自动下载结果）
python scripts/minimax.py i2i input.jpg "把这张图变成卡通风格" --download

# 指定输出文件
python scripts/minimax.py i2i input.jpg "把这张图变成卡通风格" -o cartoon.jpg

# 指定宽高比
python scripts/minimax.py i2i input.jpg "把这张图变成卡通风格" --ratio 16:9
```

**参数说明**：
- `input.jpg` - 参考图片路径（支持 JPG、PNG）
- `"提示词"` - 描述想要的效果

### 语音合成 (TTS)

```bash
# 基本语音合成
python scripts/minimax.py tts "你好，世界"

# 指定声音 ID（需要先通过克隆获取）
python scripts/minimax.py tts "你好，世界" --voice-id your_voice_id
```

### 语音克隆

```bash
# 1. 上传音频获取 voice_id
python scripts/minimax.py clone-upload audio.wav

# 2. 使用返回的 voice_id 进行语音合成
python scripts/minimax.py tts "使用克隆的声音" --voice-id returned_voice_id
```

### 视频生成

视频生成是**异步**的，需要先创建任务，再查询状态。

```bash
# 1. 创建视频生成任务
python scripts/minimax.py video "日出时分，海浪拍打沙滩"
# 返回 {"id": "task_id", ...}

# 2. 使用返回的 task_id 查询状态
python scripts/minimax.py video-query <task_id>
```

## AI 使用本技能的指南

当用户请求生成图片、语音、视频或音乐时，AI 应该：

1. **确定任务类型**：
   - 文生图：用户只描述想要的内容
   - 图生图：用户提供参考图片或明确要求基于某图生成
   - 语音合成：用户要求将文字转为语音
   - 视频生成：用户要求生成视频

2. **执行脚本**：
   - 进入 `skills/minimax-api` 目录
   - 使用对应的命令执行

3. **下载结果**（如果有）：
   - 使用 `--download` 或 `-o` 参数自动下载
   - 或手动从 JSON 响应中提取 URL 下载

4. **返回结果给用户**：
   - 图片：返回文件路径或展示图片
   - 视频/语音：返回文件路径
   - 对话：直接返回文本

## 常见问题

**Q: 图生图的效果不理想？**
A: 图生图当前仅支持人物主体（character）参考，非人物图片可能效果有限。尝试更精确的提示词描述。

**Q: 视频生成需要多久？**
A: 视频生成是异步任务，通常需要几分钟。使用 `video-query` 命令轮询状态。

**Q: API 返回错误？**
A: 检查错误码：1003=无效Key，1004=余额不足，1005=限流，3001=内容审核不通过

## 模型列表

详见 [references/models.md](references/models.md)

## API 端点速查

| 功能 | 端点 |
|------|------|
| 文本生成 | `POST /anthropic/v1/messages` |
| 语音合成 | `POST /v1/t2a_v2` |
| 语音克隆上传 | `POST /v1/voice_cloning/upload` |
| 文生图/图生图 | `POST /v1/image_generation` |
| 视频生成 | `POST /v1/video_generation` |
| 视频查询 | `GET /v1/video_generation/{task_id}` |
| 音乐生成 | `POST /v1/music_generation` |

## 更多信息

- API 文档：https://platform.minimaxi.com
- MCP 集成：https://platform.minimaxi.com/docs/guides/mcp-guide.md