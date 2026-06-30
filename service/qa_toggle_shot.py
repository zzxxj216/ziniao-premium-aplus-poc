"""加问答 → 把模块底部(黑白背景开关)滚进视野 → 截图 + 打印视口/像素比(为坐标点击做准备)。"""
import os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级问答"


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
    open_premium_editor(driver)
    print("加模块(v2):", add_module_v2(driver, MODULE)); time.sleep(3)

    # 滚到"添加问题"附近(模块底部),黑白开关应在其上下
    try:
        el = driver.find_element(By.XPATH, '//*[contains(text(),"添加问题")]')
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)
    info = driver.execute_script("return {w:window.innerWidth,h:window.innerHeight,dpr:window.devicePixelRatio};")
    print("视口:", info)
    driver.save_screenshot(os.path.join(HERE, "scratch", "qa_toggle.png"))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
