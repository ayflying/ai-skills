import os
import shutil
import sys


def setup_multi_agent():
    # 获取脚本所在目录（技能安装后位于 .agents/skills/multi-agent/scripts/）
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 技能安装目录结构：.agents/skills/multi-agent/scripts/setup.py
    # 因此向上两级得到技能根目录：.agents/skills/multi-agent/
    skill_root = os.path.dirname(os.path.dirname(script_dir))
    skill_agents_dir = os.path.join(skill_root, ".opencode", "agents")

    # 获取当前工作区根目录 (向上查找直到找到 .git 目录或到达根目录)
    project_root = os.getcwd()
    while project_root != os.path.dirname(project_root):
        if os.path.exists(os.path.join(project_root, ".git")):
            break
        project_root = os.path.dirname(project_root)

    target_agents_dir = os.path.join(project_root, ".opencode", "agents")

    print(f"[*] 正在初始化 Multi-Agent 协作环境...")
    print(f"[*] 源目录: {skill_agents_dir}")
    print(f"[*] 目标目录: {target_agents_dir}")

    if not os.path.exists(skill_agents_dir):
        print(f"[!] 错误: 未找到源代理配置目录 {skill_agents_dir}")
        sys.exit(1)

    if not os.path.exists(target_agents_dir):
        os.makedirs(target_agents_dir)
        print(f"[*] 已创建目标目录: {target_agents_dir}")

    # 复制所有 .md 配置文件
    for filename in os.listdir(skill_agents_dir):
        if filename.endswith(".md"):
            src_file = os.path.join(skill_agents_dir, filename)
            dst_file = os.path.join(target_agents_dir, filename)
            shutil.copy2(src_file, dst_file)
            print(f"    - 已部署: {filename}")

    print("\n[✔] 初始化完成！请刷新 OpenCode 或按 Tab 键查看新的代理身份。")


if __name__ == "__main__":
    setup_multi_agent()
