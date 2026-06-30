"""探查 XY 内容管理器实际文案/语言。"""
import os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import safe_get

HERE = os.path.dirname(os.path.abspath(__file__))
CM = "https://sellercentral.amazon.com/enhanced-content/content-manager"


def main():
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90):
        print("控制API未就绪"); return
    z.update_core()
    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    driver = z.attach(z.open_store(store.get("browserOauth"))); driver.implicitly_wait(8)
    safe_get(driver, CM); time.sleep(10)
    driver.save_screenshot(os.path.join(HERE, "scratch", "probe_xy_cm.png"))
    print("URL:", driver.current_url, "| 标题:", driver.title)
    for tag in ["h1", "h2", "button", "a"]:
        els = driver.find_elements(By.TAG_NAME, tag)
        uniq = list(dict.fromkeys([(e.text or "").strip() for e in els if (e.text or "").strip() and len(e.text) < 30]))
        if uniq:
            print(f"<{tag}>: {uniq[:25]}")
    # 顶部语言指示
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
