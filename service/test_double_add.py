"""测试 add_module_v2 能否把双图加进编辑器。"""
import os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "包含文本的高级双图片"
JS_BODY = DEEP + "return deepAll(n=>n.tagName==='DIV'&&n.isContentEditable&&(''+(n.className||'')).includes('public-DraftEditor-content')).length;"


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
    print("add_module_v2:", add_module_v2(driver, MODULE)); time.sleep(3)
    slots = len([e for e in driver.find_elements(By.XPATH, '//*[contains(text(),"点击添加图片")]') if e.is_displayed()])
    print("图位(点击添加图片)数:", slots)
    print("Draft.js 正文数:", driver.execute_script(JS_BODY))
    driver.save_screenshot(os.path.join(HERE, "scratch", "double_added.png"))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
