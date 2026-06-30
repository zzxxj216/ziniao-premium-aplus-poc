"""确认背景图片模块的图片尺寸要求:加模块 → 点「添加背景图片」→ 抓对话框/图位的尺寸标注。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, both, DEEP, JS_TRIGGERS, JS_ZONES

HERE = os.path.dirname(os.path.abspath(__file__))
JS_DIMS = DEEP + r"""
var seen={},out=[];
var re=/(\d{2,4}\s*[:×x]\s*\d{2,4})|(\d{2,4}\s*px)|min\]/i;
deepAll(function(n){
  var r=n.getBoundingClientRect&&n.getBoundingClientRect(); if(!(r&&r.width>0&&r.height>0))return false;
  var t=(n.textContent||'').trim(); if(t.length<2||t.length>80)return false;
  if(!re.test(t))return false;
  for(var i=0;i<n.children.length;i++){if((n.children[i].textContent||'').trim()===t)return false;}
  return true;
}).forEach(function(n){var t=(n.textContent||'').trim();if(!seen[t]){seen[t]=1;out.push(t);}});
return out;
"""

def main():
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client(); z.wait_ready(90); z.update_core()
    st = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    d = z.attach(z.open_store(st.get("browserOauth"))); d.implicitly_wait(8)
    open_premium_editor(d)
    print("加背景图片:", add_module_v2(d, "包含文本的高级背景图片")); time.sleep(3)
    print("加完模块尺寸标注:", json.dumps(d.execute_script(JS_DIMS), ensure_ascii=False))
    opened = False
    for c in both("添加背景图片"):
        for e in d.execute_script(JS_TRIGGERS, c)[:4]:
            try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", e); e.click()
            except Exception: continue
            t = time.time()+8
            while time.time() < t:
                if d.execute_script(JS_ZONES): opened = True; break
                time.sleep(1)
            if opened: break
        if opened: break
    time.sleep(2)
    print("对话框打开:", opened)
    print("对话框尺寸标注:", json.dumps(d.execute_script(JS_DIMS), ensure_ascii=False))
    d.save_screenshot(os.path.join(HERE, "scratch", "bg_req.png"))
    print("DONE")

if __name__ == "__main__":
    main()
