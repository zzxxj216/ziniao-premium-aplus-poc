"""
M2/M3 准备:进入「开始创建 A+ 商品描述」向导,探查可选的内容类型/模块,
为"类型清单 + 创建接口输入 schema"取证。纯查看,绝不点击保存/提交。
"""
import os
import time

import yaml
from selenium.webdriver.common.by import By

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
CM_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager"


def dump_interactive(driver, tag):
    print(f"\n===== [{tag}] {driver.current_url} | {driver.title} =====")
    for by, name in [(By.TAG_NAME, "h1"), (By.TAG_NAME, "h2"), (By.TAG_NAME, "h3"),
                     (By.TAG_NAME, "button"), (By.TAG_NAME, "a")]:
        try:
            els = driver.find_elements(by, name)
        except Exception:
            continue
        texts = []
        for e in els:
            try:
                t = (e.text or "").strip().replace("\n", " ")
            except Exception:
                t = ""
            if t and len(t) < 60:
                texts.append(t)
        # 去重保序
        uniq = list(dict.fromkeys(texts))
        if uniq:
            print(f"  <{name}> ({len(uniq)}): {uniq[:40]}")


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
    driver.implicitly_wait(20)

    driver.get(CM_URL)
    time.sleep(7)
    out_dir = os.path.join(HERE, "scratch"); os.makedirs(out_dir, exist_ok=True)
    driver.save_screenshot(os.path.join(out_dir, "create_0_manager.png"))
    dump_interactive(driver, "content-manager")

    # 点「开始创建 A+ 商品描述」
    clicked = False
    for xp in ['//*[contains(text(),"开始创建")]',
               '//button[contains(.,"开始创建")]',
               '//a[contains(.,"开始创建")]',
               '//*[contains(text(),"创建 A+")]']:
        try:
            el = driver.find_element(By.XPATH, xp)
            driver.execute_script("arguments[0].click();", el)
            clicked = True
            print(f"\n已点击创建入口: {xp}")
            break
        except Exception:
            continue
    if not clicked:
        print("没找到创建入口按钮"); print("\n窗口保持打开。"); return

    time.sleep(7)
    driver.save_screenshot(os.path.join(out_dir, "create_1_step.png"))
    dump_interactive(driver, "create-step-1")

    # 若出现"添加模块/模板"入口,尝试展开看模块库(仍不保存)
    for xp in ['//*[contains(text(),"添加模块")]', '//*[contains(text(),"模块")]',
               '//*[contains(text(),"Premium")]', '//*[contains(text(),"高级")]']:
        try:
            el = driver.find_element(By.XPATH, xp)
            driver.execute_script("arguments[0].click();", el)
            time.sleep(5)
            driver.save_screenshot(os.path.join(out_dir, "create_2_modules.png"))
            dump_interactive(driver, "create-modules")
            print(f"(展开了: {xp})")
            break
        except Exception:
            continue

    print("\n窗口保持打开。未保存任何内容。")


if __name__ == "__main__":
    main()
