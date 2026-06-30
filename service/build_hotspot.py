"""热点1:传底图 → 在图区按坐标点击加热点 → 填热点文字 → 命名 → 存草稿。"""
import os, time
import yaml
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, add_image_module, click_label, DEEP
from build_generic import set_name

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "高级热点1"
IMG = "/Users/zane/Desktop/dinosaur/A+/ChatGPT Image 2026年6月23日 10_44_19 (1).png"

JS_AREA = DEEP + """
var a=deepAll(function(n){return (n.textContent||'').trim()==='单击任何位置以添加热点';});
if(!a.length) return null;
// 取其可点击的祖先(图区容器),尽量大
var el=a[0],best=a[0],d=0;
while(el&&d<5){var r=el.getBoundingClientRect?el.getBoundingClientRect():{};if(r.width>300&&r.height>150){best=el;break;}el=el.parentElement;d++;}
return best;
"""
JS_EMPTY_INPUTS = DEEP + "return deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&!(n.value||'').trim()&&n.id!=='sc-search-field'&&!/搜索|商品描述名称|替代文本/.test((n.placeholder||'')+((n.getAttribute&&n.getAttribute('aria-label'))||''));}).filter(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();return r&&r.width>0;});"


def main():
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client()
    if not z.wait_ready(90):
        print("控制API未就绪"); return
    z.update_core()
    store = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    driver = z.attach(z.open_store(store.get("browserOauth"))); driver.implicitly_wait(8)
    open_premium_editor(driver)
    print("加模块:", add_module_v2(driver, MODULE)); time.sleep(2)
    print("命名(提前):", set_name(driver, "ZZTEST_hotspot1_" + time.strftime("%H%M%S")))
    print("传底图:", add_image_module(driver, IMG, "hotspot base", 0)); time.sleep(3)

    area = driver.execute_script(JS_AREA)
    if not area:
        print("没找到热点图区"); return
    print("热点图区尺寸:", area.size)
    # 在图区不同位置点击加热点(从中心偏移)
    spots = [(-200, -60), (150, 40)]
    for k, (dx, dy) in enumerate(spots):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", area)
            ActionChains(driver).move_to_element_with_offset(area, dx, dy).click().perform()
            time.sleep(2)
            empties = driver.execute_script(JS_EMPTY_INPUTS)
            print(f"  点热点{k+1} 后空输入框={len(empties)}")
            if empties:
                try:
                    empties[-1].click(); empties[-1].send_keys(f"Feature {k+1}")
                except Exception as e:
                    print("   填热点字异常", e)
        except Exception as e:
            print(f"  点热点{k+1}异常 {e}")
    driver.save_screenshot(os.path.join(HERE, "scratch", "hotspot_done.png"))
    print("保存草稿:", click_label(driver, "保存为草稿"))
    time.sleep(8)
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("URL:", driver.current_url)
    print("结果:", [k for k in ["已保存", "验证失败", "必须填写", "错误", "草稿"] if k in txt])
    print("\n完成。窗口保持打开。")


if __name__ == "__main__":
    main()
