"""探查高级问答的"黑/白背景"切换图标(在模块底部)。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级问答"

JS = DEEP + """
var res={byword:[], icons:[]};
// 1) 带背景/颜色/黑白 字样的元素(label/title/aria/文本)
deepAll(function(n){
  var t=(n.textContent||'').trim();
  var a=(n.getAttribute&&(n.getAttribute('aria-label')||n.getAttribute('title')||n.getAttribute('label')))||'';
  var blob=t+' '+a;
  return /背景|颜色|黑|白|深色|浅色|主题|background|dark|light|theme/i.test(blob) && blob.length<20;
}).forEach(function(n){
  res.byword.push({tag:n.tagName,txt:(n.textContent||'').trim().slice(0,16),aria:(n.getAttribute&&(n.getAttribute('aria-label')||n.getAttribute('title')||n.getAttribute('label')))||'',cls:(''+(n.className||'')).slice(0,30)});
});
// 2) 模块内(祖先含"添加问题")的小图标开关:可点击、无/少文字、含svg/img,排除浏览器壳
var bad=/menu|navigation|favorite|hamburger|header|toolbar|footer|search/i;
deepAll(function(n){
  var ck=(n.tagName==='BUTTON'||n.tagName==='KAT-BUTTON'||(n.getAttribute&&n.getAttribute('role')==='button')||(n.getAttribute&&n.getAttribute('tabindex')!=null));
  if(!ck) return false;
  if(bad.test(''+(n.className||''))) return false;
  if((n.textContent||'').trim().length>3) return false;
  var icon=false; try{icon=!!n.querySelector('svg,img,use,path');}catch(e){}
  if(!icon) return false;
  var p=n,d=0,inmod=false; while(p&&d<12){if((p.textContent||'').indexOf('添加问题')>=0||(p.textContent||'').indexOf('回答')>=0){inmod=true;break;}p=p.parentNode||(p.getRootNode&&p.getRootNode().host);d++;}
  return inmod;
}).forEach(function(n){
  var r=n.getBoundingClientRect?n.getBoundingClientRect():{};
  res.icons.push({tag:n.tagName,cls:(''+(n.className||'')).slice(0,40),y:Math.round(r.y||0),x:Math.round(r.x||0),html:(n.outerHTML||'').replace(/\\s+/g,' ').slice(0,120)});
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
    driver.save_screenshot(os.path.join(HERE, "scratch", "qa_bg.png"))
    r = driver.execute_script(JS)
    print("含背景/黑白字样:", json.dumps(r["byword"], ensure_ascii=False))
    print(f"模块内图标开关({len(r['icons'])}):")
    for x in r["icons"]: print("  " + json.dumps(x, ensure_ascii=False))
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
