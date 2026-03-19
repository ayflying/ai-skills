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
        """
        获取网站列表
        :param page: 当前页码
        :param limit: 每页显示的记录数
        """
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
        """
        创建新网站
        :param webname: 网站域名
        :param path: 网站根目录路径
        :param type: 网站类型 (默认 PHP)
        :param version: PHP版本 (00为静态)
        :param port: 端口号
        :param ps: 备注信息
        :param ftp: 是否创建FTP
        :param sql: 是否创建数据库
        """
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
        """
        删除网站
        :param site_id: 网站ID
        :param webname: 网站主域名
        """
        return self.request(
            "/site?action=DeleteSite", {"id": site_id, "webname": webname}
        )

    def set_site_status(self, site_id, webname, status):
        """
        设置网站状态
        :param site_id: 网站ID
        :param webname: 网站主域名
        :param status: 0表示停止, 1表示启动
        """
        action = "SiteStop" if status == 0 else "SiteStart"
        return self.request(
            f"/site?action={action}", {"id": site_id, "webname": webname}
        )

    def set_php_version(self, webname, version):
        """
        修改网站使用的PHP版本
        :param webname: 网站域名
        :param version: PHP版本号 (如 74, 80)
        """
        return self.request(
            "/site?action=SetPHPVersion", {"siteName": webname, "version": version}
        )

    def apply_let_ssl(self, domain, site_id, auth_type="http", auth_to=None):
        """
        申请 Let's Encrypt 免费证书
        :param domain: 域名
        :param site_id: 网站ID
        :param auth_type: 验证类型 (http/dns)
        """
        params = {
            "domains": json.dumps([domain]),
            "id": site_id,
            "auth_type": auth_type,
            "auth_to": auth_to if auth_to else domain,
        }
        return self.request("/ssl?action=ApplyLetSSL", params)

    # --- Docker Management ---
    def get_docker_containers(self):
        """获取所有 Docker 容器列表"""
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

    def operate_docker_container(self, container_id, action):
        """
        操作 Docker 容器 (start/stop/restart/remove)
        """
        return self.request(
            "/project/docker/model",
            {
                "url": "unix:///var/run/docker.sock",
                "dk_model_name": "container",
                "dk_def_name": action,
                "container_id": container_id,
            },
        )

    def get_docker_logs(self, container_id):
        """获取 Docker 容器日志 (优先使用 API, 失败则回退到 Shell)"""
        result = self.request(
            "/project/docker/model",
            {
                "url": "unix:///var/run/docker.sock",
                "dk_model_name": "container",
                "dk_def_name": "get_logs",
                "container_id": container_id,
            },
        )
        if result and result.get("status") is False:
            # Fallback to shell if API fails
            return self.exec_shell(f"docker logs --tail 100 {container_id}")
        return result

    # --- Docker Compose Management ---
    def docker_compose_cmd(self, path, command):
        """
        通过 ExecShell 稳健执行 Docker Compose 命令
        :param path: docker-compose.yml 所在目录
        :param command: 指令 (如 up -d, down, restart)
        """
        full_cmd = f"cd {path} && docker-compose {command}"
        return self.exec_shell(full_cmd)

    # --- Database Management ---
    def get_databases(self, page=1, limit=20):
        """
        获取数据库列表
        :param page: 页码
        :param limit: 每页数量
        """
        return self.request(
            "/data?action=getData&table=databases", {"p": page, "limit": limit}
        )

    def create_database(self, name, username, password, db_type="MySQL", ps=""):
        """
        创建数据库
        """
        return self.request(
            "/database?action=AddDatabase",
            {
                "name": name,
                "db_user": username,
                "password": password,
                "address": "127.0.0.1",
                "type": db_type,
                "ps": ps,
            },
        )

    def delete_database(self, db_id, name):
        """
        删除数据库
        """
        return self.request(
            "/database?action=DeleteDatabase", {"id": db_id, "name": name}
        )

    def set_database_password(self, db_id, name, password):
        """
        修改数据库密码
        """
        return self.request(
            "/database?action=ResDatabasePassword",
            {"id": db_id, "name": name, "password": password},
        )

    def get_database_logs(self):
        """获取数据库错误日志"""
        return self.request("/database?action=GetDbErrorLog")

    # --- Software Management ---
    def install_software(self, s_name, version):
        """
        安装软件
        """
        return self.request(
            "/plugin?action=install_plugin", {"s_name": s_name, "version": version}
        )

    def uninstall_software(self, s_name, version):
        """
        卸载软件
        """
        return self.request(
            "/plugin?action=un_install_plugin", {"s_name": s_name, "version": version}
        )

    def update_software(self, s_name, version):
        """
        更新软件
        """
        return self.request(
            "/plugin?action=update_plugin", {"s_name": s_name, "version": version}
        )

    # --- Security & Firewall ---
    def get_firewall_list(self, page=1, limit=20):
        """获取防火墙规则列表"""
        return self.request("/firewall?action=GetList", {"p": page, "limit": limit})

    def add_firewall_rule(self, port, ps, protocol="tcp"):
        """添加防火墙规则"""
        return self.request(
            "/firewall?action=AddAcceptPort",
            {"port": port, "ps": ps, "protocol": protocol},
        )

    def delete_firewall_rule(self, rule_id, port):
        """删除防火墙规则"""
        return self.request(
            "/firewall?action=DelAcceptPort", {"id": rule_id, "port": port}
        )

    def get_ssh_status(self):
        """获取 SSH 状态"""
        return self.request("/firewall?action=GetSSHStatus")

    def set_ssh_status(self, status):
        """设置 SSH 状态 (0: 关闭, 1: 开启)"""
        action = "CloseSSH" if status == 0 else "OpenSSH"
        return self.request(f"/firewall?action={action}")

    # --- Logs ---
    def get_panel_logs(self, page=1, limit=20):
        """获取面板操作日志"""
        return self.request("/config?action=get_logs", {"p": page, "limit": limit})

    def get_site_logs(self, site_name):
        """获取网站运行日志"""
        return self.request("/site?action=GetSiteLogs", {"siteName": site_name})

    # --- File Management ---
    def get_files(self, path):
        """
        获取指定目录的文件和文件夹列表
        :param path: 服务器绝对路径
        """
        return self.request("/files?action=GetDir", {"path": path})

    def create_dir(self, path):
        """
        创建新目录
        :param path: 绝对路径
        """
        return self.request("/files?action=CreateDir", {"path": path})

    def compress_file(self, s_path, d_path, type="zip"):
        """
        压缩文件/目录
        """
        return self.request(
            "/files?action=Zip", {"sfile": s_path, "dfile": d_path, "type": type}
        )

    def decompress_file(self, s_path, d_path, password=""):
        """
        解压文件
        """
        return self.request(
            "/files?action=UnZip",
            {"sfile": s_path, "dfile": d_path, "password": password},
        )

    def get_recycle_bin(self):
        """
        查看回收站内容
        """
        return self.request("/files?action=GetRecycleBin")

    def restore_recycle_bin(self, path):
        """
        从回收站恢复
        """
        return self.request("/files?action=ReFile", {"path": path})

    def empty_recycle_bin(self):
        """
        清空回收站
        """
        return self.request("/files?action=CloseRecycleBin")

    def get_file_logs(self):
        """获取文件操作日志"""
        return self.request("/config?action=get_logs", {"search": "文件"})

    def write_file(self, path, content):
        """
        写入文件内容 (覆盖)
        :param path: 绝对路径
        :param content: 文件内容
        """
        # Try the WriteFile action which might be more appropriate for new files
        import base64

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        return self.request(
            "/files?action=WriteFile", {"path": path, "data": encoded_content}
        )

    def get_file_content(self, path):
        """
        读取服务器文件内容
        :param path: 绝对路径
        """
        return self.request("/files?action=GetFileBody", {"path": path})

    def download_file(self, remote_path, local_path):
        """
        下载服务器文件到本地路径
        :param remote_path: 服务器绝对路径
        :param local_path: 本地保存路径
        """
        result = self.get_file_content(remote_path)
        if result and result.get("status") is not False:
            content = result.get("data", "")
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": True, "msg": f"File downloaded to {local_path}"}
        return result

    def upload_file(self, local_path, remote_path):
        """
        上传本地文件到服务器指定路径
        :param local_path: 本地文件路径
        :param remote_path: 服务器保存绝对路径
        """
        if not os.path.exists(local_path):
            return {"status": False, "msg": f"Local file {local_path} not found"}

        with open(local_path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.write_file(remote_path, content)

    def exec_shell(self, command):
        """
        在服务器执行 shell 命令
        :param command: shell 指令
        """
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
    elif action == "docker_logs":
        if not args:
            print(
                json.dumps(
                    {"status": False, "msg": "Usage: docker_logs <container_id>"}
                )
            )
        else:
            print(json.dumps(api.get_docker_logs(args[0]), indent=2))
    elif action == "compose":
        if len(args) < 2:
            print(
                json.dumps({"status": False, "msg": "Usage: compose <path> <command>"})
            )
        else:
            print(
                json.dumps(
                    api.docker_compose_cmd(args[0], " ".join(args[1:])), indent=2
                )
            )
    elif action == "compose_logs":
        if not args:
            print(json.dumps({"status": False, "msg": "Usage: compose_logs <path>"}))
        else:
            print(
                json.dumps(api.docker_compose_cmd(args[0], "logs --tail 100"), indent=2)
            )
    elif action == "databases":
        print(json.dumps(api.get_databases(), indent=2))
    elif action == "add_db":
        if len(args) < 3:
            print(
                json.dumps(
                    {"status": False, "msg": "Usage: add_db <name> <user> <pass>"}
                )
            )
        else:
            print(json.dumps(api.create_database(args[0], args[1], args[2]), indent=2))
    elif action == "del_db":
        if len(args) < 2:
            print(json.dumps({"status": False, "msg": "Usage: del_db <id> <name>"}))
        else:
            print(json.dumps(api.delete_database(args[0], args[1]), indent=2))
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
    elif action == "download":
        if len(args) < 2:
            print(
                json.dumps(
                    {
                        "status": False,
                        "msg": "Usage: download <remote_path> <local_path>",
                    }
                )
            )
        else:
            print(json.dumps(api.download_file(args[0], args[1]), indent=2))
    elif action == "zip":
        if len(args) < 2:
            print(json.dumps({"status": False, "msg": "Usage: zip <src> <dst>"}))
        else:
            print(json.dumps(api.compress_file(args[0], args[1]), indent=2))
    elif action == "unzip":
        if len(args) < 2:
            print(json.dumps({"status": False, "msg": "Usage: unzip <src> <dst>"}))
        else:
            print(json.dumps(api.decompress_file(args[0], args[1]), indent=2))
    elif action == "recycle":
        print(json.dumps(api.get_recycle_bin(), indent=2))
    elif action == "empty_recycle":
        print(json.dumps(api.empty_recycle_bin(), indent=2))
    elif action == "ssl":
        if len(args) < 2:
            print(json.dumps({"status": False, "msg": "Usage: ssl <domain> <site_id>"}))
        else:
            print(json.dumps(api.apply_let_ssl(args[0], args[1]), indent=2))
    elif action == "plugins":
        print(json.dumps(api.get_plugins(), indent=2))
    elif action == "install":
        if len(args) < 2:
            print(
                json.dumps({"status": False, "msg": "Usage: install <name> <version>"})
            )
        else:
            print(json.dumps(api.install_software(args[0], args[1]), indent=2))
    elif action == "update_soft":
        if len(args) < 2:
            print(
                json.dumps(
                    {"status": False, "msg": "Usage: update_soft <name> <version>"}
                )
            )
        else:
            print(json.dumps(api.update_software(args[0], args[1]), indent=2))
    elif action == "firewall":
        print(json.dumps(api.get_firewall_list(), indent=2))
    elif action == "logs":
        print(json.dumps(api.get_panel_logs(), indent=2))
    elif action == "exec_shell":
        command = " ".join(args) if args else "echo hello"
        print(json.dumps(api.exec_shell(command), indent=2))
    else:
        print(json.dumps({"status": False, "msg": f"Unknown action: {action}"}))
