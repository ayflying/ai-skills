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

音色克隆完整流程：

```bash
# 1. 上传待克隆音频 (10秒-5分钟)
python scripts/minimax.py clone-upload audio.wav
# 返回 {"file": {"file_id": "xxx"}, ...}

# 2. (可选) 上传示例音频增强效果 (<8秒)
python scripts/minimax.py clone-upload-prompt prompt.wav
# 返回 {"file": {"file_id": "yyy"}, ...}

# 3. 执行音色克隆
python scripts/minimax.py voice-clone <file_id> <自定义voice_id> "克隆用的文本"
# 可选: --prompt-file-id <prompt_file_id> --prompt-text "示例文本"

# 4. 使用克隆的 voice_id 进行语音合成
python scripts/minimax.py tts "使用克隆的声音" --voice-id 你的voice_id
```

### WebSocket 语音合成

流式语音合成，支持更长文本 (最长 10,000 字符)：

```bash
# 基本用法
python scripts/minimax.py tts-ws "要转换的文本" -o output.mp3

# 使用克隆的声音
python scripts/minimax.py tts-ws "要转换的文本" --voice-id 你的voice_id -o output.mp3

# 调整语速和音调
python scripts/minimax.py tts-ws "要转换的文本" --speed 1.2 --pitch 0 -o output.mp3
```

**参数说明**：
- `--voice-id` - 语音 ID (可用克隆的自定义 ID 或预设 ID)
- `--model` - TTS 模型 (speech-2.8-hd/speech-2.6-hd/speech-02-hd 等)
- `--speed` - 语速 (默认 1.0)
- `--pitch` - 音调 (默认 0)
- `--format` - 音频格式 (mp3/wav/pcm)
- `--bitrate` - 比特率 (默认 128000)
- `--sample-rate` - 采样率 (默认 32000)

### 视频生成

视频生成是**异步**的，需要先创建任务，再查询状态。支持三种模式：

#### 文生视频 (T2V)

```bash
python scripts/minimax.py video "日出时分，海浪拍打沙滩，远处海鸥飞过[推进]"
# 返回 {"task_id": "xxx", ...}

# 指定时长和分辨率
python scripts/minimax.py video "海边日落" --duration 10 --resolution 1080P
```

#### 图生视频 (I2V)

```bash
python scripts/minimax.py i2v "猫咪转身看向镜头[左摇]" image.jpg

# 使用 URL
python scripts/minimax.py i2v "人物走向镜头" https://example.com/image.jpg
```

#### 首尾帧视频 (FL2V)

```bash
python scripts/minimax.py fl2v "小女孩成长为女人" start.jpg end.jpg
```

#### 查询视频状态

```bash
python scripts/minimax.py video-query <task_id>
```

**运镜指令**：在 prompt 中使用 `[指令]` 可控制镜头移动：
- `[左移]` `[右移]` `[左摇]` `[右摇]` `[推进]` `[拉远]`
- `[上升]` `[下降]` `[上摇]` `[下摇]`
- `[变焦推近]` `[变焦拉远]` `[晃动]` `[跟随]` `[固定]`

**参数说明**：
- `--model` - 模型 (T2V: MiniMax-Hailuo-2.3/MiniMax-Hailuo-02/T2V-01; I2V: MiniMax-Hailuo-2.3/MiniMax-Hailuo-02/I2V-01; FL2V: MiniMax-Hailuo-02)
- `--duration` - 时长 (6或10秒)
- `--resolution` - 分辨率 (512P/720P/768P/1080P)

### 音乐生成

支持带歌词的歌曲和纯音乐生成。

```bash
# 生成有歌词的歌曲
python scripts/minimax.py music "流行音乐,欢快,阳光" --lyrics "[Verse]\n歌词第一行\n歌词第二行"

# 生成纯音乐
python scripts/minimax.py music "爵士乐,放松,咖啡馆" --instrumental

# 自动生成歌词（根据 prompt）
python scripts/minimax.py music "独立民谣,忧郁,内省" --lyrics-optimizer

# 下载到本地
python scripts/minimax.py music "流行音乐" --download -o song.mp3
```

**参数说明**：
- `prompt` - 音乐描述（风格、情绪、场景），必填
- `--lyrics` - 歌词，使用 `\n` 分隔行，支持结构标签如 `[Verse]`, `[Chorus]` 等
- `--instrumental` - 生成纯音乐（无人声）
- `--lyrics-optimizer` - 根据 prompt 自动生成歌词
- `--format` - 音频格式 (mp3/wav/pcm，默认 mp3)
- `--bitrate` - 比特率 (默认 256000)
- `--sample-rate` - 采样率 (默认 44100)

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
| WebSocket 语音合成 | `WSS /ws/v1/t2a_v2` |
| 克隆音频上传 | `POST /v1/files/upload` |
| 示例音频上传 | `POST /v1/files/upload` |
| 音色克隆 | `POST /v1/voice_clone` |
| 文生图/图生图 | `POST /v1/image_generation` |
| 视频生成 | `POST /v1/video_generation` |
| 视频查询 | `GET /v1/video_generation/{task_id}` |
| 音乐生成 | `POST /v1/music_generation` |

## 更多信息

- API 文档：https://platform.minimaxi.com
- MCP 集成：https://platform.minimaxi.com/docs/guides/mcp-guide.md