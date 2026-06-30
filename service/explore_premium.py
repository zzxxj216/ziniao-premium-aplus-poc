"""
进入「创建 高级 A+」,捕获其后第一屏(内容名称/语言)的表单结构。
纯观察,不提交。为后续自动填名 + 进模块库做准备。
"""
import os
import time

import yaml
from selenium.webdriver.common.by import By

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
CM_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager"


def dump_forms(driver, tag):
    print(f"\n===== [{tag}] {driver.current_url} | {driver.title} =====")
    for name in ["input", "select", "textarea"]:
        for e in driver.find_elements(By.TAG_NAME, name):
            try:
                info = {k: e.get_attribute(k) for k in ("id", "name", "type", "placeholder", "aria-label", "value")}
                info = {k: v for k, v in info.items() if v}
                if e.is_displayed():
                    print(f"  <{name}> {info}")
            except Exception:
                pass
    for name in ["h1", "h2", "h3", "button"]:
        els = driver.find_elements(By.TAG_NAME, name)
        uniq = list(dict.fromkeys([(e.text or "").strip() for e in els if (e.text or "").strip()]))
        if uniq:
            print(f"  <{name}>: {uniq[:30]}")


def click_text(driver, texts):
    for t in texts:
        for xp in (f'//button[contains(.,"{t}")]', f'//*[contains(text(),"{t}")]'):
            try:
                el = driver.find_element(By.XPATH, xp)
                driver.execute_script("arguments[0].click();", el)
                return t
            except Exception:
                continue
    return None


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
    out_dir = os.path.join(HERE, "scratch"); os.makedirs(out_dir, exist_ok=True)

    driver.get(CM_URL); time.sleep(7)
    print("点击:", click_text(driver, ["开始创建"]))
    time.sleep(6)  # 到类型选择屏
    print("点击:", click_text(driver, ["创建 高级 A+", "高级"]))
    time.sleep(7)  # 到名称/语言屏

    driver.save_screenshot(os.path.join(out_dir, "create_3_premium.png"))
    dump_forms(driver, "premium-step")
    print("\n窗口保持打开。未提交。")


if __name__ == "__main__":
    main()
