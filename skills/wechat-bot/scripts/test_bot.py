#!/usr/bin/env python3
"""
微信机器人测试脚本
用于测试基本功能而不实际连接微信
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """测试导入"""
    print("测试导入...")

    try:
        import wxpy

        print("[OK] wxpy 导入成功")
    except ImportError:
        print("[FAIL] wxpy 导入失败，请安装: pip install wxpy")
        return False

    try:
        from dotenv import load_dotenv

        print("[OK] python-dotenv 导入成功")
    except ImportError:
        print("[FAIL] python-dotenv 导入失败，请安装: pip install python-dotenv")
        return False

    return True


def test_config():
    """测试配置加载"""
    print("\n测试配置加载...")

    # 设置测试环境变量
    os.environ["AUTO_REPLY"] = "true"
    os.environ["REPLY_MESSAGE"] = "测试回复消息"
    os.environ["COLLECT_MESSAGES"] = "true"

    # 导入并创建机器人实例（不启动）
    from wechat_bot import WeChatBot

    try:
        bot = WeChatBot()
        print("[OK] 机器人初始化成功")
        print(f"  配置: {bot.config}")
        return True
    except Exception as e:
        print(f"[FAIL] 机器人初始化失败: {e}")
        return False


def test_data_dirs():
    """测试数据目录创建"""
    print("\n测试数据目录...")

    from wechat_bot import WeChatBot

    try:
        bot = WeChatBot()

        # 检查目录是否创建
        if bot.data_dir.exists():
            print(f"[OK] 数据目录存在: {bot.data_dir}")
        else:
            print(f"[FAIL] 数据目录不存在: {bot.data_dir}")
            return False

        return True
    except Exception as e:
        print(f"[FAIL] 目录测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("微信机器人测试")
    print("=" * 40)

    tests = [test_imports, test_config, test_data_dirs]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 40)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("\n所有测试通过！可以运行主程序:")
        print("  python scripts/wechat_bot.py")
        return 0
    else:
        print("\n部分测试失败，请检查依赖和配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
