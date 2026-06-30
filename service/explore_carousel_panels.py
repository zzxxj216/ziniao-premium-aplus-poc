"""探针:轮播面板到底怎么激活/添加。dump 面板元素 + 加面板按钮,点面板2看图位变化。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级、简单的图像轮播"

JS_PANELS = DEEP + """
var res={slots:0, panelEls:[], addish:[]};
res.slots=deepAll(n=>(n.textContent||'').trim()==='点击添加图片').filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;}).length;
deepAll(function(n){var t=(n.textContent||'').trim();return /^面板\\(\\d\\/\\d\\)$/.test(t);}).forEach(function(n){
  var r=n.getBoundingClientRect?n.getBoundingClientRect():{};
  res.panelEls.push({tag:n.tagName,txt:(n.textContent||'').trim(),cls:(''+(n.className||'')).slice(0,30),role:(n.getAttribute&&n.getAttribute('role'))||'',x:Math.round(r.x||0),y:Math.round(r.y||0),w:Math.round(r.width||0)});
});
deepAll(function(n){var t=(n.textContent||'').trim();return t.length<12 && /添加|新增|\\+|增加面板/.test(t);}).forEach(function(n){
  var key=n.tagName+':'+(n.textContent||'').trim().slice(0,10);
  if(res.addish.indexOf(key)<0) res.addish.push(key);
});
return res;
"""

def slots(driver):
    return driver.execute_script(DEEP + "return deepAll(n=>(n.textContent||'').trim()==='点击添加图片').filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;}).length;")

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
    print("加模块(v2):", add_module_v2(driver, MODULE)); time.sleep(4)

    r = driver.execute_script(JS_PANELS)
    print("初始图位数:", r["slots"])
    print("面板元素(精确 面板(N/M)):")
    for x in r["panelEls"]:
        print("  " + json.dumps(x, ensure_ascii=False))
    print("可能的加面板按钮:", r["addish"])

    # 点 面板(2/6) 看图位变化
    tabs = [e for e in driver.find_elements(By.XPATH, '//*[normalize-space(.)="面板(2/6)"]') if e.is_displayed()]
    print("面板2 可见元素数:", len(tabs))
    for i, t in enumerate(tabs):
        before = slots(driver)
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", t); t.click()
        except Exception as e:
            print(f"  点面板2元素[{i}]异常 {e}"); continue
        time.sleep(3)
        print(f"  点面板2元素[{i}] ({t.tag_name}): 图位 {before}->{slots(driver)}")
    driver.save_screenshot(os.path.join(HERE, "scratch", "carousel_panels.png"))
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
