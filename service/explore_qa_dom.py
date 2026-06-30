"""只在'高级问答'模块卡片子树内(穿透 shadow)dump 图标/可点击元素,找黑白背景开关的稳定 DOM 选择器。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级问答"

JS = DEEP + """
// 1) 锁定模块卡片:同时含 '高级问答' 和 '添加问题'、textContent 最短的元素
var cards=deepAll(function(n){var t=n.textContent||'';return t.indexOf('高级问答')>=0&&t.indexOf('添加问题')>=0;})
  .sort(function(a,b){return a.textContent.length-b.textContent.length;});
if(!cards.length) return {err:'no-card'};
var card=cards[0];
// 2) 卡片子树(light+shadow)全收集
var all=[];
function descend(root){ try{root.querySelectorAll('*').forEach(function(e){all.push(e); if(e.shadowRoot) descend(e.shadowRoot);});}catch(x){} }
descend(card);
// 3) 只留图标/可点击,排除 ngstrim/ngs 浏览器壳
var out=[];
all.forEach(function(e){
  var cls=''+(e.className&&e.className.baseVal!==undefined?e.className.baseVal:(e.className||''));
  if(/ngstrim|ngs-/.test(cls)) return;
  var svg=false; try{svg=!!e.querySelector('svg,img,use');}catch(x){}
  var clk=(e.tagName==='BUTTON'||e.tagName==='KAT-BUTTON'||(e.getAttribute&&e.getAttribute('role'))||(e.getAttribute&&e.getAttribute('tabindex')!=null));
  if(!svg&&!clk) return;
  if((e.textContent||'').trim().length>6) return;   // 排除带较多文字的(只要图标)
  var r=e.getBoundingClientRect?e.getBoundingClientRect():{};
  out.push({tag:e.tagName,cls:cls.slice(0,60),role:(e.getAttribute&&e.getAttribute('role'))||'',
    aria:(e.getAttribute&&(e.getAttribute('aria-label')||e.getAttribute('title')))||'',
    sel:(e.getAttribute&&(e.getAttribute('aria-pressed')||e.getAttribute('aria-checked')||e.getAttribute('aria-selected')))||'',
    svg:svg, y:Math.round(r.y||0), w:Math.round(r.width||0),
    html:(e.outerHTML||'').replace(/\\s+/g,' ').slice(0,110)});
});
out.sort(function(a,b){return a.y-b.y;});
return {cardLen:card.textContent.length, count:out.length, items:out.slice(0,40)};
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
    r = driver.execute_script(JS)
    if r.get("err"):
        print("没锁定到卡片"); return
    print(f"卡片文本长度={r['cardLen']}  卡片内图标/可点击元素={r['count']}(按 y 排序,取前40):")
    for x in r["items"]:
        print("  " + json.dumps(x, ensure_ascii=False))
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
