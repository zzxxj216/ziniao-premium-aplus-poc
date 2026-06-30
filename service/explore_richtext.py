"""探查正文(富文本)编辑器结构:contenteditable / 占位元素 / 工具条。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "带文本的单张高级图片"

JS = DEEP + """
var res=[];
deepAll(n=>n.isContentEditable===true).forEach(function(n){
  res.push({k:'editable',tag:n.tagName,cls:(''+(n.className||'')).slice(0,50),id:n.id||'',role:n.getAttribute&&n.getAttribute('role'),aria:n.getAttribute&&n.getAttribute('aria-label'),dph:n.getAttribute&&n.getAttribute('data-placeholder'),txt:(n.textContent||'').trim().slice(0,20)});
});
deepAll(n=>(n.textContent||'').trim()==='输入正文文本'||(n.getAttribute&&n.getAttribute('placeholder')==='输入正文文本')||(n.getAttribute&&n.getAttribute('data-placeholder')==='输入正文文本')).forEach(function(n){
  res.push({k:'bodyph',tag:n.tagName,cls:(''+(n.className||'')).slice(0,50),id:n.id||'',ce:n.isContentEditable});
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
    for r in driver.execute_script(JS):
        print("  "+json.dumps(r, ensure_ascii=False))
    print("\n完成。窗口保持打开。")

if __name__=="__main__": main()
