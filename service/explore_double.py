"""探查"包含文本的高级双图片"结构:文本字段、图位数、Draft.js 数、左右布局。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "包含文本的高级双图片"

JS_INPUTS = DEEP + "return deepAll(n=>(n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&n.id!=='sc-search-field').map(n=>({tag:n.tagName,ph:n.placeholder||'',aria:(n.getAttribute&&n.getAttribute('aria-label'))||''}));"
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
    print("加模块:", add_module(driver, MODULE)); time.sleep(4)
    driver.save_screenshot(os.path.join(HERE, "scratch", "double.png"))

    imgslots = len([e for e in driver.find_elements(By.XPATH, '//*[contains(text(),"点击添加图片")]') if e.is_displayed()])
    print("图位(点击添加图片)数:", imgslots)
    print("Draft.js 正文数:", driver.execute_script(JS_BODY))
    print("文本字段:")
    for f in driver.execute_script(JS_INPUTS):
        if f.get("ph") or f.get("aria"):
            print("  " + json.dumps(f, ensure_ascii=False))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
