"""dump 单图文模块左下角的 左/右 布局图标按钮(无文字、含 svg)。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "带文本的单张高级图片"

JS = DEEP + """
var res=[];
deepAll(function(n){
  var clickable=(n.tagName==='BUTTON'||n.tagName==='KAT-BUTTON'||(n.getAttribute&&n.getAttribute('role')==='button')||(n.onclick));
  var hasSvg=false; try{hasSvg=!!n.querySelector('svg,img,use');}catch(e){}
  var noText=!(n.textContent||'').trim();
  return clickable && hasSvg && noText;
}).forEach(function(n){
  res.push({tag:n.tagName,
    cls:(''+(n.className||'')).slice(0,40),
    aria:(n.getAttribute&&n.getAttribute('aria-label'))||'',
    title:(n.getAttribute&&n.getAttribute('title'))||'',
    pressed:(n.getAttribute&&(n.getAttribute('aria-pressed')||n.getAttribute('aria-checked')))||'',
    html:(n.outerHTML||'').replace(/\\s+/g,' ').slice(0,140)});
});
return res;
"""

def main():
    with open(os.path.join(HERE,"config.yaml")) as f: bc=yaml.safe_load(f)["browser"]
    z=ZiniaoClient(bc["client_path"],bc["webdriver_path"],bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90): print("控制API未就绪"); return
    z.update_core()
    oauth=z.amazon_stores("1")[0].get("browserOauth")
    driver=z.attach(z.open_store(oauth)); driver.implicitly_wait(10)
    open_premium_editor(driver)
    print("加模块:", add_module(driver, MODULE)); time.sleep(4)
    rows=driver.execute_script(JS)
    print(f"图标按钮({len(rows)}):")
    for r in rows: print("  "+json.dumps(r, ensure_ascii=False))
    print("\n完成。窗口保持打开。")

if __name__=="__main__": main()
