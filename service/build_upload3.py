"""
拖拽上传 hack:注入自有 input 取真实 File → 合成 drop 事件丢到拖拽区(穿透 shadow DOM)。
目标模块 高级完整图片。填 alt、点「添加」均走 shadow 穿透 JS。截图验证。不保存草稿。
"""
import os
import time

import yaml
from selenium.webdriver.common.by import By

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager/workflow/ebc-premium/content/new/edit"
TEST_IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"
MODULE = "高级完整图片"

# 穿透 shadow DOM + 同源 iframe 的通用收集器
DEEP = """
function deepAll(test){
  const acc=[];
  function walk(root){
    let ns; try{ns=root.querySelectorAll('*');}catch(e){return;}
    ns.forEach(n=>{
      try{ if(test(n)) acc.push(n); }catch(e){}
      if(n.shadowRoot) walk(n.shadowRoot);
      if(n.tagName==='IFRAME'){ try{ if(n.contentDocument) walk(n.contentDocument);}catch(e){} }
    });
  }
  walk(document);
  return acc;
}
"""

JS_DROPZONES = DEEP + """
return deepAll(n => (n.textContent||'').includes('拖到这里'))
  .map(n=>n)
  .sort((a,b)=>(a.textContent.length-b.textContent.length));
"""

JS_INJECT = """
var i=document.createElement('input');
i.type='file'; i.id='__sel_up__';
i.style.cssText='position:fixed;left:0;top:0;opacity:0;z-index:99999';
document.body.appendChild(i); return i;
"""

JS_DROP = DEEP + """
var input=document.getElementById('__sel_up__');
var target=arguments[0];
if(!input || !input.files.length){ return 'no-file'; }
var dt=new DataTransfer();
dt.items.add(input.files[0]);
['dragenter','dragover','drop'].forEach(function(t){
  target.dispatchEvent(new DragEvent(t,{bubbles:true,cancelable:true,composed:true,dataTransfer:dt}));
});
return 'dropped';
"""

JS_SET_ALTS = DEEP + """
var alts=deepAll(n=>n.tagName==='INPUT' && (n.placeholder||'').includes('替代文本'));
var n=0;
alts.forEach(function(el){
  var set=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value').set;
  set.call(el, 'dinosaur A+ test');
  el.dispatchEvent(new Event('input',{bubbles:true}));
  el.dispatchEvent(new Event('change',{bubbles:true})); n++;
});
return n;
"""

JS_CLICK_ADD = DEEP + """
var btns=deepAll(n=>n.tagName==='BUTTON' && n.textContent.trim()==='添加');
if(btns.length){ btns[btns.length-1].click(); return true; } return false;
"""


def main():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver()
    z.kill_client(); z.start_client()
    if not z.wait_ready(max_wait=90):
        print("控制 API 未就绪"); return
    z.update_core()
    oauth = z.amazon_stores(site_id="1")[0].get("browserOauth")
    driver = z.attach(z.open_store(oauth))
    driver.implicitly_wait(12)
    out_dir = os.path.join(HERE, "scratch"); os.makedirs(out_dir, exist_ok=True)

    driver.get(EDITOR_URL); time.sleep(7)
    driver.find_element(By.XPATH, '//*[contains(text(),"添加模块")]').click(); time.sleep(3)
    boxes = [b for b in driver.find_elements(By.XPATH, '//input[@placeholder="搜索"]')
             if b.get_attribute("id") != "sc-search-field" and b.is_displayed()]
    if boxes:
        boxes[-1].send_keys(MODULE); time.sleep(2)
    driver.execute_script("arguments[0].click();",
                          driver.find_element(By.XPATH, f'//*[normalize-space(text())="{MODULE}"]'))
    time.sleep(4)
    driver.execute_script("arguments[0].click();",
                          driver.find_element(By.XPATH, '//*[contains(text(),"点击添加图片")]'))
    time.sleep(4)

    zones = driver.execute_script(JS_DROPZONES)
    print(f"拖拽区候选: {len(zones)} 个")
    if not zones:
        driver.save_screenshot(os.path.join(out_dir, "dnd_nozone.png"))
        print("没找到拖拽区,看 dnd_nozone.png"); return

    # 注入 input 取 File
    inj = driver.execute_script(JS_INJECT)
    inj.send_keys(TEST_IMG)
    time.sleep(1)
    # 丢到桌面图拖拽区(最短 textContent 那个)
    r = driver.execute_script(JS_DROP, zones[0])
    print("drop 结果:", r)
    time.sleep(8)
    driver.save_screenshot(os.path.join(out_dir, "dnd_1_desktop.png"))

    # 移动图:重新找拖拽区(桌面传完后剩移动图区)
    zones2 = driver.execute_script(JS_DROPZONES)
    if zones2:
        driver.execute_script("var i=document.getElementById('__sel_up__'); if(i) i.value='';")
        inj.send_keys(TEST_IMG); time.sleep(1)
        print("移动图 drop:", driver.execute_script(JS_DROP, zones2[0]))
        time.sleep(8)
    driver.save_screenshot(os.path.join(out_dir, "dnd_2_mobile.png"))

    print("填 alt 数:", driver.execute_script(JS_SET_ALTS))
    time.sleep(1)
    print("点添加:", driver.execute_script(JS_CLICK_ADD))
    time.sleep(5)
    driver.save_screenshot(os.path.join(out_dir, "dnd_3_module.png"))
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("结果关键词:", [k for k in ["错误", "失败", "尺寸", "替代文本", "保存为草稿", "预览"] if k in txt])
    print("\n窗口保持打开。未保存草稿。")


if __name__ == "__main__":
    main()
