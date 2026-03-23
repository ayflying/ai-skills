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
3. 配置环境变量（参考 `.env.example`）

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MINIMAX_API_KEY` | API Key | - |
| `MINIMAX_API_HOST` | API 地址 | `https://api.minimaxi.com` (国内) |

地区对应：
- 国内: `https://api.minimaxi.com`
- 国际: `https://api.minimax.io`

## 快速使用

```bash
# 文本对话
python scripts/minimax.py chat "你好"

# 文生图
python scripts/minimax.py image "一只可爱的猫咪"

# 图生图
python scripts/minimax.py i2i input.jpg "变成卡通风格"

# 语音合成
python scripts/minimax.py tts "你好，世界"

# 视频生成
python scripts/minimax.py video "日出时分，海浪拍打沙滩"
```

## API 端点速查

| 功能 | 端点 |
|------|------|
| 文本生成 | `POST /anthropic/v1/messages` |
| 语音合成 | `POST /v1/t2a_v2` |
| 语音克隆 | `POST /v1/voice_cloning/upload` |
| 文生图/图生图 | `POST /v1/image_generation` |
| 视频生成 | `POST /v1/video_generation` |
| 音乐生成 | `POST /v1/music_generation` |

## 详细文档

- API 详细调用示例：参见 [references/api-guide.md](references/api-guide.md)
- 模型列表：参见 [references/models.md](references/models.md)

## 错误处理

| 错误码 | 说明 |
|--------|------|
| 1003 | API Key 无效 |
| 1004 | 余额不足 |
| 1005 | 限流 |
| 2001 | 请求参数错误 |
| 3001 | 内容审核不通过 |

## 更多信息

- API 文档：https://platform.minimax.io/docs
- MCP 集成：https://platform.minimax.io/docs/guides/mcp-guide.md