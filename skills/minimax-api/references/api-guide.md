# MiniMax API 详细调用指南

## 目录

- [示例约定与错误处理](#示例约定与错误处理)
- [文本生成 (Anthropic 兼容)](#文本生成-anthropic-兼容)
- [语音合成 (TTS)](#语音合成-tts)
- [语音克隆](#语音克隆)
- [文生图 (Text-to-Image)](#文生图-text-to-image)
- [图生图 (Image-to-Image)](#图生图-image-to-image)
- [视频生成 (T2V)](#视频生成-t2v)
- [音乐生成](#音乐生成)
- [使用 Python 脚本](#使用-python-脚本)

## 示例约定与错误处理

先在本机配置 MINIMAX_API_HOST、MINIMAX_API_KEY，不在聊天或日志打印凭证。以下代码展示调用形态，模型和响应字段以当前服务版本为准，未进行线上验证。HTTP 成功不等于业务成功；每次 JSON 响应均须检查业务状态并确认需要的字段，异常时停止后续下载或合成，不输出原始请求/响应全文。

```python
def check_business_result(result: dict) -> None:
    base_resp = result.get("base_resp") or {}
    code = base_resp.get("status_code", 0)
    if code not in (0, "0"):
        raise RuntimeError(f"MiniMax 业务请求失败，错误码：{code}")
```

调用方捕获 requests.RequestException、JSON 解析及缺字段错误，提供脱敏错误摘要；不无上限重试计费生成请求。下载 URL 仅接受预期可信服务的 http(s) 地址，下载时不要携带模型接口 Authorization 头。

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
    },
    timeout=(5, 60),
)
response.raise_for_status()
result = response.json()
check_business_result(result)
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
    },
    timeout=(5, 60),
)
response.raise_for_status()
check_business_result(response.json())
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
    },
    timeout=(5, 60),
)
response.raise_for_status()
check_business_result(response.json())
```

## 语音克隆

上传只返回 file_id，不能直接得到已克隆的 voice_id。流程与 [技能说明](../SKILL.md#语音克隆) 及脚本一致：先上传，再调用 voice_clone，成功后使用自定义 voice_id 合成。只处理已取得授权的声音。

### 步骤 1：上传待克隆音频

```python
with open("audio.wav", "rb") as audio_file:
    upload_resp = requests.post(
        f"{MINIMAX_API_HOST}/v1/files/upload",
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
        data={"purpose": "voice_clone"},
        files={"file": audio_file},
        timeout=(5, 30),
    )
upload_resp.raise_for_status()
upload_result = upload_resp.json()
check_business_result(upload_result)
file_id = upload_result["file"]["file_id"]
```

可选示例音频上传使用同一 `/v1/files/upload`，但 `purpose` 为 `prompt_audio`；从响应 `file.file_id` 取得 prompt_file_id，不把它误当作 voice_id。

### 步骤 2：创建音色

```python
voice_id = "your_custom_voice_id"
clone_resp = requests.post(
    f"{MINIMAX_API_HOST}/v1/voice_clone",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "file_id": file_id,
        "voice_id": voice_id,
        "text": "克隆效果试听文本",
        "model": "speech-2.8-hd",
        # 可选："clone_prompt": {"prompt_audio": prompt_file_id, "prompt_text": "示例文本"}
    },
    timeout=(5, 60),
)
clone_resp.raise_for_status()
check_business_result(clone_resp.json())
```

### 步骤 3：使用已创建的音色

```python
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/t2a_v2",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "speech-2.8-hd",
        "text": "使用克隆声音说话",
        "voice_setting": {"voice_id": voice_id},
    },
    timeout=(5, 60),
)
response.raise_for_status()
check_business_result(response.json())
```

## 文生图 (Text-to-Image)

```python
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/image_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "image-01",
        "prompt": "一只可爱的猫咪",
        "aspect_ratio": "1:1"
    },
    timeout=(5, 60),
)
response.raise_for_status()
result = response.json()
check_business_result(result)
```

### 下载图片到本地

```python
import requests

# 生成图片
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/image_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={"model": "image-01", "prompt": "一只可爱的猫咪", "aspect_ratio": "1:1"},
    timeout=(5, 60),
)
response.raise_for_status()
result = response.json()
check_business_result(result)

# 从响应中提取 URL 并下载
image_url = result["data"]["image_urls"][0]
img_resp = requests.get(image_url, timeout=(5, 60))
img_resp.raise_for_status()
with open("output.jpg", "wb") as f:
    f.write(img_resp.content)
```

支持的宽高比：`1:1`, `16:9`, `9:16`, `4:3`, `3:4`, `3:2`, `2:3`, `21:9`

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
    },
    timeout=(5, 60),
)
response.raise_for_status()
check_business_result(response.json())
```

## 视频生成 (T2V)

### 创建任务

```python
response = requests.post(
    f"{MINIMAX_API_HOST}/v1/video_generation",
    headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
    json={
        "model": "MiniMax-Hailuo-2.3",
        "prompt": "日出时分，海浪拍打沙滩"
    },
    timeout=(5, 60),
)
response.raise_for_status()
result = response.json()
check_business_result(result)
task_id = result["data"]["task_id"]
print(f"任务 ID: {task_id}")
```

### 查询状态

使用 monotonic 总期限，超时后不再发起下一轮。注意 requests 的 timeout 是连接/读取等待限制，不是严格墙钟中断；当前正在接收数据的请求可能超过总预算，要求硬期限时由调用任务系统设置外层取消和总超时，不能仅依赖 requests timeout。

```python
import time

deadline = time.monotonic() + 600  # 轮询总预算 10 分钟，请求返回后也检查
while True:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("视频任务等待超过 10 分钟，请保留任务 ID 后续查询")
    # 每次请求也有超时；总 deadline 在请求返回后再次检查
    status_resp = requests.get(
        f"{MINIMAX_API_HOST}/v1/video_generation/{task_id}",
        headers={"Authorization": f"Bearer {MINIMAX_API_KEY}"},
        timeout=min(30, remaining),
    )
    status_resp.raise_for_status()
    status = status_resp.json()
    check_business_result(status)
    if time.monotonic() >= deadline:
        raise TimeoutError("视频任务查询超过总等待期限")
    task_status = str(status["data"]["status"]).lower()
    if task_status == "success":
        break
    if task_status in {"failed", "fail"}:
        raise RuntimeError("视频生成失败，请使用任务 ID 排查")
    time.sleep(min(5, max(0, deadline - time.monotonic())))
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
    },
    timeout=(5, 60),
)
response.raise_for_status()
check_business_result(response.json())
```

## 使用 Python 脚本

```bash
# 文本对话
python scripts/minimax.py chat "解释量子计算" --model MiniMax-M2.7-200k

# 语音合成
python scripts/minimax.py tts "你好，世界" --voice-id your_voice_id

# 上传待克隆音频，读取返回的 file.file_id
python scripts/minimax.py clone-upload audio.wav

# 创建音色，再使用自定义 voice_id 合成
python scripts/minimax.py voice-clone <file_id> <自定义voice_id> "克隆用的文本"
python scripts/minimax.py tts "使用克隆的声音" --voice-id <自定义voice_id>

# 文生图 (仅返回 JSON)
python scripts/minimax.py image "一只可爱的猫咪" --ratio 16:9

# 文生图 + 自动下载
python scripts/minimax.py image "一只可爱的猫咪" --download

# 文生图 + 指定输出路径
python scripts/minimax.py image "一只可爱的猫咪" -o cat.jpg

# 图生图 + 自动下载
python scripts/minimax.py i2i input.jpg "变成卡通风格" --download

# 图生图 + 指定输出路径
python scripts/minimax.py i2i input.jpg "变成卡通风格" -o output.jpg

# 视频生成 (返回 task_id)
python scripts/minimax.py video "日出时分，海浪拍打沙滩"

# 查询视频状态
python scripts/minimax.py video-query task_id_here
```