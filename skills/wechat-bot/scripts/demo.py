#!/usr/bin/env python3
"""
微信机器人演示脚本
展示机器人功能的使用示例
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))


def demo_basic_usage():
    """演示基本使用"""
    print("微信机器人使用演示")
    print("=" * 40)

    print("\n1. 环境准备")
    print("   - Python 3.10+")
    print("   - wxpy 库: pip install wxpy")
    print("   - python-dotenv 库: pip install python-dotenv")

    print("\n2. 配置文件")
    print("   复制 .env.example 为 .env 并修改配置")
    print("   主要配置:")
    print("   - AUTO_REPLY=true/false  # 是否自动回复")
    print("   - REPLY_MESSAGE=回复内容  # 自动回复消息")
    print("   - COLLECT_MESSAGES=true  # 是否收集消息")
    print("   - SAVE_MEDIA=true       # 是否保存媒体文件")

    print("\n3. 运行模式")
    print("   基础测试: python scripts/test_bot.py")
    print("   测试模式: python scripts/wechat_bot.py --test")
    print("   实际运行: python scripts/wechat_bot.py")

    print("\n4. 功能命令")
    print("   /help    - 显示帮助信息")
    print("   /status  - 显示机器人状态")
    print("   /stats   - 显示消息统计")
    print("   /export  - 导出收集的数据")

    print("\n5. 数据存储")
    print("   - 消息记录: data/messages_YYYY-MM-DD.json")
    print("   - 媒体文件: data/media/{类型}/{时间}_{发送者}.{扩展名}")
    print("   - 会话数据: data/sessions.json")
    print("   - 日志文件: logs/wechat_bot_YYYYMMDD_HHMMSS.log")

    print("\n6. 安全提示")
    print("   [!] 风险: 个人微信自动化可能违反微信使用条款")
    print("   [!] 建议: 使用测试专用微信号")
    print("   [!] 限制: 网页版微信功能有限")


def demo_config_check():
    """演示配置检查"""
    print("\n7. 配置检查演示")

    try:
        from wechat_bot import WeChatBot

        # 创建机器人实例（测试模式）
        bot = WeChatBot()

        print("   配置加载成功!")
        print(f"   - 自动回复: {bot.config['auto_reply']}")
        print(f"   - 回复消息: {bot.config['reply_message']}")
        print(f"   - 收集消息: {bot.config['collect_messages']}")
        print(f"   - 保存媒体: {bot.config['save_media']}")
        print(f"   - 数据目录: {bot.data_dir}")

        return True

    except Exception as e:
        print(f"   配置检查失败: {e}")
        return False


def demo_file_structure():
    """演示文件结构"""
    print("\n8. 文件结构演示")

    skill_dir = Path(__file__).parent.parent

    print("   技能目录结构:")
    for item in skill_dir.iterdir():
        if item.is_dir():
            print(f"   ├── {item.name}/")
        else:
            print(f"   ├── {item.name}")


def demo_log_example():
    """演示日志示例"""
    print("\n9. 日志示例")

    log_dir = Path(__file__).parent.parent / "logs"

    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            print(f"   找到 {len(log_files)} 个日志文件:")
            for log_file in log_files[:3]:  # 显示前3个
                print(f"   - {log_file.name}")
        else:
            print("   日志目录存在但无日志文件")
    else:
        print("   日志目录不存在（将在首次运行时创建）")


def main():
    """主函数"""
    demo_basic_usage()
    demo_config_check()
    demo_file_structure()
    demo_log_example()

    print("\n" + "=" * 40)
    print("演示完成!")
    print("\n下一步:")
    print("1. 确保有测试微信号")
    print("2. 准备 .env 配置文件")
    print("3. 运行: python scripts/wechat_bot.py")
    print("4. 扫描二维码登录")


if __name__ == "__main__":
    main()
