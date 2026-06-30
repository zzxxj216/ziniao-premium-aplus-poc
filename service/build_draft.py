"""
端到端跑通(单模块,健壮版):加 高级完整图片 → 拖拽上传桌面+移动图 → 填 alt →
对话框「添加」→ 精准键入名称 →「保存为草稿」→ 验证。
要点:每步显式等待/重试;名称走 kat-input 内部 input 真实键入。
会在账号生成测试草稿 ZZTEST_*。
"""
import os
import time

import yaml
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ziniao_client import ZiniaoClient

HERE = os.path.dirname(os.path.abspath(__file__))
EDITOR_URL = "https://sellercentral.amazon.com/enhanced-content/content-manager/workflow/ebc-premium/content/new/edit"
IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"
MODULE = "高级完整图片"
NAME = "ZZTEST_dinosaur_" + time.strftime("%m%d_%H%M%S")

DEEP = """
function deepAll(test){const acc=[];function walk(root){let ns;try{ns=root.querySelectorAll('*');}catch(e){return;}
ns.forEach(n=>{try{if(test(n))acc.push(n);}catch(e){}
if(n.shadowRoot)walk(n.shadowRoot);
if(n.tagName==='IFRAME'){try{if(n.contentDocument)walk(n.contentDocument);}catch(e){}}});}
walk(document);return acc;}
"""
JS_NAME_INPUT = DEEP + """
function inner(h){if(!h)return null;if(h.tagName==='INPUT')return h;
if(h.shadowRoot){var i=h.shadowRoot.querySelector('input');if(i)return i;}
return h.querySelector?h.querySelector('input'):null;}
var hosts=deepAll(n=>{var l=(n.getAttribute&&(n.getAttribute('label')||n.getAttribute('aria-label')||''))||'';return l.includes('商品描述名称');});
for(var k=0;k<hosts.length;k++){var i=inner(hosts[k]);if(i)return i;}
var ins=deepAll(n=>n.tagName==='INPUT'&&n.id!=='sc-search-field'&&!((n.placeholder||'').match(/搜索|替代文本/)));
for(var j=0;j<ins.length;j++){var p=ins[j],d=0;while(p&&d<8){var t=(p.textContent||'')+((p.host&&p.host.textContent)||'');if(t.includes('商品描述名称'))return ins[j];p=p.parentNode||p.host;d++;}}
return null;
"""
JS_ZONES = DEEP + "return deepAll(n=>(n.textContent||'').includes('拖到这里')).sort((a,b)=>a.textContent.length-b.textContent.length);"
JS_INJECT = "var i=document.createElement('input');i.type='file';i.id='__sel_up__';i.style.cssText='position:fixed;left:0;top:0;opacity:0;z-index:99999';document.body.appendChild(i);return i;"
JS_DROP = DEEP + """
var input=document.getElementById('__sel_up__');var target=arguments[0];
if(!input||!input.files.length)return 'no-file';
var dt=new DataTransfer();dt.items.add(input.files[0]);
['dragenter','dragover','drop'].forEach(t=>target.dispatchEvent(new DragEvent(t,{bubbles:true,cancelable:true,composed:true,dataTransfer:dt})));
return 'dropped';
"""
JS_ALTS = DEEP + """
var n=0;deepAll(el=>el.tagName==='INPUT'&&(el.placeholder||'').includes('替代文本')).forEach(function(el){
if((el.value||'').trim()){n++;return;}
var set=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(el),'value').set;
set.call(el,'dinosaur name labels A+');el.dispatchEvent(new Event('input',{bubbles:true}));
el.dispatchEvent(new Event('change',{bubbles:true}));n++;});return n;
"""
JS_CLICK = DEEP + """
var label=arguments[0];
function lbl(n){var l=(n.getAttribute&&(n.getAttribute('label')||n.getAttribute('aria-label')))||'';return l.replace(/\\s/g,'');}
var c=deepAll(n=>{var t=(n.textContent||'').replace(/\\s/g,'');var ok=(n.tagName==='BUTTON'||n.tagName==='KAT-BUTTON'||n.tagName==='A'||(n.getAttribute&&n.getAttribute('role')==='button'));return ok&&!n.disabled&&(lbl(n)===label||t===label);});
if(c.length){c[c.length-1].click();return true;}return false;
"""
JS_HAS = DEEP + "var s=arguments[0];return deepAll(n=>(n.textContent||'').includes(s)).length>0;"


def wait_xpath(driver, xp, t=25):
    return WebDriverWait(driver, t).until(EC.presence_of_element_located((By.XPATH, xp)))


def deep_get(driver, js, t=25, *args):
    end = time.time() + t
    while time.time() < end:
        r = driver.execute_script(js, *args)
        if r:
            return r
        time.sleep(1)
    return None


def click_label(driver, label, t=25):
    end = time.time() + t
    while time.time() < end:
        if driver.execute_script(JS_CLICK, label):
            return True
        time.sleep(1.5)
    return False


def main():
    with open(os.path.join(HERE, "config.yaml"), "r", encoding="utf-8") as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(max_wait=90):
        print("控制 API 未就绪"); return
    z.update_core()
    oauth = z.amazon_stores(site_id="1")[0].get("browserOauth")
    driver = z.attach(z.open_store(oauth)); driver.implicitly_wait(8)
    out = os.path.join(HERE, "scratch"); os.makedirs(out, exist_ok=True)

    driver.get(EDITOR_URL)
    wait_xpath(driver, '//*[contains(text(),"添加模块")]')   # 等编辑器就绪
    print("编辑器已就绪")

    # 1) 加模块(重试打开模块库,不强依赖搜索框)
    def add_module(module):
        tile_xp = f'//*[normalize-space(text())="{module}"]'
        for attempt in range(4):
            try:
                btns = driver.find_elements(By.XPATH, '//*[normalize-space(text())="添加模块"]')
                (btns[-1] if btns else driver.find_element(By.XPATH, '//*[contains(text(),"添加模块")]')).click()
            except Exception:
                pass
            end = time.time() + 10
            while time.time() < end:
                box = [b for b in driver.find_elements(By.XPATH, '//input[@placeholder="搜索"]')
                       if b.get_attribute("id") != "sc-search-field" and b.is_displayed()]
                tiles = driver.find_elements(By.XPATH, tile_xp)
                if box and not tiles:
                    try: box[0].send_keys(module); time.sleep(2)
                    except Exception: pass
                    tiles = driver.find_elements(By.XPATH, tile_xp)
                if tiles:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});arguments[0].click();", tiles[0])
                    return True
                time.sleep(1)
            print(f"  (加模块重试 {attempt+1})")
        return False

    print("已加模块:" if add_module(MODULE) else "加模块失败:", MODULE)

    # 2) 打开图片对话框
    wait_xpath(driver, '//*[contains(text(),"点击添加图片")]')
    driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, '//*[contains(text(),"点击添加图片")]'))

    # 3) 上传桌面+移动图
    inj = deep_get(driver, JS_INJECT) or driver.execute_script(JS_INJECT)
    for slot in ("桌面", "移动"):
        zones = deep_get(driver, JS_ZONES, 20)
        if not zones:
            print(f"{slot}图:无拖拽区"); break
        driver.execute_script("var i=document.getElementById('__sel_up__');if(i)i.value='';")
        inj.send_keys(IMG); time.sleep(1)
        print(f"{slot}图 drop:", driver.execute_script(JS_DROP, zones[0]))
        time.sleep(14)
    print("填 alt:", driver.execute_script(JS_ALTS)); time.sleep(1)

    # 4) 对话框「添加」,并等对话框关闭
    print("点[添加]:", click_label(driver, "添加"))
    end = time.time() + 20
    while time.time() < end and driver.execute_script(JS_HAS, "拖到这里"):
        time.sleep(1)
    print("图片对话框已关闭:", not driver.execute_script(JS_HAS, "拖到这里"))
    driver.save_screenshot(os.path.join(out, "draft_1_module.png"))

    # 5) 精准键入名称(kat-input 内部 input)
    name_el = deep_get(driver, JS_NAME_INPUT, 15)
    if name_el:
        try: name_el.click()
        except Exception: pass
        name_el.send_keys(NAME)
        driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));try{arguments[0].blur();}catch(e){}", name_el)
        val = driver.execute_script("return arguments[0].value", name_el)
        print(f"名称已键入,回读: {val!r}")
    else:
        print("未找到名称输入框")

    # 6) 保存为草稿
    print("点[保存为草稿]:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(out, "draft_2_saved.png"))
    print("落地 URL:", driver.current_url)
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("结果关键词:", [k for k in ["验证失败", "已保存", "成功", "错误", "失败", "必须填写", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
