# 微信机器人技能

基于wxpy的个人微信自动化机器人，支持消息收发、自动回复、文件传输和数据收集功能。

## 安装

```bash
npx skills add ayflying/ai-skills --skill wechat-bot
```

## 功能特性

- 消息收发（文本、图片、语音、视频、文件）
- 自动回复配置
- 媒体文件自动保存
- 消息数据收集和统计
- 内置命令支持（help、status、stats、export）

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件配置参数
   ```

3. 运行机器人：
   ```bash
   python scripts/wechat_bot.py
   ```

4. 扫描二维码登录微信

## 使用示例

```python
# 测试模式运行
python scripts/wechat_bot.py --test

# 指定配置文件
python scripts/wechat_bot.py --config /path/to/.env
```

## 命令列表

- `/help` - 显示帮助信息
- `/status` - 显示机器人状态
- `/stats` - 显示消息统计
- `/export` - 导出收集的数据

## 配置说明

详见 `.env.example` 文件，主要配置项：

- `AUTO_REPLY` - 是否启用自动回复
- `REPLY_MESSAGE` - 自动回复内容
- `COLLECT_MESSAGES` - 是否收集消息
- `SAVE_MEDIA` - 是否保存媒体文件

## 注意事项

1. **风险提示**：个人微信自动化可能违反微信使用条款，存在封号风险
2. **登录限制**：建议使用测试账号进行开发
3. **功能限制**：基于网页版微信，部分功能可能受限

## 文件结构

```
wechat-bot/
├── SKILL.md              # 技能文档
├── README.md             # 本文件
├── requirements.txt      # 依赖列表
├── .env.example          # 配置模板
└── scripts/
    └── wechat_bot.py     # 主程序
```

## 许可证

MIT License