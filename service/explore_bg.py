"""探查背景图片上传:点「添加背景图片」后出现什么(拖拽区?另一种对话框?)。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP, JS_ZONES

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "包含文本的高级背景图片"

JS_CANDS = DEEP + "return deepAll(function(n){var x=(n.textContent||'').trim();return x.indexOf('添加背景图片')>=0&&x.length<=12;}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});"

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
    cands = driver.execute_script(JS_CANDS)
    print("『添加背景图片』候选:", len(cands))
    for i, e in enumerate(cands):
        try: print(f"  [{i}] {e.tag_name} w={e.size['width']} txt={(e.text or '')[:14]!r}")
        except Exception: pass
    # 逐个原生点击,看是否出现拖拽区或对话框
    for i, e in enumerate(cands):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", e); e.click()
        except Exception as ex:
            print(f"  点[{i}]异常 {ex}"); continue
        time.sleep(3)
        zones = len(driver.execute_script(JS_ZONES))
        print(f"  点[{i}]后 拖拽区={zones}")
        driver.save_screenshot(os.path.join(HERE, "scratch", f"bg_click{i}.png"))
        if zones: break
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
