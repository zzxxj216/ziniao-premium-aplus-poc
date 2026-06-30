"""验证:问答黑白背景开关 = 两个 width:80px;height:31px 的 button。点第二个看背景变化。"""
import os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级问答"

JS_TOGGLES = DEEP + """
return deepAll(function(n){
  if(n.tagName!=='BUTTON') return false;
  var s=(n.getAttribute&&n.getAttribute('style'))||'';
  return /width:\\s*80px/.test(s) && /height:\\s*31px/.test(s);
}).map(function(n){return n;});
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
    print("加模块(v2):", add_module_v2(driver, MODULE)); time.sleep(3)

    els = driver.execute_script(JS_TOGGLES)
    print("找到背景开关按钮数:", len(els))
    for i, e in enumerate(els):
        print(f"  [{i}] style={e.get_attribute('style')[:90]!r}")
    if len(els) >= 2:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", els[1])
        driver.save_screenshot(os.path.join(HERE, "scratch", "toggle_before.png"))
        els[1].click()   # selenium 原生点第二个
        time.sleep(2)
        driver.save_screenshot(os.path.join(HERE, "scratch", "toggle_after.png"))
        print("已点第二个开关,看 toggle_before/after.png 对比")
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
