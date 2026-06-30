"""核实高级规则轮播的字段结构:导航文本/文本/标题/面板导航,与简单轮播对比。"""
import json, os, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级规则轮播"

JS = DEEP + """
var res={inputs:[], labels:[], imgslots:0};
res.imgslots=deepAll(function(n){return (n.textContent||'').trim()==='点击添加图片';}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;}).length;
deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&n.id!=='sc-search-field';}).forEach(function(n){
  var ph=n.placeholder||''; var ar=(n.getAttribute&&n.getAttribute('aria-label'))||'';
  if(/搜索|商品描述名称/.test(ph+ar)) return;
  var r=n.getBoundingClientRect&&n.getBoundingClientRect();
  if(!(r&&r.width>0)) return;
  res.inputs.push({ph:ph, aria:ar, ml:(n.getAttribute&&n.getAttribute('maxlength'))||''});
});
['导航文本','文本','标题','副标题','正文'].forEach(function(s){
  var c=deepAll(function(n){return (n.textContent||'').trim()===s;}).length; if(c) res.labels.push(s+':'+c);
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
    print("加模块:", add_module_v2(driver, MODULE)); time.sleep(4)
    r = driver.execute_script(JS)
    print("图位数:", r["imgslots"])
    print("可见文本输入框:")
    for x in r["inputs"]: print("  " + json.dumps(x, ensure_ascii=False))
    print("字段标签计数:", r["labels"])
    driver.save_screenshot(os.path.join(HERE, "scratch", "rule_carousel.png"))
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
