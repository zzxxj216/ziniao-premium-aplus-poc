# 高级 A+ 自动化 — 模块构建状态

> 更新:2026-06-27。测试店铺:XY(美国站,简体 + English 均验证,内核146);先前 Inkelligent 亦验证过。

## ✅ 健壮性 / 边界(预检 + 加固 + 实测)
- **预检层 `validate.py`**(`validate_spec`,create_aplus 入口调用,不合格不启动浏览器):查 name、模块数≤7、未知类型、图片存在+最小尺寸(用 `sips`)、图片张数、ASIN 格式(10位)、视频 mp4、轮播面板上下限、视频图像轮播每面板需 video。实测多种坏 spec 均被挡 + 清晰报错。
- **`open_premium_editor` 整体重试 3 次**:吃掉瞬时"开始创建没加载/编辑器没就绪"。
- **`bmp()` 剥非 BMP 字符**:emoji 等会让 chromedriver send_keys 整段抛错被跳过 → 现在剥掉 emoji、其余文字正常填(所有用户文本 send_keys 已包 bmp)。
- 真机边界实测:7 模块满载 ✅;超长文案按 maxlength 自动截断 ✅;**希伯来文 RTL** 正常填 ✅;emoji 修复后副标题正常 ✅。
- 仍待:并发 409(server 层,未真机并发测)、虚假但格式合法的 ASIN 在保存时的真实报错、AI 披露(见上)。

### 用户反馈修复(2026-06)
- **图片上传卡死**:曾加"拖拽区消失=成功"的确认,但该 UI 不可靠更新 → 永远确认失败 → 3×90s 重试卡住。已**回退**:上传等 60s(容忍慢)即继续;真正保护改为 **点 Add 后 30s 对话框没关(缺图报错)→ 强制 Cancel 跳过本图**,不卡死后续。verify:2 完整图片干净上传无卡。
- **Q&A 只填 4 对(5 组)**:Q&A 开头有个**无 placeholder 的字段**,positional 填会整体**错位一格**(问/答互换、末答空)。已改:`问答`**按 placeholder 分别填**(问→Enter question / 答→Enter answer,中英候选),verify 5 组全部正确配对。
- **多个相同模块从第2个起加失败 + 搜索框中英来回跳**:add_module_v2 误命中【已添加模块的标题】。已修:`_editor_lang` 一次判语言只搜对应名 + **开库前后差集**只点新磁贴;且"库没开=瞬时→重试,库开了没磁贴才换名"。
- **多模块时轮播文案/图片串进前一个模块**(用户实测:完整图片没给标题→留空标题框,轮播文案填进去了;且简单轮播面板文本框 placeholder = 完整图片标题框 = "Enter headline text",无法靠 placeholder 区分)。已修:**每模块开始前快照"已存在的空字段/空图位"(JS_ALL_EMPTY/JS_BODIES/JS_TRIGGERS),本模块所有填充与传图都排除它们**(_fill_texts/_fill_bodies/_fill_field/_fill_by_ph/_fill_ph_list/add_image_module 全加 exclude)。
- **英文站轮播上传一直失败**:`click_panel` 只认中文「面板(N/」,英文是「**PANEL (1 / 6)**」(大写+斜杠两侧空格)→ 面板2+从不切换→传图失败。已修:click_panel 中英双语。verify:完整图片+简单轮播3面板,完整图片 texts=0(无串扰)、3面板全 image+text。
- **server.py 请求模型丢字段**:旧 Module 模型只认 type/images/texts/bodies,丢掉 video/asins/hotspots/variant/title 等。已改 `modules: list[dict]` 完整透传。

### 图片缩放 + 多轮播(用户实测)
- **固定缩放**:用户要求直接拉伸到精确尺寸(非等比)→ `resize_exact` 用 `sips --resampleHeightWidth 高 宽` 强制到 桌面 1464×600 / 移动 600×450。之前等比缩放使移动图高 337<450 被亚马逊拒(移动端传不上),固定缩放解决。
- **多轮播面板串号**:两个轮播都有「PANEL (1/3)…」标签,click_panel 全页匹配 → 点第2个轮播面板时第1个同号面板也被点。已修:加本轮播前快照已有面板标签,`click_panel(exclude=...)` 只点当前轮播的面板。
- 整篇实测(HTTP):完整图片+轮播×2+完整图片×2 = 5模块,两轮播各3面板全上,保存通过。

### 图片自动缩放(imageprep.py,历史:已被上面的固定缩放取代)
- **等比缩放、不裁剪、整图保留**:`resize_fit(src, tw)` 用 sips `--resampleWidth` 把过宽的图缩到推荐宽度(只缩不放);**永远 --out 写缓存 `.imgcache/`,绝不改源文件**(已验证)。
- create_aplus 上传前自动调用(默认开,`"resize": false` 关);桌面按模块推荐宽度、移动按 600 宽。
- ⚠️ 教训:最初写成 cover+居中裁剪 → 把设计好的横幅裁掉了("显示不全");且一个早期版本误把源文件 image(1) 改小(已改为只写缓存,不再发生)。现在是纯等比缩小。

### 增强(用户需求 2026-06)
- **自定义 alt**:图片项支持 `{"image","mobile","alt"}` 或字符串;`alt` 为图片描述(SEO/算法/无障碍),未给则模块级 `alt`→内容名兜底。add_image_module 已填到对话框的 Alt text。
- **桌面+移动两张图**:一个图位有桌面+移动两个区,add_image_module(`img`+`img_mobile`)分别传(桌面 1464×600 / 移动 600×450);不给 mobile 则复用桌面图。轮播面板支持 `mobile`/`alt`。
- 简单轮播**两个 headline**(模块级 + 每面板)均非必填,不给则留空(实测 panel texts=0 仍可保存)。
- validate 支持字典图片项 + 校验移动图 600×450。verify:完整图片传桌面+移动不同图+自定义alt、轮播面板仅alt无标题,均通过。

## ✅ 双语(简体 / English)—— build_full.TR 表
- 选择器全部"中英都认":`TR` 字典(19 个模块名 + UI 串,英文从真实英文站抓取)+ `both()` 助手。
- 英文站已验证(均保存成功、validation 通过):单图文(keyed)+ 完整图片 + 问答(Add question 加行)+ 多模块 + **对比表2(Enter ASIN)+ 背景图片(Add background image)+ 简单轮播 + 热点1(Click anywhere to add + 坐标点击)+ 全视频(Add Video)**。
- 注意:英文触发区分大小写——视频是「Add Video」(大写 V),图片是「Click to add image」。
- 未在英文站逐一复测但用同套已验证原语:双图/四图/文本/技术规格/规则·导航·视频图像轮播/含文本视频/对比表1·3/热点2。
- 英文关键串:Start creating A+ content / Create Premium A+ / Add Module / Search / Content name / Save as draft / Click to add image / Drag image here / alt text / Add。
- 字段填充改"按字段名 keyed"(title/subtitle/body/nav/img_title),双语 placeholder。
- 修掉 3 个双语 bug:headline 误命中 subheadline(用完整 placeholder)、图片守卫只查中文 trigger、JS_CLICK 未去 label 空格(Save as draft 点不到)。
- `ok` 判存改用语言无关 URL(存后 /content/new/ → /content/<guid>/)。
- 其余模块(轮播/视频/对比表/热点/背景)用同一套已双语化的原语,应可用,个别未在英文站逐一复测。

## ⚠️ AI 图片披露(未解决/待定位)
- 需求:AI 生成图要勾"AI 披露"。已加 `ai_generated`(模块级)开关 + `JS_AI_DISCLOSE`(找附近文本含 generat/生成式/披露 的 checkbox)→ add_image_module 填完 alt、点 Add 前勾选。
- 现状:整个自动化会话里**找不到任何披露 checkbox/toggle/AI文案**(dialog/模块卡片/全页都查过)。
- 根因推测:图片对话框**无 file input**(只能拖拽 hack),拖拽上传**预览不完整渲染**("Uploading…"常驻),披露 UI 可能要预览渲染后才出现;或在 Submit 步。
- 兜底:程序只做草稿,运营手动提交前须自行确认 AI 披露(已写进 SKILL.md)。
- 待用户给披露框截图/原文以精确定位,或确认其在 Submit 步。

## ✅ 19/19 全部模块跑通(经 create_aplus,均保存无验证失败)
完整图片·单图文·双图·四图·文本·背景图片·问答·技术规格·全视频·含文本视频·
轮播(简单/规则/导航/视频图像)·对比表1/2/3·热点1/2。
- 视频:标准 file input(强制可见+send_keys),名称提前设
- 对比表:填 输入ASIN + 产品图 + 图片标题(需真实 ASIN)
- 热点:`hotspots:[{title,body}]`,ActionChains 在底图按坐标点击放置 + Edit Hotspot 填字 + 完成
- 样式开关(布局/黑白/字体色):按宽度区分多对,点 [0]/[1];均纯 DOM,无坐标
- 唯一用坐标的地方 = 热点放置(本就是"在图上点位置")

## 核心机制(全部攻克,稳定)
- 紫鸟启动(直接执行二进制 + webdriver 参数)→ 开店 → CDP 接管 → 登录持久化
- 一步步进高级A+编辑器(内容管理器→开始创建→创建高级A+);按钮用 **kat-button label 包含匹配**(`click_contains`)
- **加模块两条路**:
  - `add_module`(主路):精确文本 + 差集,适合标题是直接文本节点的模块(完整图片/单图文)
  - `add_module_v2`(通用):shadow 搜索过滤 + **selenium 原生点击**磁贴 → 解决"标题在子元素"的难加模块(双图/四图…)。
    **关键:磁贴处理器只认真实事件,JS 合成 `.click()` 无效,必须 selenium 原生点击。**
- 图片:无 file input(原生选择器)→ **拖拽 hack**(注入 input 取 File + 合成 drop);自适应 1~2 图位;等"正在上传"结束
- 文本框:按 placeholder 真实 send_keys(JS 写值不被 kat-input 校验);正文是 **Draft.js**(`div.public-DraftEditor-content`)
- alt 必填:真实键入;名称(kat-input):真实键入 + 回读校验
- 原生弹窗(beforeunload):driver `unhandledPromptBehavior=accept` + `safe_get`
- 跨店可移植:换店只需登录一次 + 后台语言切简体

## 模块 handler 状态
| 模块 | 加模块 | 图片 | 文本 | 保存 | 备注 |
|---|---|---|---|---|---|
| 高级完整图片 | ✅主路 | ✅桌面+移动 | (标题/正文可选) | ✅ | build_full.py,6/6 复现 |
| 带文本的单张高级图片 | ✅主路 | ✅1图 | ✅标题/副标题/正文 | ✅ | build_text_module.py |
| 包含文本的高级双图片 | ✅v2 | ✅左右2图 | ✅2标题+2正文 | ✅ | build_double.py |
| 高级四图片和文本 | ✅v2 | ✅4图 | ✅5框+4正文 | ✅ | build_generic.py;放宽文本检测后跑通 |
| 高级文本 | ✅v2 | — | ✅标题+正文 | ✅ | build_generic.py |
| 其余(轮播/结构/对比/视频…) | (v2 可加) | 测试中 | — | — | 通用 handler 已较强;含面板/加行/ASIN/视频的需补逻辑 |

**通用 handler 文本检测(已放宽)**:可见、空、排除系统/搜索/alt/名称的所有 input/textarea(含无 placeholder 的)+ 所有空 Draft.js 正文。

## 轮播类(build_carousel.py)— 部分跑通
- 面板是 `面板(N/6)` 标签(min2/max6)。默认仅 2 个面板;第 3+ 个需"加面板"动作(尚未实现,故 panel3 无图位)。
- 逐面板"点标签→传图→填文":面板1 OK,面板2 起图上传的「添加」按钮时序不稳(偶 False)。
- **修正认知(探针确认)**:轮播默认就有 **3 个图位同时显示**(堆叠式,非单面板切换);点 `面板(N/6)` 标签图位数不变(3→3)。
  所以**不需要点面板标签**——正确做法 = **通用 handler**(对所有可见"点击添加图片"逐个上传 els[-1] 轮流 + 填所有文本)。
  `build_carousel.py` 的"点标签"是多余且有害的,应弃用,直接用 `build_generic.py` 跑轮播。
- 面板上限 6(面板1/6..6/6 是顶部计数/导航);>3 面板是否需"加面板"待确认(默认3已够多数场景)。
- **只上传1张的真因(已定位)**:通用 handler 用 selenium light-DOM xpath 找"点击添加图片",**只找到第1个**;
  其余图位在 **shadow DOM** 里(探针用 deepAll 穿透才数到 3)。第1面板图+文已成功保存。
- **修法(明确)**:把图位检测/点击改成 **deepAll 穿透 shadow**(返回元素 → selenium 原生点击),
  循环上传所有可见图位。这是轮播完整化的唯一缺口。
- 环境提示:超长会话后 XY 客户端出现瞬时错误(startBrowser 返回 None / 内容管理器加载慢),重跑可过;必要时重启紫鸟。
- **再一层动态行为(已定位)**:shadow 穿透后能数到 3 个图位并传第1个;但**传完1个后另2个图位消失**(候选3→上传1→剩0)。
  说明轮播填完一面板图会切视图/收起其他面板。**多面板完整化的最后一步**:每传完1张后,需重新"露出"下一面板的图位
  (点 `面板(N)` 标签 / 或某"下一张"控件)再传。当前稳定产出 = 1 面板图+文+保存。
- **进展**:逐面板"点面板(N)→等图位(shadow)→传图"已能填 **2/3 面板**(面板1、3 成功;面板2 点标签后图位常=0,显隐不稳)。
- **按钮文本/ASIN 修复(通用)**:fill_text 跳过 maxlength≤14 及标签含 ASIN/按钮/商品编码 的字段(可选短字段,需真实值,误填会超限报错)。
  → 这条对所有模块有益(避免把占位文案塞进短/格式化字段)。
- ✅ **轮播完整跑通(3/3 面板)**:关键修复 = 点 `面板(N)` 标签时**逐个候选元素点到图位出现**(标签有多个重复元素,第一个常点不中);
  每面板:点标签→等图位(shadow JS_IMG_SLOTS)→add_image_module 传图→填文(跳过按钮/ASIN)。`build_carousel.py`。
- **轮播分三类,字段不同,不能照搬**(实测确认):
  - 简单图像轮播:2–6 面板;每面板 图片 + 正文≤200(+可选 按钮文本/ASIN);面板靠「面板(N)」标签导航。
  - 规则轮播:2–**5** 面板;每面板 图片* + **导航文本***(≤25,即面板标签)+ 文本≤20;模块标题≤100。
  - 导航轮播:2–5 面板;每面板 图片* + **导航文本***≤25 + 标题≤50 + 副标题 + 正文≤100。
  - 视频图像轮播:2–6 面板;每面板 图片800:600 + **视频** + 副标题*≤50 + 正文≤500(需视频文件)。
  - 关键:规则/导航轮播每面板**导航文本必填**(简单轮播没有);上限 5。create_aplus 目前只接了简单图像轮播。

## 样式图标开关(已解决,DOM 定位)
部分模块底部有**无文字/无 aria 的样式开关**。它们是 **CSS 背景方块按钮**(无 `<svg>` 子元素),
之前定位不到,是因为我的图标过滤**要求含 svg**,把它们漏了。**改为"找模块内无文字的 styled button"即可,无需坐标。**
- **高级问答 黑底/白底**:模块内两个 `<button>`,内联样式 `width:80px; height:31px; cursor:pointer`;
  点 `[0]`=白底、`[1]`=黑底。**已实测点击生效(背景变黑)**。(toggle_test.py)
- **单图文 图左/图右布局**:模块底部 2 个 `<div role=button>` 100×31(内联 `padding:4px;margin:0 14px 0 0`);
  点 `[0]`=文左图右(默认)、`[1]`=图左文右。**已实测生效(图换到左侧)**。(layout_test.py)
通用定位:**模块底部、无文字、成对、宽~80-100 高~31 的可点击元素**;点 [0]/[1] 选样式。**不要求含 svg。**
- ✅ **已接进 `create_aplus`**:spec 可选 `layout`(图左/图右)、`background`(黑/白);`_set_style` 取底部样式对点 [0]/[1]。
  实测 `单图文 + layout:图左` → texts2/bodies1/**styled:true**/已保存。(aplus_api.py)
  注:`_fill_texts/_fill_bodies` 已加 scrollIntoView,且改为"先填文再传图"(否则传图后输入框被滚出视野点不到)。

## 问答(已扩展)
- 默认 2 组;点「添加问题」可加到 5 组(build_qa.py 验证 4→6→8→10 框全填)。加行套路通用(技术规格"添加规格"同理)。

## 复杂模块的现实
轮播/对比表/技术规格/问答/视频都属"动态行/面板/ASIN/视频"类,每个要单独调且时序脆,产出常是部分。
建议按**实际最常用的模块**优先做扎实,而非追求 19 个全做满。已完整可交付的(图文类5个)已能覆盖大量纯图/图文 A+ 需求。

## 通用 handler(build_generic.py)
`python build_generic.py "<模块名>" [图数上限]`:v2加模块 → 按图位自动上传 → 填所有"内容文本框"+Draft.js正文(占位、按 maxlength 截断) → 命名 → 存草稿。
**局限**:依赖"文本框有 placeholder/aria 且是 input/textarea/Draft.js"。四图这类(字段无 placeholder 或特殊容器)需单独探字段。

## 待办
1. 四图文本字段:逐格探 DOM(小标题/正文的真实定位)后补进 handler
2. 修通用 handler 的图位循环(四图多试了一次第5位,可能扰乱后续填字段)
3. **左右布局开关**(单图文/双图的"图左/图右"图标,仍未定位 selector)
4. 其余模块(轮播/技术规格/问答/对比表/视频)按字段表逐个实现
5. 封装 `create_aplus(asin, [{type, 图/文...}])` 接口 + 运营瘦技能
6. 清理 XY 上的 ZZTEST_* 测试草稿

## 已建测试草稿(XY,待清理)
ZZTEST_singletext_* / ZZTEST_double_* / ZZTEST_高级四图片* / ZZTEST_dinosaur_* 等(均为草稿,未提交)。
