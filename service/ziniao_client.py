"""
紫鸟浏览器 v6 (mac) 本地控制 API + Selenium CDP 接管封装。

机制来源:已核对官方 ziniao-open/ziniao_webdriver_demo 源码。
与 demo 的区别:
  - 企业凭据走环境变量(ZINIAO_COMPANY / ZINIAO_USERNAME / ZINIAO_PASSWORD),不再明文写配置文件
  - 仅保留 mac / v6 路径,聚焦中心服务场景
  - 类封装,便于后续被 FastAPI 端点复用

注意:webdriver 模式会接管紫鸟主进程,运行期间这台机器的紫鸟是被程序独占的。
"""
import hashlib
import json
import os
import platform
import subprocess
import time
import uuid

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

IS_MAC = platform.system() == "Darwin"


class ZiniaoError(RuntimeError):
    pass


class ZiniaoClient:
    def __init__(self, client_path: str, webdriver_dir: str, port: int):
        self.client_path = client_path        # mac 上为客户端程序名 "ziniao" 或 .app 路径
        self.webdriver_dir = webdriver_dir    # 备用 chromedriver 存放目录
        self.port = int(port)
        self.user_info = {
            "company": os.environ["ZINIAO_COMPANY"],
            "username": os.environ["ZINIAO_USERNAME"],
            "password": os.environ["ZINIAO_PASSWORD"],
        }

    # ---------- 本地控制 API ----------
    def _post(self, data: dict, timeout: int = 120):
        """启动期客户端可能还没监听端口,连接失败时返回 None 让上层轮询等待。"""
        data = {**data, **self.user_info}
        url = f"http://127.0.0.1:{self.port}"
        try:
            resp = requests.post(url, json.dumps(data).encode("utf-8"), timeout=timeout)
            return json.loads(resp.text)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return None

    def wait_ready(self, max_wait: int = 60) -> bool:
        """轮询直到本地控制 API 起来。"""
        waited = 0
        while waited < max_wait:
            if self._post({"action": "getBrowserList", "requestId": str(uuid.uuid4())}) is not None:
                return True
            time.sleep(2); waited += 2
        return False

    def kill_client(self):
        """关闭已运行的紫鸟主进程(webdriver 模式需要全新以该模式启动)。"""
        if IS_MAC:
            os.system("killall ziniao")
            time.sleep(3)

    def start_client(self):
        """以 webdriver 模式启动客户端。

        直接执行 .app 内二进制(而非 `open -a`),确保 webdriver 参数一定被传入 ——
        `open -a` 在 app 已运行时会去重为"仅激活",导致参数被丢弃。
        """
        if not IS_MAC:
            raise ZiniaoError("当前封装仅针对 mac;其他系统参考 demo 的分支")
        args = ["--run_type=web_driver", "--ipc_type=http", f"--port={self.port}"]
        if self.client_path.endswith(".app"):
            exe = os.path.join(self.client_path, "Contents", "MacOS", "ziniao")
            cmd = [exe, *args]
        else:
            cmd = ["open", "-a", self.client_path, "--args", *args]
        subprocess.Popen(cmd)
        time.sleep(5)

    def update_core(self, max_wait: int = 120):
        """打开店铺前更新内核;http 有超时,需循环调用直到成功。"""
        waited = 0
        while waited < max_wait:
            r = self._post({"action": "updateCore", "requestId": str(uuid.uuid4())})
            if r is None:
                time.sleep(2); waited += 2; continue
            sc = r.get("statusCode")
            if sc == 0:
                return
            if sc is None or sc == -10003:
                # 旧版本不支持该接口,跳过
                return
            time.sleep(2); waited += 2

    def list_browsers(self) -> list:
        """getBrowserList:返回所有店铺(含 browserOauth / browserName / siteId)。"""
        r = self._post({"action": "getBrowserList", "requestId": str(uuid.uuid4())})
        if str(r.get("statusCode")) != "0":
            raise ZiniaoError(f"getBrowserList 失败: {json.dumps(r, ensure_ascii=False)}")
        return r.get("browserList") or []

    def amazon_stores(self, site_id: str = "1") -> list:
        """筛选某站点的亚马逊店铺。site_id=1 为美国站。"""
        return [b for b in self.list_browsers() if str(b.get("siteId")) == str(site_id)]

    def store_by_name(self, name: str) -> dict:
        """按店铺名(紫鸟里的 browserName,大小写不敏感)精确选店。"""
        key = (name or "").strip().lower()
        for b in self.list_browsers():
            if (b.get("browserName") or "").strip().lower() == key:
                return b
        raise ZiniaoError(f"未找到店铺: {name}")

    def open_store(self, store_id: str) -> dict:
        """startBrowser:打开店铺窗口,返回含 debuggingPort / launcherPage / downloadPath。"""
        data = {
            "action": "startBrowser", "requestId": str(uuid.uuid4()),
            "isWaitPluginUpdate": 0, "isHeadless": 0, "isWebDriverReadOnlyMode": 0,
            "cookieTypeLoad": 0, "cookieTypeSave": 0, "runMode": "1",
            "isLoadUserPlugin": False, "pluginIdType": 1, "privacyMode": 0,
            "notPromptForDownload": 1,
        }
        # 纯数字按 browserId,否则按 browserOauth
        data["browserId" if str(store_id).isdigit() else "browserOauth"] = str(store_id)
        r = None
        for _ in range(4):  # 控制API偶发无响应(返回None),重试
            r = self._post(data)
            if r is not None:
                break
            time.sleep(3)
        if r is None:
            raise ZiniaoError("startBrowser 无响应(控制API),请重试或重启紫鸟")
        if str(r.get("statusCode")) != "0":
            raise ZiniaoError(f"startBrowser 失败: {json.dumps(r, ensure_ascii=False)}")
        return r

    def close_store(self, browser_oauth: str):
        self._post({"action": "stopBrowser", "requestId": str(uuid.uuid4()),
                    "duplicate": 0, "browserOauth": browser_oauth})

    def exit_client(self):
        self._post({"action": "exit", "requestId": str(uuid.uuid4())})

    # ---------- Selenium 接管 ----------
    def attach(self, open_ret: dict) -> webdriver.Chrome:
        """用 startBrowser 返回的 debuggingPort 做 CDP 接管。"""
        driver_path = self._resolve_chromedriver(open_ret)
        if not driver_path:
            raise ZiniaoError("找不到匹配的 chromedriver;先用 demo 的 download_driver 填充 webdriver_dir")
        port = open_ret.get("debuggingPort")
        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=3")
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
        # 自动接受 beforeunload 等原生弹窗(否则未保存编辑器导航时会卡死会话)
        options.set_capability("unhandledPromptBehavior", "accept")
        return webdriver.Chrome(service=Service(driver_path), options=options)

    def _resolve_chromedriver(self, open_ret: dict):
        """优先用店铺内核自带 webdriver,否则回退 webdriver_dir/chromedriver{major}。"""
        browser_path = open_ret.get("browserPath")
        if browser_path:
            if browser_path.endswith("superbrowser"):
                browser_path = os.path.dirname(browser_path)
            bundled = os.path.join(browser_path, "webdriver")
            if os.path.exists(bundled):
                return bundled
        core_version = open_ret.get("core_version") or ""
        major = core_version.split(".")[0] if core_version else ""
        fallback = os.path.join(self.webdriver_dir, f"chromedriver{major}")
        return fallback if os.path.exists(fallback) else None

    def download_driver(self):
        """从紫鸟 CDN 拉取各版本 chromedriver 到 webdriver_dir(mac)。源自 demo。"""
        arch = platform.machine()
        if arch == "x86_64":
            config_url = "https://cdn-superbrowser-attachment.ziniao.com/webdriver/mac/x64/config.json"
        elif arch == "arm64":
            config_url = "https://cdn-superbrowser-attachment.ziniao.com/webdriver/mac/arm64/config.json"
        else:
            return
        items = requests.get(config_url, timeout=60).json()
        os.makedirs(self.webdriver_dir, exist_ok=True)
        existing = {f for f in os.listdir(self.webdriver_dir) if f.startswith("chromedriver")}
        for item in items:
            name = item["name"]
            local = os.path.join(self.webdriver_dir, name)
            if name in existing and self._sha1(local) == item["sha1"]:
                continue
            with requests.get(item["url"], stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(local, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            os.chmod(local, 0o755)

    @staticmethod
    def _sha1(path: str) -> str:
        with open(path, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()
