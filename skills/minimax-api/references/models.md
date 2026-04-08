# MiniMax 模型列表

## 文本模型

| 模型 | 说明 | 上下文 | 特性 |
|------|------|--------|------|
| MiniMax-M2.7-200k | 最新旗舰模型 | 200k tokens | 强推理、代码、多模态 |
| MiniMax-M2.1-200k | 高性价比 | 200k tokens | 快速响应 |
| MiniMax-M2 | 平衡型 | 100k tokens | 通用场景 |
| MiniMax-M1-75k | 快速模型 | 75k tokens | 函数调用优化 |

## 语音模型

| 模型 | 说明 | 特性 |
|------|------|------|
| speech-2.8-hd | 精准还原真实语气细节 | 全面提升音色相似度 |
| speech-2.6-hd | 超低延时 | 归一化升级，更高自然度 |
| speech-2.8-turbo | 精准还原真实语气细节 | 更快更优惠 |
| speech-2.6-turbo | 极速版 | 适用于语音聊天和数字人场景 |
| speech-02-hd | 高清语音合成 | 多语言、情感控制 |
| speech-02 | 标准语音合成 | 低延迟 |
| speech-01 | 基础语音 | 简单场景 |

## 图像模型

| 模型 | 说明 |
|------|------|
| image-01 | 主力图像生成模型 |
| image-01-mini | 快速版本 |

## 视频模型

| 模型 | 说明 |
|------|------|
| video-01 | 文本/图像生成视频 |
| video-01-mini | 快速版本 |

## 音乐模型

| 模型 | 说明 |
|------|------|
| music-2.5+ | 最新旗舰音乐模型（推荐），支持纯音乐生成 |
| music-2.5 | 标准音乐模型 |
| music-01 | 歌词+描述生成完整歌曲 |

## API 端点

| 功能 | 端点 |
|------|------|
| 文本生成 | `POST {host}/anthropic/v1/messages` |
| 语音合成 | `POST {host}/v1/t2a_v2` |
| WebSocket 语音合成 | `WSS {host}/ws/v1/t2a_v2` |
| 克隆音频上传 | `POST {host}/v1/files/upload` |
| 示例音频上传 | `POST {host}/v1/files/upload` |
| 音色克隆 | `POST {host}/v1/voice_clone` |
| 文生图/图生图 | `POST {host}/v1/image_generation` |
| 视频生成 | `POST {host}/v1/video_generation` |
| 视频查询 | `GET {host}/v1/video_generation/{task_id}` |
| 音乐生成 | `POST {host}/v1/music_generation` |