"""
攻图片上传:加「高级完整图片」模块 → 点「点击添加图片」→ 找 file input →
send_keys 传一张 dinosaur A+ 图 → 截图看结果(是否出现裁切框/确认)。纯测试,不保存。
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


def find_file_inputs(driver):
    """跨主文档 + 各 iframe 找 input[type=file],返回 [(frame_idx_or_None, element)]。"""
    found = []
    driver.switch_to.default_content()
    for e in driver.find_elements(By.XPATH, '//input[@type="file"]'):
        found.append((None, e))
    n = len(driver.find_elements(By.TAG_NAME, "iframe"))
    for i in range(n):
        driver.switch_to.default_content()
        fl = driver.find_elements(By.TAG_NAME, "iframe")
        if i >= len(fl):
            break
        try:
            driver.switch_to.frame(fl[i])
            for e in driver.find_elements(By.XPATH, '//input[@type="file"]'):
                found.append((i, e))
        except Exception:
            pass
    driver.switch_to.default_content()
    return found


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

    print("测试图存在:", os.path.exists(TEST_IMG), TEST_IMG)
    driver.get(EDITOR_URL); time.sleep(7)

    # 加模块
    driver.find_element(By.XPATH, '//*[contains(text(),"添加模块")]').click(); time.sleep(3)
    boxes = [b for b in driver.find_elements(By.XPATH, '//input[@placeholder="搜索"]')
             if b.get_attribute("id") != "sc-search-field" and b.is_displayed()]
    if boxes:
        boxes[-1].send_keys(MODULE); time.sleep(2)
    driver.execute_script("arguments[0].click();",
                          driver.find_element(By.XPATH, f'//*[normalize-space(text())="{MODULE}"]'))
    time.sleep(4)
    print("已加模块:", MODULE)

    # file input 在点"添加图片"之前可能就已存在(隐藏)
    pre = find_file_inputs(driver)
    print(f"点添加图片前 file input 数: {len(pre)}")

    # 点「点击添加图片」
    try:
        el = driver.find_element(By.XPATH, '//*[contains(text(),"点击添加图片")]')
        driver.execute_script("arguments[0].click();", el)
        time.sleep(4)
        print("已点 点击添加图片")
    except Exception as e:
        print("没找到 点击添加图片:", e)
    driver.switch_to.default_content()
    driver.save_screenshot(os.path.join(out_dir, "upload_1_dialog.png"))

    inputs = find_file_inputs(driver)
    print(f"file input 数: {len(inputs)}")
    if not inputs:
        # dump 弹层文字以了解上传控件形态
        for i in range(len(driver.find_elements(By.TAG_NAME, "iframe")) + 1):
            driver.switch_to.default_content()
            if i > 0:
                try:
                    driver.switch_to.frame(driver.find_elements(By.TAG_NAME, "iframe")[i-1])
                except Exception:
                    continue
            try:
                txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
                lines = list(dict.fromkeys([l.strip() for l in txt.splitlines() if l.strip()]))
                print(f"  [frame {i}] {lines[:30]}")
            except Exception:
                pass
        driver.switch_to.default_content()
        print("\n未找到 file input,看 upload_1_dialog.png。窗口保持。"); return

    # 传图(切到该 input 所在 frame)
    idx, _ = inputs[0]
    driver.switch_to.default_content()
    if idx is not None:
        driver.switch_to.frame(driver.find_elements(By.TAG_NAME, "iframe")[idx])
    fi = driver.find_elements(By.XPATH, '//input[@type="file"]')[0]
    try:
        fi.send_keys(TEST_IMG)
        print("已 send_keys 传图")
    except Exception as e:
        print("send_keys 失败:", e)
    time.sleep(8)
    driver.switch_to.default_content()
    driver.save_screenshot(os.path.join(out_dir, "upload_2_after.png"))
    txt = driver.execute_script("return document.body?document.body.innerText:''") or ""
    print("传后页面关键词:",
          [k for k in ["裁切", "裁剪", "crop", "保存", "确认", "应用", "上传成功", "错误", "尺寸"] if k in txt])
    print("\n窗口保持打开。未保存。")


if __name__ == "__main__":
    main()
