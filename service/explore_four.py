"""探查"高级四图片和文本"的文本字段 DOM(标题/小标题/正文 如何定位)。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级四图片和文本"

JS = DEEP + """
var res={inputs:[],editables:[],labels:[]};
deepAll(n=>(n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&n.id!=='sc-search-field').forEach(function(n){
  res.inputs.push({tag:n.tagName,ph:n.placeholder||'',aria:(n.getAttribute&&n.getAttribute('aria-label'))||'',ml:(n.getAttribute&&n.getAttribute('maxlength'))||'',cls:(''+(n.className||'')).slice(0,30)});
});
deepAll(n=>n.isContentEditable===true).forEach(function(n){
  res.editables.push({tag:n.tagName,cls:(''+(n.className||'')).slice(0,45),dph:(n.getAttribute&&n.getAttribute('data-placeholder'))||'',role:(n.getAttribute&&n.getAttribute('role'))||''});
});
['标题','小标题','正文','正文文本','文本'].forEach(function(s){
  var c=deepAll(n=>(n.textContent||'').trim()===s).length; if(c) res.labels.push(s+':'+c);
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
    driver.save_screenshot(os.path.join(HERE, "scratch", "four_fields.png"))
    r = driver.execute_script(JS)
    print("inputs:")
    for x in r["inputs"]: print("  " + json.dumps(x, ensure_ascii=False))
    print("editables(contenteditable):")
    for x in r["editables"]: print("  " + json.dumps(x, ensure_ascii=False))
    print("labels:", r["labels"])
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
