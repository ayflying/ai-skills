# 微信机器人测试指南

## 1. 环境检查

### 1.1 检查Python版本
```bash
python --version
# 应该显示 Python 3.10+
```

### 1.2 检查依赖安装
```bash
# 进入技能目录
cd skills/wechat-bot

# 检查已安装的包
pip list | grep -E "(wxpy|python-dotenv)"
```

## 2. 基础测试

### 2.1 运行测试脚本
```bash
# 运行基础测试
python scripts/test_bot.py
```

**预期输出**：
- 所有导入测试通过
- 配置加载成功
- 数据目录创建成功
- 测试结果: 3/3 通过

### 2.2 测试配置文件
```bash
# 检查.env文件
cat .env
```

## 3. 功能测试

### 3.1 测试配置加载
```python
# 创建测试脚本
python -c "
from scripts.wechat_bot import WeChatBot
bot = WeChatBot()
print('配置加载成功:', bot.config)
"
```

### 3.2 测试数据目录创建
```bash
# 检查目录是否创建
ls -la data/
ls -la logs/
```

## 4. 运行模式测试

### 4.1 测试模式运行
```bash
# 以测试模式启动（不实际连接微信）
python scripts/wechat_bot.py --test
```

**预期输出**：
- 显示配置信息
- 不显示二维码
- 机器人已初始化但未启动

### 4.2 帮助信息
```bash
# 查看帮助信息
python scripts/wechat_bot.py --help
```

## 5. 实际运行测试（需要微信账号）

### 5.1 测试账号准备
**重要提示**：建议使用**测试专用微信账号**，不要使用主力账号！

1. 准备一个专门的测试微信号
2. 确保该账号可以正常登录网页版微信
3. 准备一些测试联系人或群聊

### 5.2 启动机器人
```bash
# 确保在正确的目录
cd skills/wechat-bot

# 启动机器人
python scripts/wechat_bot.py
```

### 5.3 扫描二维码登录
1. 运行后会显示二维码
2. 使用测试微信账号扫描二维码
3. 在手机上确认登录

### 5.4 测试消息功能
1. **发送测试消息**：
   - 用另一个微信账号向机器人发送消息
   - 检查机器人是否收到

2. **测试自动回复**：
   - 发送任意文本消息
   - 检查是否收到自动回复

3. **测试命令**：
   - 发送 `/help` 查看帮助
   - 发送 `/status` 查看状态
   - 发送 `/stats` 查看统计
   - 发送 `/export` 导出数据

4. **测试媒体文件**：
   - 发送图片、语音、视频、文件
   - 检查 `data/media/` 目录是否保存

## 6. 数据检查

### 6.1 查看消息记录
```bash
# 查看今日消息文件
ls -la data/messages_$(date +%Y-%m-%d).json

# 查看消息内容（Windows）
type data\messages_2026-03-19.json

# 查看消息内容（Linux/Mac）
cat data/messages_2026-03-19.json | jq .
```

### 6.2 查看媒体文件
```bash
# 查看保存的媒体文件
ls -la data/media/
```

### 6.3 查看日志文件
```bash
# 查看最新的日志文件
ls -la logs/
```

## 7. 故障排除

### 7.1 常见问题及解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 无法导入wxpy | 未安装依赖 | `pip install wxpy python-dotenv` |
| 二维码不显示 | 终端问题 | 尝试其他终端或使用`console_qr=False` |
| 登录失败 | 微信账号限制 | 使用测试账号，检查网络连接 |
| 消息收不到 | 登录状态问题 | 重新启动机器人 |
| 发送失败 | 联系人不存在 | 检查联系人名称 |

### 7.2 调试模式
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python scripts/wechat_bot.py
```

### 7.3 清理测试数据
```bash
# 删除测试数据
rm -rf data/
rm -rf logs/
rm -f .env
```

## 8. 性能测试

### 8.1 消息吞吐量测试
1. 使用测试账号连续发送10条消息
2. 检查机器人是否全部接收
3. 查看响应时间

### 8.2 长时间运行测试
```bash
# 后台运行（Linux/Mac）
nohup python scripts/wechat_bot.py > wechat_bot.log 2>&1 &

# Windows 使用 start 命令
start python scripts/wechat_bot.py
```

## 9. 安全测试

### 9.1 过滤功能测试
1. 修改`.env`文件中的`GROUP_FILTER`或`CONTACT_FILTER`
2. 重新启动机器人
3. 测试过滤规则是否生效

### 9.2 敏感信息检查
```bash
# 确保.gitignore正确配置
cat .gitignore

# 确保敏感文件不被提交
git status
```

## 10. 停止机器人

### 10.1 正常停止
- 在终端按 `Ctrl+C`
- 机器人会自动保存会话数据

### 10.2 强制停止
```bash
# 查找进程
ps aux | grep wechat_bot

# 终止进程
kill -9 <PID>
```

## 11. 测试报告模板

```
测试日期: 2026-03-19
测试账号: test_wechat_001

测试项目 | 状态 | 备注
---------|------|------
依赖安装 | ✅ 通过 | wxpy, python-dotenv
基础测试 | ✅ 通过 | test_bot.py 3/3 通过
配置加载 | ✅ 通过 | .env文件正常
二维码显示 | ✅ 通过 | 显示正常
登录功能 | ⏳ 待测试 | 需要测试账号
消息收发 | ⏳ 待测试 | 需要测试账号
自动回复 | ⏳ 待测试 | 需要测试账号
媒体文件 | ⏳ 待测试 | 需要测试账号
命令功能 | ⏳ 待测试 | 需要测试账号

总体评估: 基础功能正常，需要实际微信账号进行完整测试。
```

## 注意事项

1. **风险提示**：微信机器人可能违反微信使用条款
2. **测试账号**：务必使用专用测试账号
3. **数据备份**：定期备份重要数据
4. **日志清理**：定期清理日志文件
5. **合规使用**：仅用于合法的自动化需求