#!/usr/bin/env python3
"""
微信机器人实际运行测试脚本
引导用户进行完整的功能测试
"""

import os
import sys
import time
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))


def print_header():
    """打印标题"""
    print("=" * 60)
    print("        微信机器人实际运行测试")
    print("=" * 60)


def print_warning():
    """打印警告信息"""
    print("\n" + "=" * 60)
    print("                    重要警告")
    print("=" * 60)
    print("[!] 风险提示:")
    print("   1. 个人微信自动化可能违反微信使用条款")
    print("   2. 可能导致账号被限制或封禁")
    print("   3. 网页版微信功能有限，部分功能不可用")
    print("\n[!] 建议:")
    print("   1. 务必使用【测试专用微信号】")
    print("   2. 不要使用主力账号或重要账号")
    print("   3. 测试完成后及时退出登录")
    print("   4. 仅用于合法的自动化需求")
    print("=" * 60)


def check_prerequisites():
    """检查前置条件"""
    print("\n1. 检查前置条件...")

    # 检查Python版本
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 10:
        print(
            f"   [OK] Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
    else:
        print(
            f"   [FAIL] Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
        print("         需要 Python 3.10+")
        return False

    # 检查依赖
    try:
        import wxpy

        print("   [OK] wxpy库已安装")
    except ImportError:
        print("   [FAIL] wxpy库未安装")
        print("         运行: pip install wxpy python-dotenv")
        return False

    # 检查配置文件
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print("   [OK] .env配置文件存在")
    else:
        print("   [INFO] .env配置文件不存在，将使用默认配置")
        print("         建议创建 .env 文件配置参数")

    return True


def check_test_account():
    """检查测试账号准备"""
    print("\n2. 测试账号准备...")

    print("   请确认以下事项:")
    print("   ✓ 准备了专门的测试微信号")
    print("   ✓ 该账号可以正常登录网页版微信")
    print("   ✓ 不是主力账号或重要账号")
    print("   ✓ 了解可能存在的风险")

    response = input("\n   是否已准备好测试账号？(yes/no): ").strip().lower()
    return response in ["yes", "y", "是"]


def run_basic_tests():
    """运行基础测试"""
    print("\n3. 运行基础测试...")

    try:
        from wechat_bot import WeChatBot

        # 创建机器人实例
        bot = WeChatBot()
        print("   [OK] 机器人初始化成功")
        print(f"   [INFO] 数据目录: {bot.data_dir.absolute()}")
        print(f"   [INFO] 日志目录: logs/")

        # 检查配置
        config = bot.config
        print("   [INFO] 当前配置:")
        print(f"     - 自动回复: {config['auto_reply']}")
        print(f"     - 收集消息: {config['collect_messages']}")
        print(f"     - 保存媒体: {config['save_media']}")

        return True

    except Exception as e:
        print(f"   [FAIL] 基础测试失败: {e}")
        return False


def start_wechat_bot():
    """启动微信机器人"""
    print("\n4. 启动微信机器人...")
    print("   即将启动机器人，启动后会显示二维码")
    print("   请使用测试微信账号扫描二维码登录")

    response = input("\n   是否继续启动？(yes/no): ").strip().lower()
    if response not in ["yes", "y", "是"]:
        print("   [INFO] 用户取消启动")
        return

    try:
        from wechat_bot import WeChatBot

        print("\n   正在启动机器人...")
        print("   请稍候，等待二维码显示...")

        # 创建并启动机器人
        bot = WeChatBot()
        bot.start()

    except KeyboardInterrupt:
        print("\n\n   [INFO] 收到中断信号，正在停止...")
    except Exception as e:
        print(f"\n   [ERROR] 启动失败: {e}")

        # 提供故障排除建议
        print("\n   故障排除建议:")
        print("   1. 检查网络连接")
        print("   2. 确认微信账号正常")
        print("   3. 检查是否安装了所有依赖")
        print("   4. 尝试使用其他终端")


def print_test_guide():
    """打印测试指南"""
    print("\n5. 功能测试指南...")
    print("   登录成功后，请按以下步骤测试:")

    print("\n   A. 消息收发测试:")
    print("      1. 用另一个微信账号向机器人发送文本消息")
    print("      2. 检查机器人是否收到消息")
    print("      3. 检查是否收到自动回复（如果启用）")

    print("\n   B. 命令测试:")
    print("      发送以下命令测试:")
    print("      - /help    - 显示帮助信息")
    print("      - /status  - 显示机器人状态")
    print("      - /stats   - 显示消息统计")
    print("      - /export  - 导出收集的数据")

    print("\n   C. 媒体文件测试:")
    print("      1. 发送图片消息")
    print("      2. 发送语音消息")
    print("      3. 发送视频消息")
    print("      4. 发送文件")
    print("      5. 检查 data/media/ 目录是否保存")

    print("\n   D. 数据检查:")
    print("      1. 查看 data/messages_*.json 文件")
    print("      2. 查看 logs/*.log 日志文件")
    print("      3. 检查 data/sessions.json 会话数据")


def print_cleanup_instructions():
    """打印清理说明"""
    print("\n6. 测试完成清理...")
    print("   测试完成后请:")
    print("   1. 按 Ctrl+C 停止机器人")
    print("   2. 在手机微信上退出网页版登录")
    print("   3. 检查并备份重要数据")
    print("   4. 可选: 删除测试数据 (data/, logs/)")
    print("\n   清理命令:")
    print("   rm -rf data/ logs/  # Linux/Mac")
    print("   rmdir /s /q data logs  # Windows")


def main():
    """主函数"""
    print_header()

    # 显示警告
    print_warning()

    # 确认继续
    response = input("\n是否已了解风险并继续测试？(yes/no): ").strip().lower()
    if response not in ["yes", "y", "是"]:
        print("\n[INFO] 测试已取消")
        return

    # 检查前置条件
    if not check_prerequisites():
        print("\n[ERROR] 前置条件检查失败，请先解决问题")
        return

    # 检查测试账号
    if not check_test_account():
        print("\n[INFO] 请先准备好测试账号")
        return

    # 运行基础测试
    if not run_basic_tests():
        print("\n[ERROR] 基础测试失败")
        return

    # 打印测试指南
    print_test_guide()

    # 打印清理说明
    print_cleanup_instructions()

    # 启动机器人
    start_wechat_bot()


if __name__ == "__main__":
    main()
