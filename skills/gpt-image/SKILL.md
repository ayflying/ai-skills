---
name: gpt-image
description: |
  OpenAI GPT Image 系列画图、图生图与图片编辑技能，兼容 gpt-image-1、gpt-image-1.5、gpt-image-2 等版本，封装文生图、参考图生成、局部编辑、尺寸/质量/格式参数和结果落盘流程。Use when: (1) 需要调用 GPT Image 系列模型生成图片 (2) 需要使用 gpt-image-2 图生图或参考图生成新图 (3) 需要在不同 GPT Image 版本之间切换测试 (4) 需要根据一张或多张参考图进行图片编辑或重绘 (5) 需要输出 png/jpeg/webp 图片文件 (6) 需要处理 GPT Image API 的 base64 图片响应
---

# gpt-image

使用 OpenAI GPT Image 系列模型进行图片生成、图生图和编辑。优先使用随技能提供的 `scripts/gpt_image.py`，避免重复编写请求、base64 解码和文件保存逻辑。

## 安装命令

```bash
npx skills add ayflying/ai-skills --skill gpt-image
```

## 前提条件

1. 设置 `OPENAI_API_KEY`，或复制 `.env.example` 为 `.env` 后填写。
2. 安装依赖：
   ```bash
   pip install requests
   ```
3. 在技能目录执行命令：
   ```bash
   cd skills/gpt-image
   ```

## 模型选择

默认使用当前最新 GPT Image 绘图模型 `gpt-image-2`。只有用户明确指定模型时，才用 `--model` 切换到其它 GPT Image 版本：

```bash
python scripts/gpt_image.py generate "一枚简洁的应用图标" -o outputs/icon.png
python scripts/gpt_image.py generate "一枚简洁的应用图标" --model gpt-image-1.5 -o outputs/icon-v1-5.png
```

只使用 GPT Image 系列模型；不要把 `seedream`、`gemini` 等非 GPT 画图模型写进此技能。

## 文生图

```bash
python scripts/gpt_image.py generate "一张现代 SaaS 仪表盘宣传图，清爽明亮，真实产品截图质感" -o outputs/dashboard.png
```

常用参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--model` | GPT Image 模型版本 | `gpt-image-2` |
| `--size` | 输出尺寸，支持 `auto` 或 `WIDTHxHEIGHT` | `auto` |
| `--quality` | `auto`、`low`、`medium`、`high` | `auto` |
| `--format` | `png`、`jpeg`、`webp` | `png` |
| `--background` | `auto`、`opaque`，部分模型支持 `transparent` | `auto` |
| `--moderation` | `auto` 或 `low` | `auto` |
| `--n` | 生成数量 | `1` |

自定义 `WIDTHxHEIGHT` 时，优先使用官方模型支持的尺寸；遇到网关或模型报参数不支持时，先改为 `--size auto`、`--quality auto`、`--format png` 做最小请求。

## 图生图

`gpt-image-2` 支持图像输入与图像输出。图生图使用 Image API 的 `edits` 端点：上传一张或多张参考图，再用 prompt 描述新图。

```bash
python scripts/gpt_image.py i2i "把这张产品图改成高端电商主图，保留产品外观，白色摄影棚背景" --image product.png --model gpt-image-2 -o outputs/product-main.png
```

多参考图图生图：

```bash
python scripts/gpt_image.py i2i "把这些物品组合成一张节日礼盒产品图" --image item1.png --image item2.png --image item3.png --model gpt-image-2 -o outputs/gift.png
```

## 图片编辑

使用一张或多张参考图生成新图：

```bash
python scripts/gpt_image.py edit `
  "把参考图中的产品放进极简白色摄影棚，保持产品外观一致" `
  --image product.png `
  -o outputs/product-studio.png
```

局部编辑可加 mask。mask 必须和第一张输入图尺寸一致，并包含 alpha 通道：

```bash
python scripts/gpt_image.py edit "只把沙发替换成浅绿色，其余保持不变" --image room.png --mask mask.png -o outputs/room-green-sofa.png
```

`gpt-image-2` 会自动以高保真处理输入图，不要为它传 `input_fidelity`；旧版模型如需保真参数，再按实际接口支持传入。

## 提示词规则

- 先写用途和主体，再写画面结构、材质、光线、镜头、文字内容和禁止项。
- 需要真实照片时，明确相机语言：镜头焦段、光线方向、景深、拍摄年代或质感。
- 需要 UI、海报、信息图时，明确版式层级、文字内容、留白、品牌色和输出比例。
- 需要稳定编辑时，写清楚“保持不变”的内容，例如人物身份、产品形状、原始构图或文字。
- 遇到版本差异时，优先保持 prompt 不变，只切换 `--model`，便于比较模型效果。

## 输出与限制

- GPT Image 模型默认返回 `b64_json`，脚本会自动解码并保存为图片文件。
- GPT Image 系列主要使用 `v1/images/generations` 和 `v1/images/edits`；图生图属于 `edits` 端点的参考图生成能力。
- `output_format` 可用 `png`、`jpeg`、`webp`；`jpeg` 和 `webp` 可配合 `--compression`。
- 不要提交 `.env` 或任何真实 API Key。

## 官方文档

- 图片生成指南：https://developers.openai.com/api/docs/guides/image-generation
- 图片 API：https://developers.openai.com/api/reference/resources/images
