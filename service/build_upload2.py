"""
真上传:高级完整图片 → 点击添加图片 → JS 深搜(穿透 shadow DOM)file input →
send_keys 桌面图+移动图(同一张测试图)→ 填 alt → 点「添加」→ 截图。不保存草稿。
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

JS_FIND_FILE = """
const acc=[];
function walk(root){
  try{ root.querySelectorAll('input[type=file]').forEach(e=>acc.push(e)); }catch(e){}
  try{ root.querySelectorAll('*').forEach(e=>{ if(e.shadowRoot) walk(e.shadowRoot); }); }catch(e){}
}
walk(document);
return acc;
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

    inputs = driver.execute_script(JS_FIND_FILE)
    print(f"深搜到 file input: {len(inputs)} 个")
    if not inputs:
        driver.save_screenshot(os.path.join(out_dir, "upload_fail.png"))
        print("仍无 file input,看 upload_fail.png"); return

    # 桌面图
    inputs[0].send_keys(TEST_IMG); print("桌面图已传"); time.sleep(6)
    # 移动图(若有第二个 input)
    inputs2 = driver.execute_script(JS_FIND_FILE)
    if len(inputs2) >= 2:
        try:
            inputs2[1].send_keys(TEST_IMG); print("移动图已传"); time.sleep(6)
        except Exception as e:
            print("移动图传失败:", e)

    driver.save_screenshot(os.path.join(out_dir, "upload_2_uploaded.png"))

    # 填 alt 文本
    alts = [a for a in driver.find_elements(By.XPATH, '//input[@placeholder="输入替代文本"]') if a.is_displayed()]
    print(f"alt 输入框: {len(alts)} 个")
    for a in alts:
        try:
            a.clear(); a.send_keys("dinosaur A+ test image")
        except Exception:
            pass
    time.sleep(1)

    # 点对话框「添加」
    try:
        btns = [b for b in driver.find_elements(By.XPATH, '//button[normalize-space(.)="添加"]') if b.is_displayed()]
        if btns:
            driver.execute_script("arguments[0].click();", btns[-1]); print("已点 添加"); time.sleep(5)
    except Exception as e:
        print("点添加失败:", e)

    driver.save_screenshot(os.path.join(out_dir, "upload_3_module.png"))
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("结果关键词:", [k for k in ["错误", "失败", "尺寸", "成功", "替代文本", "保存为草稿"] if k in txt])
    print("\n窗口保持打开。未保存草稿。")


if __name__ == "__main__":
    main()
