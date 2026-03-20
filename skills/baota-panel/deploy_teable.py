import sys
import os
import json

# 添加 scripts 目录到路径
sys.path.append(os.path.join(os.getcwd(), "scripts"))
from bt_api import BTPanelAPI


def deploy():
    PANEL_URL = os.getenv("BT_PANEL_URL", "https://192.168.50.243:8888")
    API_KEY = "sGjg5lGNSAY2eEUvaedAFDxnuRlKZQM5"

    api = BTPanelAPI(PANEL_URL, API_KEY)

    yaml_content = """services:
  teable:
    image: gitea.adesk.com/esm/teable:latest
    container_name: teable
    restart: always
    ports:
      - '33000:3000'
    environment:
      - PRISMA_DATABASE_URL=postgresql://postgres:fWZM6XzXnT7tiK87@192.168.50.243:35432/teable?schema=public
      - REDIS_URL=redis://:12345678@192.168.50.243:6379/0
      - SOCIAL_AUTH_PROVIDERS=casdoor
      - BACKEND_CASDOOR_ENDPOINT=https://casdoor.adesk.com
      - BACKEND_CASDOOR_CLIENT_ID=ca462193b11167bf46f2
      - BACKEND_CASDOOR_CLIENT_SECRET=38621866ba9a916111d658872ce906ceb18c1164
      - BACKEND_CASDOOR_ORGANIZATION=sonow
      - BACKEND_CASDOOR_CALLBACK_URL=http://localhost:33000/api/auth/casdoor/callback
      - PUBLIC_ORIGIN=http://localhost:33000
      - TZ=Asia/Shanghai
      - SECRET_KEY=teable_prod_38621866ba9a916111d658872ce906ceb18c1164
    networks:
      - teable-net
    volumes:
      - teable_assets:/app/.assets

networks:
  teable-net:
    driver: bridge
    name: teable-net

volumes:
  teable_assets:
    driver: local
"""

    print("Step 1: Creating Compose Template...")
    res = api.create_compose_template(
        "teable_project", yaml_content, "Deployed via AI Model Direct"
    )
    print(f"Template Result: {res}")

    if not res.get("status"):
        print("Template creation failed or already exists. Fetching template list...")

    print("Step 2: Fetching Template ID...")
    projects = api.get_compose_projects()
    templates = projects.get("msg", {}).get("template", [])
    template_id = None
    for t in templates:
        if t["name"] == "teable_project":
            template_id = t["id"]
            break

    if not template_id:
        print("Error: Template not found.")
        return

    print(f"Using Template ID: {template_id}")

    print("Step 3: Creating and Starting Project...")
    deploy_res = api.create_compose_project(
        "teable", template_id, "Teable socket deployment"
    )
    print(f"Deploy Result: {json.dumps(deploy_res, indent=2)}")


if __name__ == "__main__":
    deploy()
