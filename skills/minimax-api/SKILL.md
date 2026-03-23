---
name: minimax-api
description: |
  MiniMax 多模态 AI API 集成，支持文本生成、语音合成、语音克隆、视频生成、图像生成和音乐创作。
  Use when: (1) 调用 MiniMax API 进行文本生成或对话 (2) 语音合成 (TTS) 或语音克隆 (3) 生成视频或图像 (4) 音乐生成 (5) 使用 Anthropic/OpenAI 兼容 API
---

# minimax-api

MiniMax 多模态 AI API 集成，通过 HTTP 调用MiniMax平台能力。

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill minimax-api
```

## 前提条件

1. 注册 MiniMax API 平台：https://platform.minimax.io
2. 创建 API Key：https://platform.minimax.io/user-center/basic-information/interface-key
3. 配置环境变量（参考 `.env.example`）

## API 端点

| 地区 | Base URL | API Key 获取 |
|------|----------|-------------|
| 国际 | `https://api.minimax.io` | platform.minimax.io |
| 国内 | `https://api.minimaxi.com` | platform.minimaxi.com |

## 环境变量

```bash
MINIMAX_API_KEY=your-api-key
MINIMAX_API_HOST=https://api.minimax.io  # 国际
# 或
MINIMAX_API_HOST=https://api.minimaxi.com  # 国内
```

## 核心功能

### 1. 文本生成 ( Anthropic 兼容)

```python
import requests

response = requests.post(
    f"{MINIMAX_API_HOST}/anthropic/v1/messages",
    headers={
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    },
    json={
        "model": "MiniMax-M2.7-200k",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "Hello"}]
    }
)
```

### 2. 语音合成 (TTS)

```python
# 同步 TTS (短文本)
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/t2a_v2",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "speech-02-hd",
        "text": "你好，世界",
        "stream": False
    }
)
```

### 3. 语音克隆

```python
# 1. 上传音频
with open("audio.wav", "rb") as f:
    upload_resp = requests.post(
        f"{MINIMAX_API_HOST}/v1/voice_cloning/upload",
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
        files={"file": f}
    )
voice_id = upload_resp.json()["data"]["voice_id"]

# 2. 使用克隆声音合成
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/t2a_v2",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={"model": "speech-02-hd", "text": "使用克隆声音", "voice_setting": {"voice_id": voice_id}}
)
```

### 4. 图像生成

```python
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/image_v2",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "image-01",
        "prompt": "一只可爱的猫咪",
        "aspect_ratio": "1:1"
    }
)
```

### 5. 视频生成 (T2V)

```python
# 创建任务
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/video_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "video-01",
        "prompt": "日出时分，海浪拍打沙滩"
    }
)
task_id = response.json()["data"]["task_id"]

# 查询状态
status_resp = requests.get(
    f"{MINIMAX_API_HOST}/v1/video_generation/{task_id}",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"}
)
```

### 6. 音乐生成

```python
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/music_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "music-01",
        "prompt": "欢快的流行音乐，适合派对",
        "lyrics": "[verse]\n这是一段歌词\n[chorus]\n副歌部分"
    }
)
```

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
- 模型列表：参见 [references/models.md](references/models.md)
- MCP 集成：https://platform.minimax.io/docs/guides/mcp-guide.md