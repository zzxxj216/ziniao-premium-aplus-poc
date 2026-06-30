"""
M2 发现:dump 出与 A+ / 品牌 / 内容 相关的导航链接(文字 + href),
以确定性定位 A+ Content Manager 的真实 URL。纯查看,不改动。
"""
import os
import time

import yaml
from selenium.webdriver.common.by import By

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
KW = ["a+", "aplus", "内容", "品牌", "premium", "高级", "content", "brand"]


def dump_links(driver, tag):
    print(f"\n===== [{tag}] {driver.current_url} | {driver.title} =====")
    try:
        anchors = driver.find_elements(By.TAG_NAME, "a")
    except Exception as e:
        print("取链接异常:", e); return
    seen = set()
    for a in anchors:
        try:
            href = a.get_attribute("href") or ""
            text = (a.text or "").strip().replace("\n", " ")
        except Exception:
            continue
        blob = (href + " " + text).lower()
        if any(k in blob for k in KW) and href and href not in seen:
            seen.add(href)
            print(f"  [{text[:30]:<30}] {href}")


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

    driver.get("https://sellercentral.amazon.com/home")
    time.sleep(5)
    dump_links(driver, "classic-home")

    # 经典后台主菜单(☰)展开后再 dump
    try:
        menu = driver.find_element(By.ID, "sc-mkt-picker-switcher-select") if False else None
    except Exception:
        menu = None
    # 经典后台菜单按钮通常是左上角的汉堡;尝试常见选择器
    for sel in ['//a[@id="menuButton"]', '//div[@id="menu"]//a', '//*[@aria-label="菜单"]',
                '//*[contains(@class,"hamburger")]']:
        try:
            el = driver.find_element(By.XPATH, sel)
            el.click(); time.sleep(3)
            print(f"\n(已点开菜单: {sel})")
            dump_links(driver, "classic-home-menu-open")
            break
        except Exception:
            continue

    out_dir = os.path.join(HERE, "scratch"); os.makedirs(out_dir, exist_ok=True)
    driver.save_screenshot(os.path.join(out_dir, "nav_classic.png"))

    print("\n窗口保持打开。")


if __name__ == "__main__":
    main()
