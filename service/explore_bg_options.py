"""探查背景图片模块底部的两个选项(样式开关对 / 字体颜色下拉等)。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP
from aplus_api import JS_STYLE_PAIR

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "包含文本的高级背景图片"

JS_SELECTS = DEEP + """
return deepAll(function(n){return n.tagName==='SELECT'||n.tagName==='KAT-DROPDOWN'||(n.getAttribute&&n.getAttribute('role')==='listbox');})
.filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;})
.map(function(n){return {tag:n.tagName, aria:(n.getAttribute&&(n.getAttribute('aria-label')||n.getAttribute('label')))||'', opts:(n.innerText||'').replace(/\\s+/g,'|').slice(0,60), y:Math.round((n.getBoundingClientRect&&n.getBoundingClientRect().y)||0)};});
"""

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

    pair = driver.execute_script(JS_STYLE_PAIR)
    print("底部样式开关对候选:", len(pair))
    for i, e in enumerate(pair):
        try: print(f"  [{i}] {e.tag_name} w={e.size['width']} h={e.size['height']} txt={(e.text or '')[:14]!r} style={(e.get_attribute('style') or '')[:50]!r}")
        except Exception: pass
    print("下拉/选择:")
    for s in driver.execute_script(JS_SELECTS):
        print("  " + json.dumps(s, ensure_ascii=False))
    # 滚到模块底部截图
    try:
        el = driver.find_element(By.XPATH, '//*[contains(text(),"添加模块")]')
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception:
        pass
    time.sleep(1)
    driver.save_screenshot(os.path.join(HERE, "scratch", "bg_options.png"))
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
