"""探查热点1:上传底图后如何加热点(点图/按钮),加完的文字字段。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, add_image_module, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级热点1"
IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"

JS = DEEP + """
var res={hotwords:[], inputs:[], img:null};
deepAll(function(n){var t=(n.textContent||'').trim();return t.length<16&&/热点|添加热点|hotspot|点击.*添加|拖.*热点/.test(t);}).forEach(function(n){
  var k=n.tagName+':'+(n.textContent||'').trim().slice(0,14); if(res.hotwords.indexOf(k)<0)res.hotwords.push(k);
});
deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&n.id!=='sc-search-field';}).forEach(function(n){
  var ph=n.placeholder||'',ar=(n.getAttribute&&n.getAttribute('aria-label'))||'';
  if(/搜索|商品描述名称/.test(ph+ar))return; var r=n.getBoundingClientRect&&n.getBoundingClientRect(); if(!(r&&r.width>0))return;
  res.inputs.push({ph:ph,aria:ar});
});
// 找上传后的图片元素(img,大尺寸)
var imgs=deepAll(function(n){return n.tagName==='IMG';}).map(function(n){var r=n.getBoundingClientRect?n.getBoundingClientRect():{};return {w:Math.round(r.width||0),h:Math.round(r.height||0),x:Math.round(r.x||0),y:Math.round(r.y||0)};}).filter(function(o){return o.w>300;});
res.img=imgs;
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
    print("加模块:", add_module_v2(driver, MODULE)); time.sleep(2)
    print("传底图:", add_image_module(driver, IMG, "hotspot base", 0)); time.sleep(3)
    r = driver.execute_script(JS)
    print("热点相关文案/按钮:", r["hotwords"])
    print("输入框:", json.dumps(r["inputs"], ensure_ascii=False))
    print("大图元素(可点坐标的目标):", json.dumps(r["img"], ensure_ascii=False))
    driver.save_screenshot(os.path.join(HERE, "scratch", "hotspot.png"))
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
