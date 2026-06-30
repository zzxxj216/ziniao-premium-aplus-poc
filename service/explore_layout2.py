"""精准定位单图文模块的 左/右 布局图标(排除紫鸟浏览器壳)。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "带文本的单张高级图片"

JS = DEEP + """
var bad=/menu|navigation|favorite|hamburger|header|toolbar|footer|search|tab-|sidebar|toptab/i;
var res=[];
deepAll(function(n){
  var clickable=(n.tagName==='BUTTON'||n.tagName==='KAT-BUTTON'||n.tagName==='A'
    ||(n.getAttribute&&n.getAttribute('role')==='button')
    ||(n.getAttribute&&n.getAttribute('tabindex')!=null)||n.onclick);
  if(!clickable) return false;
  var cls=''+(n.className||'');
  if(bad.test(cls)) return false;
  var icon=false; try{icon=!!n.querySelector('svg,img,use,path,canvas');}catch(e){}
  if(!icon) return false;
  if((n.textContent||'').trim().length>3) return false;
  // 必须在含模块字段的子树里(祖先文本出现 800:600 或 正文文本)
  var p=n,d=0,inModule=false;
  while(p&&d<12){var t=(p.textContent||'');if(t.indexOf('800:600')>=0||t.indexOf('正文文本')>=0){inModule=true;break;}p=p.parentNode||(p.getRootNode&&p.getRootNode().host);d++;}
  return inModule;
}).forEach(function(n){
  res.push({tag:n.tagName, cls:(''+(n.className||'')).slice(0,60),
    parent:(''+((n.parentElement&&n.parentElement.className)||'')).slice(0,50),
    aria:(n.getAttribute&&n.getAttribute('aria-label'))||'',
    sel:(n.getAttribute&&(n.getAttribute('aria-selected')||n.getAttribute('aria-pressed')))||'',
    html:(n.outerHTML||'').replace(/\\s+/g,' ').slice(0,160)});
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
    print(f"模块内图标按钮({len(rows)}):")
    for r in rows: print("  "+json.dumps(r, ensure_ascii=False))
    print("\n完成。窗口保持打开。")

if __name__=="__main__": main()
