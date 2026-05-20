# gpt-image

OpenAI GPT Image 系列画图与图片编辑技能，支持 `gpt-image-1`、`gpt-image-1.5`、`gpt-image-2` 等版本切换，以及文生图、参考图编辑、尺寸/质量/格式配置和结果文件保存。

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
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

安装依赖：

```bash
pip install requests
```

## 使用

```bash
python scripts/gpt_image.py generate "一张现代产品海报，干净构图，真实摄影质感" --model gpt-image-1.5 -o outputs/poster.png
```

```bash
python scripts/gpt_image.py edit "保持产品外观，把背景改成极简摄影棚" --image product.png --model gpt-image-2 -o outputs/product-studio.png
```

更多参数与提示词建议见 `SKILL.md`。
