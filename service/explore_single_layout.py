"""找单图文的左右布局开关:模块内无文字的样式 button(不要求 svg)。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "带文本的单张高级图片"

JS = DEEP + """
// 锁定模块卡片:含 '点击添加图片' 且 '标题',textContent 最短
var cards=deepAll(function(n){var t=n.textContent||'';return t.indexOf('点击添加图片')>=0&&t.indexOf('标题')>=0;})
  .sort(function(a,b){return a.textContent.length-b.textContent.length;});
if(!cards.length) return {err:'no-card'};
var card=cards[0];
var all=[]; function descend(r){try{r.querySelectorAll('*').forEach(function(e){all.push(e);if(e.shadowRoot)descend(e.shadowRoot);});}catch(x){}} descend(card);
var out=[];
all.forEach(function(e){
  var clk=(e.tagName==='BUTTON'||(e.getAttribute&&e.getAttribute('role')==='button')||(e.getAttribute&&e.getAttribute('tabindex')!=null));
  if(!clk) return;
  if((e.textContent||'').trim().length>3) return;     // 无文字
  var cls=''+(e.className&&e.className.baseVal!==undefined?e.className.baseVal:(e.className||''));
  if(/ngstrim|ngs-/.test(cls)) return;
  var st=(e.getAttribute&&e.getAttribute('style'))||'';
  var r=e.getBoundingClientRect?e.getBoundingClientRect():{};
  out.push({tag:e.tagName, aria:(e.getAttribute&&(e.getAttribute('aria-label')||e.getAttribute('title')))||'',
    cls:cls.slice(0,40), style:st.slice(0,90), y:Math.round(r.y||0), x:Math.round(r.x||0), w:Math.round(r.width||0), h:Math.round(r.height||0)});
});
out.sort(function(a,b){return a.y-b.y;});
return {count:out.length, items:out};
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
    r = driver.execute_script(JS)
    if r.get("err"): print("没锁定卡片"); return
    print(f"模块内无文字可点击元素({r['count']}):")
    for x in r["items"]: print("  " + json.dumps(x, ensure_ascii=False))
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
