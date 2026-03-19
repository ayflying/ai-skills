#!/bin/bash

echo "============================================================"
echo "                   微信机器人测试启动器"
echo "============================================================"

echo ""
echo "[!] 重要警告:"
echo "    1. 个人微信自动化可能违反微信使用条款"
echo "    2. 可能导致账号被限制或封禁"
echo "    3. 网页版微信功能有限，部分功能不可用"
echo ""
echo "[!] 建议:"
echo "    1. 务必使用【测试专用微信号】"
echo "    2. 不要使用主力账号或重要账号"
echo "    3. 测试完成后及时退出登录"
echo ""
echo "============================================================"

echo ""
read -p "是否已了解风险并继续测试？(yes/no): " confirm
if [ "$confirm" != "yes" ] && [ "$confirm" != "y" ]; then
    echo "[INFO] 测试已取消"
    exit 0
fi

echo ""
echo "[1/4] 运行基础测试..."
python3 scripts/test_bot.py
if [ $? -ne 0 ]; then
    echo "[ERROR] 基础测试失败"
    exit 1
fi

echo ""
echo "[2/4] 检查配置..."
python3 scripts/wechat_bot.py --test
if [ $? -ne 0 ]; then
    echo "[ERROR] 配置检查失败"
    exit 1
fi

echo ""
echo "[3/4] 启动微信机器人..."
echo "请稍候，等待二维码显示..."
echo "使用测试微信账号扫描二维码登录。"
echo ""
echo "登录后请测试以下功能:"
echo "  1. 发送文本消息"
echo "  2. 发送 /help 命令"
echo "  3. 发送图片/语音/视频/文件"
echo "  4. 发送 /export 导出数据"
echo ""
echo "按 Ctrl+C 可停止机器人"
echo ""

python3 scripts/wechat_bot.py

echo ""
echo "[4/4] 测试完成清理建议:"
echo "  1. 在手机微信上退出网页版登录"
echo "  2. 检查并备份 data/ 目录中的重要数据"
echo "  3. 可选: 删除测试数据 (rm -rf data/ logs/)"
echo ""
read -p "按回车键继续..."