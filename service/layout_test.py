"""验证单图文左右布局开关:模块底部两个 ~100x31 无文字可点击 div。点第二个看图是否换边。"""
import os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, add_image_module, DEEP

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "带文本的单张高级图片"
IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"

# 模块内、无文字、可点击、宽 60~140 高 25~40 的元素(排除 32x32 富文本工具栏),按 y 取最靠下的一对
JS_LAYOUT = DEEP + """
var out=deepAll(function(e){
  var clk=(e.tagName==='BUTTON'||(e.getAttribute&&e.getAttribute('role')==='button')||(e.getAttribute&&e.getAttribute('tabindex')!=null));
  if(!clk) return false;
  if((e.textContent||'').trim().length>3) return false;
  var cls=''+(e.className&&e.className.baseVal!==undefined?e.className.baseVal:(e.className||''));
  if(/ngstrim|ngs-/.test(cls)) return false;
  var r=e.getBoundingClientRect?e.getBoundingClientRect():{};
  return r.width>=60&&r.width<=140&&r.height>=25&&r.height<=40;
});
out.sort(function(a,b){var ra=a.getBoundingClientRect(),rb=b.getBoundingClientRect();return ra.y-rb.y;});
return out;
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
    print("加模块(v2):", add_module_v2(driver, MODULE)); time.sleep(2)
    # 先传图,这样布局变化看得见
    print("传图:", add_image_module(driver, IMG, "layout test", 0)); time.sleep(2)
    els = driver.execute_script(JS_LAYOUT)
    print("候选布局开关数:", len(els))
    if len(els) >= 2:
        pair = els[-2:]  # 最靠下的两个 = 布局对
        for i, e in enumerate(pair):
            print(f"  [{i}] w={e.size['width']} h={e.size['height']} style={ (e.get_attribute('style') or '')[:60]!r}")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pair[0])
        driver.save_screenshot(os.path.join(HERE, "scratch", "layout_before.png"))
        pair[1].click(); time.sleep(2)   # 点右(第二个)
        driver.save_screenshot(os.path.join(HERE, "scratch", "layout_after.png"))
        print("已点第二个布局开关,看 layout_before/after.png")
    print("\n完成。窗口保持打开。")

if __name__ == "__main__":
    main()
