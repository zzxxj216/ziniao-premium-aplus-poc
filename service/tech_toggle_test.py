"""技术规格的样式开关:用 JS_STYLE_PAIR 找模块底部样式对,点一下看变化。"""
import os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2
from aplus_api import JS_STYLE_PAIR

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级技术规格"


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
    print("加模块(v2):", add_module_v2(driver, MODULE)); time.sleep(3)

    els = driver.execute_script(JS_STYLE_PAIR)
    print("底部样式开关候选数:", len(els))
    for i, e in enumerate(els):
        try:
            print(f"  [{i}] {e.tag_name} w={e.size['width']} h={e.size['height']} style={(e.get_attribute('style') or '')[:70]!r}")
        except Exception:
            pass
    if len(els) >= 2:
        pair = els[-2:]
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pair[0])
        driver.save_screenshot(os.path.join(HERE, "scratch", "tech_before.png"))
        pair[1].click(); time.sleep(2)
        driver.save_screenshot(os.path.join(HERE, "scratch", "tech_after.png"))
        print("已点第二个,看 tech_before/after.png")
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
