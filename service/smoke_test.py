"""
M1 冒烟测试:起客户端 → 开第一个美国站亚马逊店铺 → CDP 接管 →
确认已登进 Seller Central → 截图 → 打印当前 URL/标题 → 收尾。

在那台装了紫鸟 v6 的 Mac 上运行:
    export ZINIAO_COMPANY=...  ZINIAO_USERNAME=...  ZINIAO_PASSWORD=...
    python smoke_test.py

成功标准:scratch/seller_central.png 截到的是已登录的 Seller Central 首页。
A+ Content Manager 的导航与选择器留待看到真实页面后再写(见文末 TODO)。
"""
import os
import time
import traceback

import yaml

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))


def load_browser_config():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg["browser"]


def main():
    bc = load_browser_config()
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])

    print("=== 下载/校验 chromedriver ===")
    z.download_driver()

    print("=== 关闭并以 webdriver 模式重启紫鸟 ===")
    z.kill_client()
    z.start_client()
    print("=== 等待本地控制 API 就绪 ===")
    if not z.wait_ready(max_wait=90):
        print("控制 API 在 90s 内未就绪 —— 客户端可能没以 webdriver 模式启动")
        return
    z.update_core()

    print("=== 获取美国站(siteId=1)店铺 ===")
    stores = z.amazon_stores(site_id="1")
    if not stores:
        print("没有找到美国站店铺,检查紫鸟里是否已添加亚马逊美国店铺")
        z.exit_client(); return
    store = stores[0]
    name = store.get("browserName")
    oauth = store.get("browserOauth")
    print(f"目标店铺: {name} ({oauth})")

    ret = z.open_store(oauth)
    driver = None
    try:
        driver = z.attach(ret)
        driver.implicitly_wait(60)

        # 落到店铺平台主页(Seller Central 首页)
        launcher = ret.get("launcherPage")
        print(f"打开平台主页: {launcher}")
        driver.get(launcher)
        time.sleep(6)

        out_dir = os.path.join(HERE, "scratch")
        os.makedirs(out_dir, exist_ok=True)
        shot = os.path.join(out_dir, "seller_central.png")
        driver.save_screenshot(shot)
        print(f"当前 URL : {driver.current_url}")
        print(f"页面标题 : {driver.title}")
        print(f"截图已存 : {shot}")

        # TODO(M2): 在此导航到 A+ Content Manager,抓取真实 DOM 选择器。
        #   - 进入路径 / URL 需看真实页面确认,不预设
        #   - 确认高级 A+(Premium A+)入口是否存在(取决于品牌资格)
    except Exception:
        print("冒烟测试异常:\n" + traceback.format_exc())
    finally:
        if driver:
            driver.quit()
        print(f"=== 关闭店铺: {name} ===")
        z.close_store(oauth)
        z.exit_client()


if __name__ == "__main__":
    main()
