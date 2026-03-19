import hashlib
import time
import requests
import json
import os
import sys


class BTPanelAPI:
    def __init__(self, panel_url, api_key):
        self.panel_url = panel_url.rstrip("/")
        self.api_key = api_key

    def _get_token(self):
        now_time = int(time.time())
        token_str = (
            str(now_time) + hashlib.md5(self.api_key.encode("utf-8")).hexdigest()
        )
        token = hashlib.md5(token_str.encode("utf-8")).hexdigest()
        return now_time, token

    def request(self, action_path, params=None):
        if params is None:
            params = {}

        now_time, token = self._get_token()
        params["request_time"] = now_time
        params["request_token"] = token

        url = f"{self.panel_url}/{action_path.lstrip('/')}"

        try:
            # Disable SSL verification for local network IPs
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.post(url, data=params, verify=False, timeout=10)
            try:
                return response.json()
            except json.JSONDecodeError:
                return {
                    "status": False,
                    "msg": f"Invalid JSON response: {response.text[:200]}",
                }
        except Exception as e:
            return {"status": False, "msg": str(e)}

    # --- Site Management ---
    def get_sites(self, page=1, limit=20):
        return self.request(
            "/data?action=getData&table=sites", {"p": page, "limit": limit}
        )

    def create_site(
        self,
        webname,
        path,
        type="PHP",
        version="00",
        port="80",
        ps="",
        ftp="false",
        sql="false",
    ):
        params = {
            "webname": webname,
            "path": path,
            "type": type,
            "version": version,
            "port": port,
            "ps": ps,
            "ftp": ftp,
            "sql": sql,
        }
        return self.request("/site?action=AddSite", params)

    def delete_site(self, site_id, webname):
        """删除网站"""
        return self.request(
            "/site?action=DeleteSite", {"id": site_id, "webname": webname}
        )

    def set_site_status(self, site_id, webname, status):
        """设置网站状态 (0: 停止, 1: 启动)"""
        action = "SiteStop" if status == 0 else "SiteStart"
        return self.request(
            f"/site?action={action}", {"id": site_id, "webname": webname}
        )

    def set_php_version(self, webname, version):
        """修改网站 PHP 版本"""
        return self.request(
            "/site?action=SetPHPVersion", {"siteName": webname, "version": version}
        )

    def apply_let_ssl(self, domain, site_id, auth_type="http", auth_to=None):
        """申请 Let's Encrypt SSL 证书"""
        params = {
            "domains": json.dumps([domain]),
            "id": site_id,
            "auth_type": auth_type,
            "auth_to": auth_to if auth_to else domain,
        }
        return self.request("/ssl?action=ApplyLetSSL", params)

    # --- Docker Management ---
    def get_docker_containers(self):
        # Using verified path and parameters from exploration
        url = "/project/docker/model"
        params = {
            "url": "unix:///var/run/docker.sock",
            "dk_model_name": "container",
            "dk_def_name": "get_list",
        }
        result = self.request(url, params)
        if result and isinstance(result, dict) and result.get("status") is True:
            # The list is nested in msg -> container_list
            msg = result.get("msg", {})
            if isinstance(msg, dict):
                return msg.get("container_list", [])
            return msg
        return result

    # --- Database Management ---
    def get_databases(self, page=1, limit=20):
        return self.request(
            "/data?action=getData&table=databases", {"p": page, "limit": limit}
        )

    # --- File Management ---
    def get_files(self, path):
        return self.request("/files?action=GetDir", {"path": path})

    def create_dir(self, path):
        return self.request("/files?action=CreateDir", {"path": path})

    def write_file(self, path, content):
        # Try the WriteFile action which might be more appropriate for new files
        import base64

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        return self.request(
            "/files?action=WriteFile", {"path": path, "data": encoded_content}
        )

    def get_file_content(self, path):
        """读取文件内容"""
        return self.request("/files?action=GetFileBody", {"path": path})

    def download_file(self, remote_path, local_path):
        """下载远程文件到本地"""
        result = self.get_file_content(remote_path)
        if result and result.get("status") is not False:
            content = result.get("data", "")
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": True, "msg": f"File downloaded to {local_path}"}
        return result

    def upload_file(self, local_path, remote_path):
        """上传本地文件到服务器 (使用 WriteFile 方式)"""
        if not os.path.exists(local_path):
            return {"status": False, "msg": f"Local file {local_path} not found"}

        with open(local_path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.write_file(remote_path, content)

    def exec_shell(self, command):
        """执行 shell 命令"""
        return self.request("/files?action=ExecShell", {"command": command})

    # --- Docker Compose Management ---
    def add_compose_template(self, name, compose_content, env_content=""):
        """添加 Docker Compose 模板"""
        return self.request(
            "/project/docker/model",
            {
                "url": "unix:///var/run/docker.sock",
                "dk_model_name": "compose",
                "dk_def_name": "add_template",
                "name": name,
                "data": compose_content,
                "env": env_content,
            },
        )

    def get_compose_templates(self):
        """获取 Docker Compose 模板列表"""
        return self.request(
            "/project/docker/model",
            {
                "url": "unix:///var/run/docker.sock",
                "dk_model_name": "compose",
                "dk_def_name": "template_list",
            },
        )

    def create_compose_project(self, project_name, template_id):
        """使用模板创建 Docker Compose 项目"""
        return self.request(
            "/project/docker/model",
            {
                "url": "unix:///var/run/docker.sock",
                "dk_model_name": "compose",
                "dk_def_name": "create",
                "project_name": project_name,
                "template_id": template_id,
            },
        )

    def get_system_info(self):
        return self.request("/system?action=GetSystemTotal")

    def get_plugins(self):
        return self.request("/plugin?action=get_soft_list")


if __name__ == "__main__":
    # Load from environment variables
    PANEL_URL = os.getenv("BT_PANEL_URL", "https://192.168.50.243:8888")
    API_KEY = os.getenv("BT_API_KEY")

    if not API_KEY:
        # Try loading from .env file manually if not in environment
        try:
            # Check relative path to skill root
            env_path = os.path.join(os.path.dirname(__file__), "../.env")
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.split("=", 1)
                            if k.strip() == "BT_API_KEY":
                                API_KEY = v.strip().strip('"').strip("'")
                            if k.strip() == "BT_PANEL_URL":
                                PANEL_URL = v.strip().strip('"').strip("'")
        except Exception:
            pass

    if not API_KEY:
        print(
            json.dumps(
                {
                    "status": False,
                    "msg": "Error: BT_API_KEY not set in environment or .env file",
                }
            )
        )
        sys.exit(1)

    api = BTPanelAPI(PANEL_URL, API_KEY)

    if len(sys.argv) < 2:
        print(json.dumps(api.get_system_info(), indent=2))
        sys.exit(0)

    action = sys.argv[1]
    args = sys.argv[2:]

    if action == "sites":
        print(json.dumps(api.get_sites(), indent=2))
    elif action == "add_site":
        if len(args) < 2:
            print(
                json.dumps({"status": False, "msg": "Usage: add_site <domain> <path>"})
            )
        else:
            print(json.dumps(api.create_site(args[0], args[1]), indent=2))
    elif action == "del_site":
        if len(args) < 2:
            print(json.dumps({"status": False, "msg": "Usage: del_site <id> <domain>"}))
        else:
            print(json.dumps(api.delete_site(args[0], args[1]), indent=2))
    elif action == "stop_site":
        if len(args) < 2:
            print(
                json.dumps({"status": False, "msg": "Usage: stop_site <id> <domain>"})
            )
        else:
            print(json.dumps(api.set_site_status(args[0], args[1], 0), indent=2))
    elif action == "start_site":
        if len(args) < 2:
            print(
                json.dumps({"status": False, "msg": "Usage: start_site <id> <domain>"})
            )
        else:
            print(json.dumps(api.set_site_status(args[0], args[1], 1), indent=2))
    elif action == "docker":
        print(json.dumps(api.get_docker_containers(), indent=2))
    elif action == "databases":
        print(json.dumps(api.get_databases(), indent=2))
    elif action == "files":
        path = args[0] if args else "/"
        print(json.dumps(api.get_files(path), indent=2))
    elif action == "read_file":
        if not args:
            print(
                json.dumps({"status": False, "msg": "Usage: read_file <remote_path>"})
            )
        else:
            print(json.dumps(api.get_file_content(args[0]), indent=2))
    elif action == "upload":
        if len(args) < 2:
            print(
                json.dumps(
                    {"status": False, "msg": "Usage: upload <local_path> <remote_path>"}
                )
            )
        else:
            print(json.dumps(api.upload_file(args[0], args[1]), indent=2))
    elif action == "ssl":
        if len(args) < 2:
            print(json.dumps({"status": False, "msg": "Usage: ssl <domain> <site_id>"}))
        else:
            print(json.dumps(api.apply_let_ssl(args[0], args[1]), indent=2))
    elif action == "plugins":
        print(json.dumps(api.get_plugins(), indent=2))
    elif action == "exec_shell":
        command = " ".join(args) if args else "echo hello"
        print(json.dumps(api.exec_shell(command), indent=2))
    else:
        print(json.dumps({"status": False, "msg": f"Unknown action: {action}"}))
