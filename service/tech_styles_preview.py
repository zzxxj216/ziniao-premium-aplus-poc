"""技术规格两种样式分别预览:填示例 → 选样式[0]→预览截图 → 选样式[1]→预览截图。"""
import os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2
from build_generic import fill_text
from aplus_api import JS_STYLE_PAIR

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级技术规格"


def click_tab(driver, name):
    for e in driver.find_elements(By.XPATH, f'//*[normalize-space(text())="{name}"]'):
        if e.is_displayed():
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", e)
                return True
            except Exception:
                pass
    return False


def set_style(driver, idx):
    els = driver.execute_script(JS_STYLE_PAIR)
    if len(els) >= 2:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", els[-2:][idx])
        return True
    return False


def main():
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90):
        print("控制API未就绪"); return
    z.update_core()
    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    driver = z.attach(z.open_store(store.get("browserOauth"))); driver.implicitly_wait(10)
    open_premium_editor(driver)
    print("加模块:", add_module_v2(driver, MODULE)); time.sleep(3)
    print("填示例:", fill_text(driver)); time.sleep(1)

    for idx, tag in [(0, "style0"), (1, "style1")]:
        click_tab(driver, "编辑"); time.sleep(1)
        print(f"选样式[{idx}]:", set_style(driver, idx)); time.sleep(1.5)
        click_tab(driver, "预览"); time.sleep(4)
        driver.save_screenshot(os.path.join(HERE, "scratch", f"tech_{tag}.png"))
        print(f"  预览截图 tech_{tag}.png")
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
