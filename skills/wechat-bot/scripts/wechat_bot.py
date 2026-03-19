#!/usr/bin/env python3
"""
微信机器人 - 基于wxpy的个人微信自动化工具
支持消息收发、自动回复、文件传输和数据收集功能
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from wxpy import *
except ImportError:
    print("请先安装wxpy库: pip install wxpy")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    print("警告: 未安装python-dotenv，将使用系统环境变量")

    def load_dotenv():
        pass


class WeChatBot:
    """微信机器人主类"""

    def __init__(self, config_path: Optional[str] = None):
        """初始化机器人"""
        # 加载环境变量
        load_dotenv(config_path)

        # 配置日志
        self.setup_logging()

        # 初始化机器人
        self.bot = None
        self.running = False
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.config = self.load_config()

        # 存储会话数据
        self.sessions: Dict[str, Dict] = {}
        self.load_sessions()

        self.logger.info("微信机器人初始化完成")

    def setup_logging(self):
        """配置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_file = (
            log_dir / f"wechat_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
        )
        self.logger = logging.getLogger("WeChatBot")

    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "auto_reply": os.getenv("AUTO_REPLY", "false").lower() == "true",
            "reply_message": os.getenv("REPLY_MESSAGE", "收到消息，稍后回复"),
            "collect_messages": os.getenv("COLLECT_MESSAGES", "true").lower() == "true",
            "save_media": os.getenv("SAVE_MEDIA", "true").lower() == "true",
            "group_filter": os.getenv("GROUP_FILTER", "").split(",")
            if os.getenv("GROUP_FILTER")
            else [],
            "contact_filter": os.getenv("CONTACT_FILTER", "").split(",")
            if os.getenv("CONTACT_FILTER")
            else [],
        }

        self.logger.info(f"配置加载完成: {default_config}")
        return default_config

    def load_sessions(self):
        """加载会话数据"""
        session_file = self.data_dir / "sessions.json"
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    self.sessions = json.load(f)
                self.logger.info(f"加载 {len(self.sessions)} 个会话")
            except Exception as e:
                self.logger.error(f"加载会话失败: {e}")

    def save_sessions(self):
        """保存会话数据"""
        session_file = self.data_dir / "sessions.json"
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存会话失败: {e}")

    def start(self):
        """启动机器人"""
        try:
            self.logger.info("正在启动微信机器人...")

            # 登录微信
            self.bot = Bot(
                cache_path=True,
                console_qr=True,
                qr_callback=self.on_qr_code,
                login_callback=self.on_login,
                logout_callback=self.on_logout,
            )

            # 注册消息处理器
            self.register_handlers()

            self.running = True
            self.logger.info("微信机器人启动成功")

            # 保持运行
            while self.running:
                time.sleep(1)

        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            raise

    def on_qr_code(self, uuid, status, qrcode):
        """二维码回调"""
        self.logger.info(f"请扫描二维码登录 (状态: {status})")

    def on_login(self):
        """登录回调"""
        self.logger.info("登录成功")
        self.save_sessions()

    def on_logout(self):
        """登出回调"""
        self.logger.info("已登出")
        self.running = False
        self.save_sessions()

    def register_handlers(self):
        """注册消息处理器"""

        @self.bot.register(msg_types=TEXT)
        def on_text_message(msg):
            """处理文本消息"""
            self.handle_message(msg)

        @self.bot.register(msg_types=PICTURE)
        def on_picture_message(msg):
            """处理图片消息"""
            self.handle_media_message(msg, "picture")

        @self.bot.register(msg_types=RECORDING)
        def on_recording_message(msg):
            """处理语音消息"""
            self.handle_media_message(msg, "recording")

        @self.bot.register(msg_types=VIDEO)
        def on_video_message(msg):
            """处理视频消息"""
            self.handle_media_message(msg, "video")

        @self.bot.register(msg_types=ATTACHMENT)
        def on_attachment_message(msg):
            """处理文件消息"""
            self.handle_media_message(msg, "attachment")

        self.logger.info("消息处理器注册完成")

    def handle_message(self, msg):
        """处理文本消息"""
        try:
            sender = msg.sender
            sender_name = self.get_sender_name(sender)
            content = msg.text

            self.logger.info(f"收到来自 {sender_name} 的消息: {content}")

            # 记录消息
            if self.config["collect_messages"]:
                self.record_message(sender_name, "text", content)

            # 自动回复
            if self.config["auto_reply"] and not msg.is_to_me:
                self.send_reply(sender, content)

            # 处理特殊命令
            self.handle_command(msg, content)

        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")

    def handle_media_message(self, msg, media_type: str):
        """处理媒体消息"""
        try:
            sender = msg.sender
            sender_name = self.get_sender_name(sender)

            self.logger.info(f"收到来自 {sender_name} 的{media_type}消息")

            # 保存媒体文件
            if self.config["save_media"]:
                self.save_media_file(msg, media_type, sender_name)

            # 记录消息
            if self.config["collect_messages"]:
                self.record_message(sender_name, media_type, f"[{media_type}]")

        except Exception as e:
            self.logger.error(f"处理媒体消息失败: {e}")

    def get_sender_name(self, sender) -> str:
        """获取发送者名称"""
        try:
            if hasattr(sender, "name"):
                return sender.name
            elif hasattr(sender, "nick_name"):
                return sender.nick_name
            else:
                return str(sender)
        except:
            return "未知用户"

    def record_message(self, sender: str, msg_type: str, content: str):
        """记录消息到文件"""
        try:
            timestamp = datetime.now().isoformat()
            record = {
                "timestamp": timestamp,
                "sender": sender,
                "type": msg_type,
                "content": content,
            }

            # 保存到当日文件
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.data_dir / f"messages_{today}.json"

            # 读取现有数据
            messages = []
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    messages = json.load(f)

            # 添加新记录
            messages.append(record)

            # 保存
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"记录消息失败: {e}")

    def save_media_file(self, msg, media_type: str, sender: str):
        """保存媒体文件"""
        try:
            # 创建媒体目录
            media_dir = self.data_dir / "media" / media_type
            media_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_sender = "".join(
                c for c in sender if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            filename = f"{timestamp}_{safe_sender}_{media_type}"

            # 根据类型保存
            if media_type == "picture":
                msg.get_file(save_path=str(media_dir / f"{filename}.jpg"))
            elif media_type == "recording":
                msg.get_file(save_path=str(media_dir / f"{filename}.mp3"))
            elif media_type == "video":
                msg.get_file(save_path=str(media_dir / f"{filename}.mp4"))
            elif media_type == "attachment":
                msg.get_file(save_path=str(media_dir / filename))

            self.logger.info(f"媒体文件已保存: {filename}")

        except Exception as e:
            self.logger.error(f"保存媒体文件失败: {e}")

    def send_reply(self, sender, original_content: str):
        """发送自动回复"""
        try:
            reply_message = self.config["reply_message"]
            sender.send(reply_message)
            self.logger.info(f"已回复 {self.get_sender_name(sender)}: {reply_message}")
        except Exception as e:
            self.logger.error(f"发送回复失败: {e}")

    def handle_command(self, msg, content: str):
        """处理特殊命令"""
        if content.startswith("/"):
            command = content[1:].split()[0].lower()

            if command == "help":
                self.send_help(msg.sender)
            elif command == "status":
                self.send_status(msg.sender)
            elif command == "stats":
                self.send_stats(msg.sender)
            elif command == "export":
                self.export_data(msg.sender)

    def send_help(self, sender):
        """发送帮助信息"""
        help_text = """微信机器人命令帮助：
/help - 显示此帮助信息
/status - 显示机器人状态
/stats - 显示消息统计
/export - 导出收集的数据"""
        sender.send(help_text)

    def send_status(self, sender):
        """发送状态信息"""
        status_text = f"""机器人状态：
运行状态: {"运行中" if self.running else "已停止"}
会话数量: {len(self.sessions)}
数据目录: {self.data_dir.absolute()}"""
        sender.send(status_text)

    def send_stats(self, sender):
        """发送统计信息"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = self.data_dir / f"messages_{today}.json"

            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    messages = json.load(f)

                stats = {"total": len(messages), "by_type": {}, "by_sender": {}}

                for msg in messages:
                    # 按类型统计
                    msg_type = msg.get("type", "unknown")
                    stats["by_type"][msg_type] = stats["by_type"].get(msg_type, 0) + 1

                    # 按发送者统计
                    sender_name = msg.get("sender", "unknown")
                    stats["by_sender"][sender_name] = (
                        stats["by_sender"].get(sender_name, 0) + 1
                    )

                stats_text = f"今日消息统计 ({today})：\n"
                stats_text += f"总计: {stats['total']} 条\n"
                stats_text += "按类型:\n"
                for msg_type, count in stats["by_type"].items():
                    stats_text += f"  {msg_type}: {count}\n"

                sender.send(stats_text)
            else:
                sender.send(f"今日 ({today}) 暂无消息记录")

        except Exception as e:
            self.logger.error(f"发送统计失败: {e}")
            sender.send("获取统计信息失败")

    def export_data(self, sender):
        """导出数据"""
        try:
            export_dir = self.data_dir / "export"
            export_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_file = export_dir / f"export_{timestamp}.json"

            # 收集所有数据
            export_data = {
                "export_time": datetime.now().isoformat(),
                "sessions": self.sessions,
                "messages": {},
            }

            # 读取所有消息文件
            for msg_file in self.data_dir.glob("messages_*.json"):
                date = msg_file.stem.replace("messages_", "")
                with open(msg_file, "r", encoding="utf-8") as f:
                    export_data["messages"][date] = json.load(f)

            # 保存导出文件
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            sender.send(f"数据已导出到: {export_file}")

        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            sender.send("导出数据失败")

    def send_message(self, to: str, message: str):
        """发送消息"""
        try:
            # 查找联系人
            contact = self.bot.friends().search(to)
            if contact:
                contact[0].send(message)
                self.logger.info(f"已发送消息给 {to}: {message}")
                return True
            else:
                self.logger.error(f"未找到联系人: {to}")
                return False
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            return False

    def stop(self):
        """停止机器人"""
        self.running = False
        self.save_sessions()
        if self.bot:
            self.bot.logout()
        self.logger.info("微信机器人已停止")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="微信机器人")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--test", action="store_true", help="测试模式")

    args = parser.parse_args()

    try:
        # 创建并启动机器人
        bot = WeChatBot(config_path=args.config)

        if args.test:
            print("测试模式 - 机器人已初始化但未启动")
            print("配置信息:", bot.config)
            return

        bot.start()

    except KeyboardInterrupt:
        print("\n收到中断信号，正在停止...")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
