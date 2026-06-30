"""验证 XY:会话持久化 + 后台界面语言(简体/繁体)。"""
import os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import safe_get

HERE = os.path.dirname(os.path.abspath(__file__))
CM_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager"
SIMP = ["开始创建", "添加模块", "商品描述", "保存为草稿"]
TRAD = ["開始建立", "開始創建", "新增模組", "商品說明", "儲存"]


def main():
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90):
        print("控制API未就绪"); return
    z.update_core()
    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    print("店铺:", store.get("browserName"))
    driver = z.attach(z.open_store(store.get("browserOauth"))); driver.implicitly_wait(10)

    driver.get("https://sellercentral.amazon.com/home"); time.sleep(6)
    print("home URL:", driver.current_url, "| 标题:", driver.title)
    logged_in = "sellercentral." in driver.current_url and "/ap/" not in driver.current_url
    print("已登录(会话持久化):", logged_in)

    safe_get(driver, CM_URL); time.sleep(8)
    driver.save_screenshot(os.path.join(HERE, "scratch", "xy_cm.png"))
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("命中简体:", [k for k in SIMP if k in txt])
    print("命中繁体:", [k for k in TRAD if k in txt])
    print("CM URL:", driver.current_url, "| 标题:", driver.title)
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
