"""探查"高级、简单的图像轮播"的面板结构:面板标签/添加按钮、图位、文本字段。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级、简单的图像轮播"

JS = DEEP + """
var res={panelish:[],imgslots:0,clickables:[]};
res.imgslots=deepAll(n=>(n.textContent||'').trim()==='点击添加图片').length;
deepAll(function(n){
  var t=(n.textContent||'').trim();
  return t.length<14 && (/面板|添加|＋|\\+|下一|上一/.test(t)) ;
}).forEach(function(n){
  var key=n.tagName+':'+(n.textContent||'').trim().slice(0,12);
  if(res.panelish.indexOf(key)<0) res.panelish.push(key);
});
// 可点击且文本短(可能是面板标签/加面板)
deepAll(function(n){
  var ok=(n.tagName==='BUTTON'||n.tagName==='KAT-BUTTON'||(n.getAttribute&&n.getAttribute('role')==='button')||(n.getAttribute&&n.getAttribute('role')==='tab'));
  var t=(n.textContent||'').trim();
  return ok && t.length<16 && t.length>0;
}).forEach(function(n){
  var key=(n.getAttribute&&n.getAttribute('role')||n.tagName)+':'+(n.textContent||'').trim().slice(0,12);
  if(res.clickables.indexOf(key)<0) res.clickables.push(key);
});
return res;
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
    print("加模块(v2):", add_module_v2(driver, MODULE)); time.sleep(4)
    driver.save_screenshot(os.path.join(HERE, "scratch", "carousel.png"))
    r = driver.execute_script(JS)
    print("图位数:", r["imgslots"])
    print("面板相关文本:", r["panelish"])
    print("短文本可点击元素:", r["clickables"])
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
