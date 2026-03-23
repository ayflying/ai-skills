# MiniMax API 详细调用指南

## 文本生成 (Anthropic 兼容)

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
print(response.json())
```

## 语音合成 (TTS)

### 同步 TTS (短文本)

```python
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

### 指定声音

```python
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/t2a_v2",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "speech-02-hd",
        "text": "你好，世界",
        "voice_setting": {
            "voice_id": "voice_id_here"
        }
    }
)
```

## 语音克隆

### 步骤 1: 上传音频

```python
with open("audio.wav", "rb") as f:
    upload_resp = requests.post(
        f"{MINIMAX_API_HOST}/v1/voice_cloning/upload",
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
        files={"file": f}
    )
voice_id = upload_resp.json()["data"]["voice_id"]
print(f"克隆的声音 ID: {voice_id}")
```

### 步骤 2: 使用克隆声音合成

```python
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/t2a_v2",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "speech-02-hd",
        "text": "使用克隆声音说话",
        "voice_setting": {"voice_id": voice_id}
    }
)
```

## 文生图 (Text-to-Image)

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
print(response.json())
```

支持的宽高比：`1:1`, `16:9`, `9:16`, `4:3`, `3:4`

## 图生图 (Image-to-Image)

```python
import base64

# 读取参考图像并转为 base64
with open("input.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# 使用 subject_reference 指定参考图
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/image_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "image-01",
        "prompt": "将这只猫变成卡通风格",
        "aspect_ratio": "1:1",
        "subject_reference": [
            {"type": "character", "image_file": f"data:image/jpeg;base64,{image_base64}"}
        ]
    }
)
```

## 视频生成 (T2V)

### 创建任务

```python
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/video_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "video-01",
        "prompt": "日出时分，海浪拍打沙滩"
    }
)
task_id = response.json()["data"]["task_id"]
print(f"任务 ID: {task_id}")
```

### 查询状态

```python
import time

while True:
    status_resp = requests.get(
        f"{MINIMAX_API_HOST}/v1/video_generation/{task_id}",
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"}
    )
    status = status_resp.json()
    print(status)
    
    if status["data"]["status"] == "success":
        break
    elif status["data"]["status"] == "failed":
        print("生成失败")
        break
    
    time.sleep(5)  # 每 5 秒查询一次
```

## 音乐生成

```python
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/music_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "music-01",
        "prompt": "欢快的流行音乐，适合派对",
        "lyrics": """[verse]
这是一段歌词
[chorus]
副歌部分"""
    }
)
```

## 使用 Python 脚本

```bash
# 文本对话
python scripts/minimax.py chat "解释量子计算" --model MiniMax-M2.7-200k

# 语音合成
python scripts/minimax.py tts "你好，世界" --voice-id your_voice_id

# 上传克隆声音
python scripts/minimax.py clone-upload audio.wav

# 文生图
python scripts/minimax.py image "一只可爱的猫咪" --ratio 16:9

# 图生图
python scripts/minimax.py i2i input.jpg "变成卡通风格" --ratio 1:1

# 视频生成
python scripts/minimax.py video "日出时分，海浪拍打沙滩"

# 查询视频状态
python scripts/minimax.py video-query task_id_here
```