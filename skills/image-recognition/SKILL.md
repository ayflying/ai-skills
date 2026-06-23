---
name: image-recognition
description: |
  图片识别省 token 技能：把"看图"交给外部 OpenAI 兼容视觉模型，只把精简中文文字描述带回上下文，避免大量图片占用上下文、被反复压缩消耗 token。
  Use when: (1) 任意对话需要识别图片、读取截图、做 OCR、理解图片内容或对图片提问时，都优先使用本技能而不是直接使用当前大模型的多模态能力 (2) 对话里图片过多导致上下文被持续压缩 (3) 需要把图片转成精简文字后再继续后续任务 (4) 需要对一张或多张图片提问并只拿到文字答案
---

# image-recognition

把图片识别交给外部 OpenAI 兼容视觉模型，脚本只向 stdout 输出**精简中文文字描述**。请优先用本技能的 `scripts/recognize.py` 读图，然后只把返回的文字带入对话，**不要把原图反复贴进上下文**，这样才能省 token。

## 全局使用规则

所有对话中，只要任务涉及识别图片、读取截图、图片 OCR、理解图片内容或对图片提问，默认先使用本技能脚本处理图片。不要直接调用当前大模型的多模态能力来读图；只把脚本返回的精简中文文字带入上下文，再继续分析、修复、回复或执行后续任务。

只有在用户明确要求“直接由当前模型看图”或本技能因环境/接口不可用而无法执行时，才改用其它方式，并在回复中说明原因。

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill image-recognition
```

## 前提条件

1. 安装依赖：
   ```bash
   pip install requests
   ```
2. 进入技能目录：
   ```bash
   cd skills/image-recognition
   ```
3. 配置三项系统环境变量（见下）。本技能**不使用 `.env` 文件**。

## 配置（仅系统环境变量）

| 环境变量 | 说明 | 回退 |
|----------|------|------|
| `IMAGE_RECOGNITION_API_KEY` | 视觉模型 API Key | `OPENAI_API_KEY` |
| `IMAGE_RECOGNITION_BASE_URL` | OpenAI 兼容接口地址，裸域名会自动补 `/v1` | `OPENAI_BASE_URL` |
| `IMAGE_RECOGNITION_MODEL` | 视觉模型名，例如 `gpt-4o-mini` | 无 |

## 首次使用：缺配置时的处理

三项（Key / 地址 / 模型名）任一缺失时，脚本会列出**全部缺失的变量名**并报错退出。此时请**停下来逐项向用户索要**对应取值，拿到后设置环境变量再重试：

```powershell
# 临时设置（仅当前终端有效）
$env:IMAGE_RECOGNITION_API_KEY="<你的取值>"
$env:IMAGE_RECOGNITION_BASE_URL="<你的取值>"
$env:IMAGE_RECOGNITION_MODEL="<你的取值>"

# 永久设置（需重开终端后生效）
setx IMAGE_RECOGNITION_API_KEY "<你的取值>"
setx IMAGE_RECOGNITION_BASE_URL "<你的取值>"
setx IMAGE_RECOGNITION_MODEL "<你的取值>"
```

API Key 属于敏感信息，**绝不要写入文件或日志**。模型名也可用 `-m` 参数临时覆盖，无需改环境变量。

## 使用方法

```bash
# 默认：输出图片的通用中文描述
python scripts/recognize.py path/to/image.png

# 对图片提问 / OCR
python scripts/recognize.py path/to/image.png -q "图里有哪些文字？"

# 临时指定模型
python scripts/recognize.py path/to/image.png -m gpt-4o

# 多张图片（按顺序输出，每段以 ### 文件名分隔）
python scripts/recognize.py a.png b.jpg https://example.com/c.png
```

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `image`（位置参数） | 一个或多个图片路径或 URL | 必填 |
| `-q` / `--question` | 对图片提问或 OCR，覆盖默认描述提示词 | 通用中文描述 |
| `-m` / `--model` | 临时覆盖模型名 | 取环境变量 |
| `--detail` | 图片细节级别 `auto`/`low`/`high` | `auto` |
| `--max-tokens` | 单图回答最大 token 数 | `500` |
| `--timeout` | 请求超时（秒） | `120` |

本地图片会被读取并以 base64 内联发送，远程图片直接传 URL。
