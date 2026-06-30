"""
深链进高级 A+ 编辑器,探测 iframe,打开「添加模块」库,捕获 7 个模块选项。
纯观察,不保存(不点"保存为草稿")。
"""
import os
import time

import yaml
from selenium.webdriver.common.by import By

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager/workflow/ebc-premium/content/new/edit"


def find_in_frames(driver, xpath):
    """在主文档 + 各 iframe 里找元素,返回 (frame_index 或 None, element 或 None)。"""
    driver.switch_to.default_content()
    els = driver.find_elements(By.XPATH, xpath)
    if els:
        return None, els[0]
    n = len(driver.find_elements(By.TAG_NAME, "iframe"))
    for idx in range(n):
        driver.switch_to.default_content()
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        if idx >= len(frames):
            break
        try:
            driver.switch_to.frame(frames[idx])
            els = driver.find_elements(By.XPATH, xpath)
            if els:
                return idx, els[0]
        except Exception:
            continue
    driver.switch_to.default_content()
    return None, None


def dump_here(driver, tag):
    print(f"--- dump [{tag}] ---")
    for name in ["h1", "h2", "h3", "h4", "button"]:
        els = driver.find_elements(By.TAG_NAME, name)
        uniq = list(dict.fromkeys([(e.text or "").strip() for e in els if (e.text or "").strip() and len(e.text) < 50]))
        if uniq:
            print(f"  <{name}>: {uniq[:40]}")


def main():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver()
    z.kill_client(); z.start_client()
    if not z.wait_ready(max_wait=90):
        print("控制 API 未就绪"); return
    z.update_core()
    oauth = z.amazon_stores(site_id="1")[0].get("browserOauth")
    driver = z.attach(z.open_store(oauth))
    driver.implicitly_wait(15)
    out_dir = os.path.join(HERE, "scratch"); os.makedirs(out_dir, exist_ok=True)

    print(f"深链进编辑器: {EDITOR_URL}")
    driver.get(EDITOR_URL)
    time.sleep(10)
    print(f"落地 URL: {driver.current_url}")
    if "/ap/" in driver.current_url:
        print("被弹登录,放弃"); return

    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"iframe 数量: {len(iframes)}")
    for i, f in enumerate(iframes):
        print(f"  iframe[{i}] src={f.get_attribute('src')}")

    # 找「添加模块」
    idx, el = find_in_frames(driver, '//*[contains(text(),"添加模块")]')
    print(f"添加模块 所在 frame: {idx}")
    if el is None:
        print("没找到 添加模块,dump 主文档与各 iframe:")
        driver.switch_to.default_content(); dump_here(driver, "main")
        for i in range(len(iframes)):
            driver.switch_to.default_content()
            try:
                driver.switch_to.frame(driver.find_elements(By.TAG_NAME, "iframe")[i])
                dump_here(driver, f"iframe[{i}]")
            except Exception as e:
                print(f"  iframe[{i}] 异常 {e}")
        driver.switch_to.default_content()
        driver.save_screenshot(os.path.join(out_dir, "create_4_noadd.png"))
        print("\n窗口保持打开。未保存。"); return

    # 点开模块库
    driver.execute_script("arguments[0].click();", el)
    time.sleep(5)
    driver.switch_to.default_content()
    driver.save_screenshot(os.path.join(out_dir, "create_4_gallery.png"))
    # 模块库可能也在某 iframe
    if idx is not None:
        try:
            driver.switch_to.frame(driver.find_elements(By.TAG_NAME, "iframe")[idx])
        except Exception:
            pass
    dump_here(driver, "gallery")
    print("\n窗口保持打开。未保存。")


if __name__ == "__main__":
    main()
