"""
打开美国站店铺窗口、停在 Seller Central 登录页,保持窗口打开,
等待人工登录(含 2FA)。检测到离开登录页即视为登录成功,截图后退出,
**不关闭窗口/客户端**,以便后续 M2 复用该已登录会话。

用法(在装了紫鸟 v6 的 Mac 上,凭据走环境变量):
    python open_for_login.py
"""
import os
import time
import traceback

import yaml

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
LOGIN_WAIT_SECONDS = 600   # 给人工登录(含 2FA)的最长等待
POLL_INTERVAL = 5


def main():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])

    z.download_driver()
    print("=== 以 webdriver 模式启动紫鸟 ===")
    z.kill_client()
    z.start_client()
    if not z.wait_ready(max_wait=90):
        print("控制 API 未就绪"); return
    z.update_core()

    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    name, oauth = store.get("browserName"), store.get("browserOauth")
    print(f"目标店铺: {name} ({oauth})")

    ret = z.open_store(oauth)
    driver = z.attach(ret)
    driver.implicitly_wait(30)
    driver.get(ret.get("launcherPage") or "https://sellercentral.amazon.com/home")

    out_dir = os.path.join(HERE, "scratch")
    os.makedirs(out_dir, exist_ok=True)

    print(f"窗口已打开,请在紫鸟窗口里手动登录(最多等 {LOGIN_WAIT_SECONDS}s)...")
    waited = 0
    logged_in = False
    while waited < LOGIN_WAIT_SECONDS:
        try:
            url = driver.current_url
        except Exception:
            url = ""
        # 登录成功 = 在 sellercentral 域、且不在任何 /ap/ 认证页(signin/mfa 等)
        if "sellercentral." in url and "/ap/" not in url:
            logged_in = True
            break
        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL

    try:
        shot = os.path.join(out_dir, "after_login.png" if logged_in else "still_login.png")
        driver.save_screenshot(shot)
        print(f"登录{'成功' if logged_in else '未完成(超时)'}")
        print(f"当前 URL : {driver.current_url}")
        print(f"页面标题 : {driver.title}")
        print(f"截图     : {shot}")
        if logged_in:
            print(f"店铺 oauth(供 M2 复用): {oauth}")
    except Exception:
        print(traceback.format_exc())

    # 故意不调用 driver.quit() / close_store() / exit_client():保持窗口与会话
    print("窗口保持打开。")


if __name__ == "__main__":
    main()
