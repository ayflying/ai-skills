import os
import re
import shutil
import sys

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def substitute_env_vars(content, env_map):
    """将文本中的 ${VAR_NAME} 替换为环境变量值"""

    def replacer(match):
        var_name = match.group(1)
        return env_map.get(var_name, match.group(0))  # 未找到则保留原样

    return re.sub(r"\$\{(\w+)\}", replacer, content)


def setup_multi_agent():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(os.path.dirname(script_dir))
    skill_agents_dir = os.path.join(skill_root, ".opencode", "agents")

    # 获取当前工作区根目录
    project_root = os.getcwd()
    while project_root != os.path.dirname(project_root):
        if os.path.exists(os.path.join(project_root, ".git")):
            break
        project_root = os.path.dirname(project_root)

    target_agents_dir = os.path.join(project_root, ".opencode", "agents")
    target_env = os.path.join(project_root, ".env")

    print(f"[*] 正在初始化 Multi-Agent 协作环境...")
    print(f"[*] 目标目录: {target_agents_dir}")

    if not os.path.exists(skill_agents_dir):
        print(f"[!] 错误: 未找到源代理配置目录 {skill_agents_dir}")
        sys.exit(1)

    if not os.path.exists(target_agents_dir):
        os.makedirs(target_agents_dir)
        print(f"[*] 已创建目标目录: {target_agents_dir}")

    # 加载 .env 文件（如果存在）
    env_map = {}
    if os.path.exists(target_env):
        if load_dotenv:
            load_dotenv(target_env)
        print("[*] 已加载 .env 配置")

    # 收集所有环境变量
    for key, val in os.environ.items():
        if key.endswith("_NAME"):
            env_map[key] = val

    # 复制并替换所有 .md 配置文件
    for filename in os.listdir(skill_agents_dir):
        if filename.endswith(".md"):
            src_file = os.path.join(skill_agents_dir, filename)
            dst_file = os.path.join(target_agents_dir, filename)

            with open(src_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 替换占位符
            if env_map:
                content = substitute_env_vars(content, env_map)

            # 直接覆盖已存在的文件
            with open(dst_file, "w", encoding="utf-8") as f:
                f.write(content)

            action = "覆盖" if os.path.exists(dst_file) else "创建"
            print(f"    - {action}: {filename}")

    # 复制 .env.example 为 .env（如果目标项目没有 .env）
    env_example = os.path.join(skill_root, ".env.example")
    if os.path.exists(env_example) and not os.path.exists(target_env):
        shutil.copy2(env_example, target_env)
        print(f"    - 已创建: .env（请编辑此文件自定义代理名称后重新运行 setup.py）")

    print("\n[✔] 初始化完成！")
    if not env_map:
        print("    提示：编辑 .env 自定义代理名称后，重新运行 setup.py 即可生效。")


if __name__ == "__main__":
    setup_multi_agent()
