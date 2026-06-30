"""调研各模块字段字数上限:逐模块打开编辑器,抓字段 placeholder + 字数计数器(如 '80 / 80')。"""
import json, os, time
import yaml
from ziniao_client import ZiniaoClient
from build_full import open_premium_editor, add_module_v2, click_contains, DEEP
from build_generic import JS_TEXT

HERE = os.path.dirname(os.path.abspath(__file__))
MODULES = [
    "高级完整图片", "带文本的单张高级图片", "包含文本的高级双图片", "高级四图片和文本",
    "高级文本", "包含文本的高级背景图片", "高级问答", "高级技术规格",
    "高级、简单的图像轮播", "高级规则轮播", "高级导航轮播", "优质视频图像轮播",
    "包含文本的高级视频", "高级比较表1", "高级比较表2", "高级比较表3", "高级热点1", "高级热点2",
]
# 加几行(问答/技术规格)以露出更多字段
ROW = {"高级问答": "添加问题", "高级技术规格": "添加规格"}

# 抓"字段标签+字数上限"叶子:文本里含 'NN / NN' 计数器
JS_LIMITS = DEEP + r"""
var seen={},out=[];
deepAll(function(n){
  var r=n.getBoundingClientRect&&n.getBoundingClientRect(); if(!(r&&r.width>0&&r.height>0))return false;
  var t=(n.textContent||'').trim(); if(t.length<3||t.length>60)return false;
  if(!/\d{1,4}\s*\/\s*\d{1,4}/.test(t))return false;        // 含计数器
  for(var i=0;i<n.children.length;i++){if((n.children[i].textContent||'').trim()===t)return false;}
  return true;
}).forEach(function(n){var t=(n.textContent||'').trim();if(!seen[t]){seen[t]=1;out.push(t);}});
return out;
"""
JS_PH = DEEP + "var o=[];deepAll(function(n){return (n.tagName==='INPUT'||n.tagName==='TEXTAREA');}).forEach(function(n){var r=n.getBoundingClientRect&&n.getBoundingClientRect();if(!(r&&r.width>0))return;var p=n.placeholder||'';if(p&&p.toLowerCase().indexOf('search')<0&&o.indexOf(p)<0)o.push(p);});return o;"


def main():
    with open(os.path.join(HERE, "config.yaml")) as f:
        bc = yaml.safe_load(f)["browser"]
    z = ZiniaoClient(bc["client_path"], bc["webdriver_path"], bc["socket_port"])
    z.download_driver(); z.kill_client(); z.start_client(); z.wait_ready(90); z.update_core()
    st = z.store_by_name(os.environ.get("ZINIAO_STORE", "XY"))
    d = z.attach(z.open_store(st.get("browserOauth"))); d.implicitly_wait(8)
    results = {}
    for mod in MODULES:
        try:
            open_premium_editor(d)
            ok = add_module_v2(d, mod); time.sleep(3)
            if mod in ROW:                          # 多点几次加行,露出问答/规格字段
                for _ in range(2):
                    click_contains(d, ROW[mod], 5); time.sleep(1)
            limits = d.execute_script(JS_LIMITS)
            phs = d.execute_script(JS_PH)
            results[mod] = {"counters": limits, "placeholders": phs}
            print(f"### {mod}\n   计数器: {json.dumps(limits, ensure_ascii=False)}\n   字段: {json.dumps(phs, ensure_ascii=False)}")
        except Exception as e:
            results[mod] = {"err": str(e)}
            print(f"### {mod}: 异常 {e}")
    open(os.path.join(HERE, "scratch", "text_limits.json"), "w").write(json.dumps(results, ensure_ascii=False, indent=2))
    print("\nDONE")


if __name__ == "__main__":
    main()
