# gpt-image

OpenAI GPT Image 系列画图、图生图与图片编辑技能，默认使用当前最新绘图模型 `gpt-image-2`，也支持 `gpt-image-1`、`gpt-image-1.5` 等版本切换，以及文生图、参考图生成、局部编辑、尺寸/质量/格式配置和结果文件保存。

## 安装

```bash
npx skills add ayflying/ai-skills --skill gpt-image
```

## 配置

```bash
cp .env.example .env
```

填写：

```env
GPT_IMAGE_API_KEY=your-gpt-image-api-key
GPT_IMAGE_BASE_URL=https://api.openai.com/v1
```

脚本仍兼容旧的 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`，但推荐使用 `GPT_IMAGE_*`，避免和容器或其他 AI 服务的全局环境变量冲突。

安装依赖：

```bash
pip install requests
```

## 使用

```bash
python scripts/gpt_image.py generate "一张现代产品海报，干净构图，真实摄影质感" -o outputs/poster.png
```

```bash
python scripts/gpt_image.py i2i "把产品图改成高端电商主图，保留产品外观" --image product.png --model gpt-image-2 -o outputs/product-main.png
```

```bash
python scripts/gpt_image.py edit "保持产品外观，把背景改成极简摄影棚" --image product.png --model gpt-image-2 -o outputs/product-studio.png
```

更多参数与提示词建议见 `SKILL.md`。
