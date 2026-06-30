"""
M2 探查:在已登录会话里导航到 A+ Content Manager,截图并扫描页面,
确认真实 URL、是否存在"高级 A+ / Premium A+"入口,并收集含 aplus 的链接。
不改动任何 listing,纯查看。窗口保持打开。
"""
import os
import time

import yaml
from selenium.webdriver.common.by import By

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))

# 真实入口(用户提供):A+ 内容管理器
CANDIDATES = [
    "https://sellercentral.amazon.com/enhanced-content/content-manager",
]
KEYWORDS = ["Premium", "高级", "A+", "Brand Story", "品牌故事", "内容管理", "aplus"]


def main():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver()
    z.kill_client(); z.start_client()
    if not z.wait_ready(max_wait=90):
        print("控制 API 未就绪"); return
    z.update_core()
    store = z.amazon_stores(site_id="1")[0]
    oauth = store.get("browserOauth")
    ret = z.open_store(oauth)
    driver = z.attach(ret)
    driver.implicitly_wait(20)

    # 先确保在已登录态
    driver.get("https://sellercentral.amazon.com/home")
    time.sleep(5)
    print(f"home: {driver.current_url} | {driver.title}")

    out_dir = os.path.join(HERE, "scratch"); os.makedirs(out_dir, exist_ok=True)

    for i, url in enumerate(CANDIDATES):
        print(f"\n--- 尝试候选 {i}: {url} ---")
        driver.get(url)
        time.sleep(6)
        final_url, title = driver.current_url, driver.title
        print(f"落地 URL : {final_url}")
        print(f"标题     : {title}")
        shot = os.path.join(out_dir, f"aplus_{i}.png")
        driver.save_screenshot(shot)
        print(f"截图     : {shot}")
        src = driver.page_source
        hits = [k for k in KEYWORDS if k in src]
        print(f"命中关键词: {hits}")
        if "/ap/signin" in final_url or "/ap/mfa" in final_url:
            print("⚠️ 被弹回登录,会话可能失效")
            break
        # 收集含 aplus 的链接,帮助定位真实路径
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            aplus_links = sorted({a.get_attribute("href") for a in links
                                  if a.get_attribute("href") and "aplus" in a.get_attribute("href").lower()})
            if aplus_links:
                print("页面内含 aplus 的链接:")
                for l in aplus_links[:15]:
                    print("  ", l)
        except Exception as e:
            print(f"收集链接异常: {e}")

    print("\n窗口保持打开。")


if __name__ == "__main__":
    main()
