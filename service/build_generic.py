"""通用 handler:add_module_v2 加任意模块 → 按图位数自动上传 → 填所有空文本框/正文 → 命名 → 存草稿。
用法: python build_generic.py "高级四图片和文本" [图片数上限]
占位文案;文本按字段 maxlength 截断。"""
import glob, os, sys, time
import yaml
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, add_image_module, click_label, DEEP, JS_NAME_INPUT, JS_IMG_SLOTS

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = "/Users/zane/Desktop/dinosaur"
SAMPLE = "Premium A plus sample content for testing"
BODY = "Premium A+ sample body: durable, waterproof, dishwasher safe, 10 cute designs."

JS_TEXT = DEEP + """
return deepAll(function(n){
  if(n.tagName!=='INPUT'&&n.tagName!=='TEXTAREA') return false;
  if((n.value||'').trim()) return false;
  var r=n.getBoundingClientRect&&n.getBoundingClientRect();
  if(!r||r.width<5||r.height<5) return false;          // 必须可见(排除隐藏/系统输入)
  var id=n.id||'';
  if(id==='sc-search-field'||id.indexOf('footer')===0||id.indexOf('a2z')===0) return false;
  if((''+(n.className||'')).indexOf('ngstrim')>=0) return false;  // 全局搜索
  // 短可选字段(按钮文本≤12 / ASIN≤10)不填,避免超限+这些需真实值
  var ml=n.getAttribute&&n.getAttribute('maxlength'); if(ml&&parseInt(ml)<=14) return false;
  var ph=n.placeholder||''; var ar=(n.getAttribute&&n.getAttribute('aria-label'))||'';
  var bad=['搜索','替代文本','反馈','商品描述名称','ASIN','按钮','商品编码'];
  for(var i=0;i<bad.length;i++){ if(ph.indexOf(bad[i])>=0||ar.indexOf(bad[i])>=0) return false; }
  return true;   // 含无 placeholder 的内容输入框(四图的标题/小标题)
});
"""
JS_BODIES = DEEP + "return deepAll(n=>n.tagName==='DIV'&&n.isContentEditable&&(''+(n.className||'')).includes('public-DraftEditor-content'));"


def fill_text(driver):
    n = 0
    for el in driver.execute_script(JS_TEXT):
        try:
            ml = el.get_attribute("maxlength")
            t = SAMPLE[:int(ml)] if (ml and ml.isdigit()) else SAMPLE[:25]
            el.click(); el.send_keys(t); n += 1
        except Exception:
            pass
    return n


def fill_bodies(driver):
    n = 0
    for el in driver.execute_script(JS_BODIES):
        try:
            if (el.text or "").strip():
                continue
            el.click(); el.send_keys(BODY); n += 1
        except Exception:
            pass
    return n


def set_name(driver, name):
    el = None; e = time.time() + 15
    while time.time() < e and not el:
        el = driver.execute_script(JS_NAME_INPUT); time.sleep(1)
    if not el: return False
    try: driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    except Exception: pass
    try: el.click()
    except Exception: pass
    try:
        el.send_keys(name)
    except Exception:
        return False
    driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));try{arguments[0].blur();}catch(e){}", el)
    return (driver.execute_script("return arguments[0].value", el) or "").strip() != ""


def main():
    module = sys.argv[1] if len(sys.argv) > 1 else "高级四图片和文本"
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    imgs = sorted(glob.glob(os.path.join(FOLDER, "A+", "*.png")))
    name = "ZZTEST_" + "".join(c for c in module if c.isalnum())[:8] + "_" + time.strftime("%H%M%S")
    print(f"模块={module}  草稿名={name}")

    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90):
        print("控制API未就绪"); return
    z.update_core()
    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    print("目标店铺:", store.get("browserName"))
    driver = z.attach(z.open_store(store.get("browserOauth"))); driver.implicitly_wait(8)

    open_premium_editor(driver)
    print("加模块(v2):", add_module_v2(driver, module)); time.sleep(3)

    # 按图位循环上传(自动探测剩余"点击添加图片")
    cnt = 0
    while cnt < cap:
        slots = driver.execute_script(JS_IMG_SLOTS)  # 穿透 shadow,数全所有图位
        if not slots:
            break
        ok = add_image_module(driver, imgs[cnt % len(imgs)], f"img {cnt+1}", cnt)
        print(f"  上传图{cnt}: {ok}")
        if not ok:
            break
        cnt += 1
    print(f"共上传 {cnt} 张")

    print("填文本框:", fill_text(driver))
    print("填正文:", fill_bodies(driver))
    print("命名:", set_name(driver, name))
    print("保存草稿:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    driver.save_screenshot(os.path.join(HERE, "scratch", "generic_done.png"))
    print("URL:", driver.current_url)
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("结果:", [k for k in ["已保存", "验证失败", "必须填写", "错误", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
