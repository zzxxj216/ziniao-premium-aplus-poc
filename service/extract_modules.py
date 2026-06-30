"""
打开高级 A+「添加模块」库,用 innerText 跨 frame 提取模块名清单。
纯观察,不保存。
"""
import os
import time

import yaml
from selenium.webdriver.common.by import By

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager/workflow/ebc-premium/content/new/edit"


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

    driver.get(EDITOR_URL)
    time.sleep(10)
    if "/ap/" in driver.current_url:
        print("被弹登录"); return

    # 点 添加模块(主文档)
    try:
        el = driver.find_element(By.XPATH, '//*[contains(text(),"添加模块")]')
        driver.execute_script("arguments[0].click();", el)
    except Exception as e:
        print("点添加模块失败:", e); return
    time.sleep(6)
    driver.save_screenshot(os.path.join(out_dir, "create_4_gallery.png"))

    def dump_innertext(label):
        try:
            txt = driver.execute_script("return document.body ? document.body.innerText : ''")
        except Exception as e:
            print(f"[{label}] innerText 异常: {e}"); return
        lines = [l.strip() for l in (txt or "").splitlines() if l.strip()]
        # 去重保序
        uniq = list(dict.fromkeys(lines))
        if uniq:
            print(f"\n===== innerText [{label}] ({len(uniq)} 行) =====")
            for l in uniq[:120]:
                print("  ", l)

    driver.switch_to.default_content()
    dump_innertext("main")
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"\niframe 数量: {len(frames)}")
    for i in range(len(frames)):
        driver.switch_to.default_content()
        fl = driver.find_elements(By.TAG_NAME, "iframe")
        if i >= len(fl):
            break
        try:
            driver.switch_to.frame(fl[i])
            dump_innertext(f"iframe[{i}]")
            # 再下钻一层嵌套 iframe
            inner = driver.find_elements(By.TAG_NAME, "iframe")
            for j in range(len(inner)):
                try:
                    driver.switch_to.frame(driver.find_elements(By.TAG_NAME, "iframe")[j])
                    dump_innertext(f"iframe[{i}][{j}]")
                    driver.switch_to.parent_frame()
                except Exception:
                    pass
        except Exception as e:
            print(f"iframe[{i}] 异常: {e}")
    driver.switch_to.default_content()
    print("\n窗口保持打开。未保存。")


if __name__ == "__main__":
    main()
