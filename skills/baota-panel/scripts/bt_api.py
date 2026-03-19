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

        # 处理 URL 中的 action 参数
        path_parts = action_path.split("?", 1)
        base_path = path_parts[0]
        if len(path_parts) > 1:
            query_params = path_parts[1].split("&")
            for qp in query_params:
                if "=" in qp:
                    k, v = qp.split("=", 1)
                    params[k] = v

        now_time, token = self._get_token()
        params["request_time"] = now_time
        params["request_token"] = token

        url = f"{self.panel_url}/{base_path.lstrip('/')}"

        try:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            response = requests.post(url, data=params, verify=False, timeout=30)

            if not response.text:
                return {
                    "status": False,
                    "msg": "Empty response from server (possible firewall block)",
                }

            try:
                return response.json()
            except json.JSONDecodeError:
                return {
                    "status": False,
                    "msg": f"Invalid JSON response: {response.text[:100]}",
                    "raw": response.text[:500],
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
        # 包装 webname 为 JSON 格式以适配新版 API
        site_data = {"domain": webname, "domainlist": [], "count": 0}
        params = {
            "webname": json.dumps(site_data),
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
        return self.request(
            "/site?action=DeleteSite", {"id": site_id, "webname": webname}
        )

    def set_site_status(self, site_id, webname, status):
        action = "SiteStop" if status == 0 else "SiteStart"
        return self.request(
            f"/site?action={action}", {"id": site_id, "webname": webname}
        )

    def set_php_version(self, webname, version):
        return self.request(
            "/site?action=SetPHPVersion", {"siteName": webname, "version": version}
        )

    def apply_let_ssl(self, domain, site_id, auth_type="http", auth_to=None):
        params = {
            "domains": json.dumps([domain]),
            "id": site_id,
            "auth_type": auth_type,
            "auth_to": auth_to if auth_to else domain,
        }
        return self.request("/ssl?action=ApplyLetSSL", params)

    def get_site_logs(self, site_name):
        return self.request("/site?action=GetSiteLogs", {"siteName": site_name})

    def get_site_php_version(self, site_name):
        return self.request("/site?action=GetSitePHPVersion", {"siteName": site_name})

    def set_site_password(self, site_name, password):
        return self.request(
            "/site?action=SetHasPwd", {"siteName": site_name, "has_pwd": password}
        )

    def close_site_password(self, site_name):
        return self.request("/site?action=CloseHasPwd", {"siteName": site_name})

    def get_dir_user_ini(self, site_name):
        return self.request("/site?action=GetDirUserINI", {"siteName": site_name})

    def get_site_domains(self, page=1, limit=20):
        return self.request(
            "/data?action=getData&table=domain", {"p": page, "limit": limit}
        )

    def add_site_domain(self, site_name, domain, port="80"):
        return self.request(
            "/site?action=AddDomain",
            {"siteName": site_name, "domain": domain, "port": port},
        )

    def delete_site_domain(self, site_name, domain, port="80"):
        return self.request(
            "/site?action=DelDomain",
            {"siteName": site_name, "domain": domain, "port": port},
        )

    def set_security(self, site_name, status, rules=""):
        return self.request(
            "/site?action=SetSecurity",
            {"siteName": site_name, "open": status, "rules": rules},
        )

    def get_ssl_status(self, site_name):
        return self.request("/site?action=GetSSL", {"siteName": site_name})

    def set_ssl(self, site_name, cert_data, key_data):
        return self.request(
            "/site?action=SetSSL",
            {"siteName": site_name, "cert": cert_data, "key": key_data},
        )

    def http_to_https(self, site_name):
        return self.request("/site?action=HttpToHttps", {"siteName": site_name})

    def close_https(self, site_name):
        return self.request("/site?action=CloseToHttps", {"siteName": site_name})

    def get_site_index(self, site_name):
        return self.request("/site?action=GetIndex", {"siteName": site_name})

    def set_site_index(self, site_name, index_files):
        return self.request(
            "/site?action=SetIndex", {"siteName": site_name, "index": index_files}
        )

    def get_rewrite_list(self, site_name):
        return self.request("/site?action=GetRewriteList", {"siteName": site_name})

    def get_limit_net(self, site_name):
        return self.request("/site?action=GetLimitNet", {"siteName": site_name})

    def set_limit_net(self, site_name, port="limit"):
        return self.request(
            "/site?action=SetLimitNet", {"siteName": site_name, "port": port}
        )

    def close_limit_net(self, site_name):
        return self.request("/site?action=CloseLimitNet", {"siteName": site_name})

    def get_301_status(self, site_name):
        return self.request("/site?action=Get301Status", {"siteName": site_name})

    def set_301_status(self, site_name, to_domain, open="true"):
        return self.request(
            "/site?action=Set301Status",
            {"siteName": site_name, "toDomain": to_domain, "open": open},
        )

    # --- FTP Management ---
    def get_ftp_list(self, page=1, limit=20):
        return self.request(
            "/data?action=getData&table=ftps", {"p": page, "limit": limit}
        )

    def set_ftp_password(self, ftp_user, password):
        return self.request(
            "/ftp?action=SetUserPassword", {"ftp_user": ftp_user, "password": password}
        )

    def set_ftp_status(self, ftp_user, status):
        return self.request(
            "/ftp?action=SetStatus", {"ftp_user": ftp_user, "status": status}
        )

    # --- Docker Management ---
    def docker_request(self, model, def_name, extra_params=None):
        params = {
            "url": "unix:///var/run/docker.sock",
            "dk_model_name": model,
            "dk_def_name": def_name,
        }
        if extra_params:
            params.update(extra_params)
        return self.request("/project/docker/model", params)

    def get_docker_containers(self):
        result = self.docker_request("container", "get_list")
        if isinstance(result, dict) and result.get("status") is True:
            msg = result.get("msg", {})
            return msg.get("container_list", []) if isinstance(msg, dict) else msg
        return result

    def operate_docker_container(self, container_id, action):
        return self.docker_request("container", action, {"container_id": container_id})

    def get_docker_logs(self, container_id):
        return self.docker_request(
            "container", "get_logs", {"container_id": container_id}
        )

    def get_compose_projects(self):
        return self.docker_request("compose", "get_project_list")

    def create_compose_project(self, project_name, path, template_id="", remark=""):
        return self.docker_request(
            "compose",
            "create_project",
            {
                "project_name": project_name,
                "path": path,
                "template_id": template_id,
                "remark": remark,
            },
        )

    def operate_compose_project(self, project_name, action):
        return self.docker_request(
            "compose",
            "operate_project",
            {"project_name": project_name, "action": action},
        )

    # --- Database Management ---
    def get_databases(self, page=1, limit=20):
        return self.request(
            "/data?action=getData&table=databases", {"p": page, "limit": limit}
        )

    def create_database(self, name, username, password, db_type="MySQL", ps=""):
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
        return self.request(
            "/database?action=DeleteDatabase", {"id": db_id, "name": name}
        )

    def set_database_password(self, db_id, name, password):
        return self.request(
            "/database?action=ResDatabasePassword",
            {"id": db_id, "name": name, "password": password},
        )

    def get_database_logs(self):
        return self.request("/database?action=GetDbErrorLog")

    def backup_database(self, db_name):
        return self.request("/database?action=ToBackup", {"name": db_name})

    def delete_database_backup(self, db_name, backup_file):
        return self.request(
            "/database?action=DelBackup", {"name": db_name, "file": backup_file}
        )

    # --- Website Proxy ---
    def create_proxy(self, site_name, proxy_url, host, to_path=""):
        return self.request(
            "/site?action=CreateProxy",
            {
                "siteName": site_name,
                "proxy_url": proxy_url,
                "host": host,
                "toPath": to_path,
            },
        )

    def modify_proxy(self, site_name, proxy_url, host, to_path=""):
        return self.request(
            "/site?action=ModifyProxy",
            {
                "siteName": site_name,
                "proxy_url": proxy_url,
                "host": host,
                "toPath": to_path,
            },
        )

    # --- Website Dir Binding ---
    def get_dir_binding(self, site_name):
        return self.request("/site?action=GetDirBinding", {"siteName": site_name})

    def add_dir_binding(self, site_name, domain, dir_path, port="80"):
        return self.request(
            "/site?action=AddDirBinding",
            {"siteName": site_name, "domain": domain, "dir": dir_path, "port": port},
        )

    def delete_dir_binding(self, site_name, domain, dir_path):
        return self.request(
            "/site?action=DelDirBinding",
            {"siteName": site_name, "domain": domain, "dir": dir_path},
        )

    def get_dir_rewrite(self, site_name, dir_path):
        return self.request(
            "/site?action=GetDirRewrite", {"siteName": site_name, "dir": dir_path}
        )

    # --- Software Management ---
    def get_plugins(self):
        result = self.request("/plugin?action=get_soft_list")
        return (
            result.get("list")
            if isinstance(result, dict) and "list" in result
            else result
        )

    def install_software(self, s_name, version):
        return self.request(
            "/plugin?action=install_plugin", {"s_name": s_name, "version": version}
        )

    def update_software(self, s_name, version):
        return self.request(
            "/plugin?action=update_plugin", {"s_name": s_name, "version": version}
        )

    def uninstall_software(self, s_name, version):
        return self.request(
            "/plugin?action=un_install_plugin", {"s_name": s_name, "version": version}
        )

    # --- System Status ---
    def get_system_total(self):
        return self.request("/system?action=GetSystemTotal")

    def get_disk_info(self):
        return self.request("/system?action=GetDiskInfo")

    def get_network(self):
        return self.request("/system?action=GetNetWork")

    def get_task_count(self):
        return self.request("/ajax?action=GetTaskCount")

    def update_panel(self):
        return self.request("/ajax?action=UpdatePanel")

    # --- Security & Firewall ---
    def get_firewall_list(self, page=1, limit=20):
        return self.request("/firewall?action=GetList", {"p": page, "limit": limit})

    def add_firewall_rule(self, port, ps, protocol="tcp"):
        return self.request(
            "/firewall?action=AddAcceptPort",
            {"port": port, "ps": ps, "protocol": protocol},
        )

    def delete_firewall_rule(self, rule_id, port):
        return self.request(
            "/firewall?action=DelAcceptPort", {"id": rule_id, "port": port}
        )

    def get_ssh_status(self):
        return self.request("/firewall?action=GetSSHStatus")

    def set_ssh_status(self, status):
        action = "OpenSSH" if status == 1 else "CloseSSH"
        return self.request(f"/firewall?action={action}")

    # --- File Management ---
    def get_files(self, path):
        return self.request("/files?action=GetDir", {"path": path})

    def create_dir(self, path):
        return self.request("/files?action=CreateDir", {"path": path})

    def write_file(self, path, content):
        # 稳健的文件创建/更新流程
        self.request(
            "/files?action=CreateFile", {"path": path}
        )  # 尝试创建空文件以防万一
        return self.request(
            "/files?action=SaveFileBody",
            {"path": path, "data": content, "encoding": "utf-8"},
        )

    def get_file_content(self, path):
        return self.request("/files?action=GetFileBody", {"path": path})

    def download_file(self, remote_path, local_path):
        res = self.get_file_content(remote_path)
        if isinstance(res, dict) and "data" in res:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(res["data"])
            return {"status": True, "msg": f"Downloaded to {local_path}"}
        return res

    def upload_file(self, local_path, remote_path):
        if not os.path.exists(local_path):
            return {"status": False, "msg": "Local file not found"}
        with open(local_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.write_file(remote_path, content)

    def compress_file(self, s_path, d_path, type="zip"):
        return self.request(
            "/files?action=Zip", {"sfile": s_path, "dfile": d_path, "type": type}
        )

    def decompress_file(self, s_path, d_path, password=""):
        return self.request(
            "/files?action=UnZip",
            {"sfile": s_path, "dfile": d_path, "password": password},
        )

    def get_recycle_bin(self):
        return self.request("/files?action=GetRecycleBin")

    def restore_recycle_bin(self, path):
        return self.request("/files?action=ReFile", {"path": path})

    def empty_recycle_bin(self):
        return self.request("/files?action=CloseRecycleBin")

    def exec_shell(self, command):
        return self.request("/files?action=ExecShell", {"command": command})

    def get_panel_logs(self, page=1, limit=20):
        return self.request(
            "/data?action=getData&table=logs", {"p": page, "limit": limit}
        )


if __name__ == "__main__":
    PANEL_URL = os.getenv("BT_PANEL_URL", "https://192.168.50.243:8888")
    API_KEY = os.getenv("BT_API_KEY")
    if not API_KEY:
        try:
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
        except:
            pass
    if not API_KEY:
        print(json.dumps({"status": False, "msg": "BT_API_KEY not set"}))
        sys.exit(1)
    api = BTPanelAPI(PANEL_URL, API_KEY)
    if len(sys.argv) < 2:
        print(json.dumps(api.request("/system?action=GetSystemTotal"), indent=2))
    else:
        action = sys.argv[1]
        args = sys.argv[2:]
        if action == "sites":
            print(json.dumps(api.get_sites(), indent=2))
        elif action == "docker":
            print(json.dumps(api.get_docker_containers(), indent=2))
        elif action == "databases":
            print(json.dumps(api.get_databases(), indent=2))
        elif action == "files":
            print(json.dumps(api.get_files(args[0] if args else "/"), indent=2))
        elif action == "exec_shell":
            print(json.dumps(api.exec_shell(" ".join(args)), indent=2))
        else:
            print(json.dumps({"status": False, "msg": f"Unknown action: {action}"}))
