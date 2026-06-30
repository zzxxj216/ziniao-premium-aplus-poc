"""探查"带文本的单张高级图片"的 左/右 布局控件(图左文右 / 图右文左)。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "带文本的单张高级图片"
KW = ["左", "右", "位置", "对齐", "布局", "翻转", "侧"]

JS = DEEP + """
var kw=arguments[0];var res=[];
deepAll(function(n){
  var t=(n.textContent||'').trim();
  var lab=(n.getAttribute&&(n.getAttribute('label')||n.getAttribute('aria-label')||n.getAttribute('title')))||'';
  var blob=t+' '+lab;
  var hit=kw.some(k=>blob.indexOf(k)>=0);
  var small=t.length<24;
  var ctrl=['BUTTON','KAT-BUTTON','KAT-RADIOBUTTON','KAT-TOGGLE','KAT-CHECKBOX','INPUT','LABEL','KAT-RADIOGROUP'].indexOf(n.tagName)>=0;
  return hit && (small||lab) && (ctrl||lab||n.getAttribute&&n.getAttribute('role'));
}).forEach(function(n){
  res.push({tag:n.tagName, txt:(n.textContent||'').trim().slice(0,24),
    label:(n.getAttribute&&(n.getAttribute('label')||n.getAttribute('aria-label')||n.getAttribute('title')))||'',
    role:n.getAttribute&&n.getAttribute('role'), checked:n.getAttribute&&n.getAttribute('checked'),
    cls:(''+(n.className||'')).slice(0,30)});
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
    driver.save_screenshot(os.path.join(HERE,"scratch","leftright.png"))
    rows=driver.execute_script(JS, KW)
    print(f"命中控件({len(rows)}):")
    for r in rows: print("  "+json.dumps(r, ensure_ascii=False))
    print("\n完成。窗口保持打开。")

if __name__=="__main__": main()
