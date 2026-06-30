"""打开模块库,dump 弹层里所有可见输入框,定位模块库搜索框。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))

JS_INPUTS = DEEP + """
return deepAll(n=>(n.tagName==='INPUT'||n.tagName==='TEXTAREA')).filter(function(n){
  var r=n.getBoundingClientRect&&n.getBoundingClientRect(); return r&&r.width>0&&r.height>0;
}).map(function(n){return {tag:n.tagName, ph:n.placeholder||'', aria:(n.getAttribute&&n.getAttribute('aria-label'))||'',
  id:n.id||'', cls:(''+(n.className||'')).slice(0,40), type:n.type||''};});
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
    # 开模块库
    btns = [b for b in driver.find_elements(By.XPATH, '//*[normalize-space(text())="添加模块"]') if b.is_displayed()]
    (btns[-1] if btns else driver.find_element(By.XPATH, '//*[contains(text(),"添加模块")]')).click()
    time.sleep(4)
    driver.save_screenshot(os.path.join(HERE, "scratch", "gallery_inputs.png"))
    print("模块库打开后,所有可见输入框:")
    for f in driver.execute_script(JS_INPUTS):
        print("  " + json.dumps(f, ensure_ascii=False))
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
