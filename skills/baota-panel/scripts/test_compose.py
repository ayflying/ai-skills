import os
import json
import time
from bt_api import BTPanelAPI


def test_docker_compose_flow():
    # 1. 初始化 API (确保已配置环境变量或 .env)
    panel_url = os.getenv("BT_PANEL_URL", "https://192.168.50.243:8888")
    api_key = os.getenv("BT_API_KEY")

    if not api_key:
        print("错误: 请先设置 BT_API_KEY 环境变量")
        return

    api = BTPanelAPI(panel_url, api_key)

    test_dir = "/www/wwwroot/ai_debug_compose"
    yaml_path = f"{test_dir}/docker-compose.yml"

    print(f"--- 1. 创建调试目录: {test_dir} ---")
    print(api.create_dir(test_dir))

    print("\n--- 2. 写入测试 docker-compose.yml ---")
    compose_content = """
version: '3'
services:
  hello-world:
    image: nginx:alpine
    container_name: ai-test-nginx
    ports:
      - "8081:80"
"""
    print(api.write_file(yaml_path, compose_content))

    print("\n--- 3. 启动容器编排 (稳健模式) ---")
    # 使用新增的 docker_compose_cmd 方法
    print(api.docker_compose_cmd(test_dir, "up -d"))

    print("\n--- 4. 等待容器启动并查看日志 ---")
    time.sleep(5)
    print(api.docker_compose_cmd(test_dir, "logs --tail 20"))

    print("\n--- 5. 查看容器列表确认 ---")
    print(json.dumps(api.get_docker_containers(), indent=2))

    print("\n--- 6. 清理测试环境 (down) ---")
    print(api.docker_compose_cmd(test_dir, "down"))

    print("\n--- 7. 删除调试目录 ---")
    # 注意：删除操作需要用户确定，此处作为测试脚本演示流程
    print(api.exec_shell(f"rm -rf {test_dir}"))


if __name__ == "__main__":
    test_docker_compose_flow()
