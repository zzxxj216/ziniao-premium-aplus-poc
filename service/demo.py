"""
效果演示:① 截内容管理器列表(已建的草稿)② 打开 dinosaur 6模块草稿的「预览」整页截图。
"""
import base64
import os
import time

import yaml
from selenium.webdriver.common.by import By

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
CM_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager"
DRAFT_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager/workflow/ebc-premium/content/c06db32d-f970-4f0c-8b8a-6429ff65cc47/revision/1782451001368/edit"


def full_page_png(driver, path):
    try:
        res = driver.execute_cdp_cmd("Page.captureScreenshot", {"captureBeyondViewport": True, "fromSurface": True, "format": "png"})
        with open(path, "wb") as f:
            f.write(base64.b64decode(res["data"]))
        return True
    except Exception as e:
        print("整页截图失败,回退普通截图:", e)
        driver.save_screenshot(path)
        return False


def main():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(max_wait=90):
        print("控制 API 未就绪"); return
    z.update_core()
    oauth = z.amazon_stores(site_id="1")[0].get("browserOauth")
    driver = z.attach(z.open_store(oauth)); driver.implicitly_wait(10)
    out = os.path.join(HERE, "scratch"); os.makedirs(out, exist_ok=True)

    # ① 内容列表
    driver.get(CM_URL); time.sleep(8)
    driver.save_screenshot(os.path.join(out, "demo_1_list.png"))
    print("列表已截图")

    # ② 打开 dinosaur 草稿 → 预览 → 整页截图
    driver.get(DRAFT_URL); time.sleep(10)
    try:
        el = driver.find_element(By.XPATH, '//*[normalize-space(text())="预览"]')
        driver.execute_script("arguments[0].click();", el)
        print("已切到预览")
    except Exception as e:
        print("没找到预览标签:", e)
    time.sleep(8)
    full_page_png(driver, os.path.join(out, "demo_2_preview.png"))
    print("预览整页已截图")
    print("URL:", driver.current_url)
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
