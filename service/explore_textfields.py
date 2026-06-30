"""
探查"带文本的单张高级图片"模块的表单字段 DOM,弄清 标题/副标题/正文 如何定位,
为通用"按标签真实键入"做准备。纯观察,不保存。
"""
import json
import os
import time

import yaml

from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "带文本的单张高级图片"

JS_FIELDS = DEEP + """
function nearLabel(el){
  var p=el,d=0;
  while(p&&d<7){
    var host=p.getRootNode&&p.getRootNode().host;
    var prev=p.previousElementSibling;
    while(prev){
      var t=(prev.textContent||'').trim();
      if(t) return t.slice(0,24);
      prev=prev.previousElementSibling;
    }
    p=p.parentNode||host; d++;
  }
  return '';
}
return deepAll(n=>n.tagName==='INPUT'||n.tagName==='TEXTAREA').filter(el=>el.id!=='sc-search-field').map(function(el){
  return {tag:el.tagName,
    label:(el.getAttribute&&el.getAttribute('label'))||'',
    ph:el.placeholder||'',
    aria:(el.getAttribute&&el.getAttribute('aria-label'))||'',
    maxlen:el.getAttribute&&el.getAttribute('maxlength')||'',
    id:el.id||'', val:el.value||'', near:nearLabel(el)};
});
"""


def main():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(max_wait=90):
        print("控制 API 未就绪"); return
    z.update_core()
    oauth = z.amazon_stores(site_id="1")[0].get("browserOauth")
    driver = z.attach(z.open_store(oauth)); driver.implicitly_wait(10)
    out = os.path.join(HERE, "scratch"); os.makedirs(out, exist_ok=True)

    open_premium_editor(driver)
    print("编辑器已就绪")
    print("加模块:", add_module(driver, MODULE))
    time.sleep(4)
    driver.save_screenshot(os.path.join(out, "tf_module.png"))

    fields = driver.execute_script(JS_FIELDS)
    print(f"\n表单字段({len(fields)}):")
    for f in fields:
        print("  " + json.dumps(f, ensure_ascii=False))
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
