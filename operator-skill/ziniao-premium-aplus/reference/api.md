# 接口契约

中心服务部署在装了紫鸟的公共电脑上。所有请求带头 `X-API-Key: {APLUS_API_KEY}`。

## GET /health
探活 + 看支持的模块。
返回:`{"ok": true, "supported_modules": ["完整图片","单图文","双图","四图","文本"]}`

## GET /aplus/status
查看中心服务是否正在创建任务。用于遇到 `409` 时判断是正常忙碌还是需要稍后重试。

请求头同样带 `X-API-Key`。
返回:
```json
{
  "ok": true,
  "busy": false,
  "name": null,
  "running_seconds": 0,
  "timeout_seconds": 1200
}
```

## POST /aplus/create
创建一篇高级 A+ 草稿。

### 请求体(JSON)
> `modules` 可放**多个模块**(任意类型混合,按顺序排版进同一篇);**一篇最多 7 个**(亚马逊上限),勿超。
```json
{
  "store": "XY",                         // 紫鸟店铺名;省略则用服务端默认店铺
  "name": "商品描述名称(必填)",
  "modules": [
    {
      "type": "完整图片",                 // 19 类之一,见下方"模块类型"
      "images": [{"desktop":"/d.png","mobile":"/m.png","alt":"图片描述"}], // 见下"图片格式";也可简写 ["/d.png"]
      "alt":    "整模块统一图片描述",       // 可选,图片未单独给 alt 时的兜底
      "texts":  ["标题"],                 // 文本框,按 DOM 顺序填(标题/副标题/小标题/导航文本…)
      "bodies": ["正文"],                 // 正文(Draft.js 富文本),按顺序填
      "video":  "/abs/path/v.mp4",        // 视频模块用
      "asins":  ["B0..."],               // 对比表用(真实 ASIN)
      "img_titles": ["产品名"],           // 对比表2 图片标题
      "hotspots": [{"title":"","body":""}], // 热点模块用(图上铺开放置)
      "variant": "简单",                  // 轮播用:简单|规则|导航|视频图像
      "title":   "模块标题",              // 轮播模块级标题
      "panels":  [{"desktop":"","mobile":"","alt":"图片描述","video":"","texts":[]}], // 轮播每面板
      "layout":  "图左",                  // 可选样式:图左|图右(单图文/双图/背景)
      "font_color": "黑",                 // 可选样式:白|黑(背景图片字色)
      "background": "黑"                  // 可选样式:白|黑(问答背景)
    }
  ]
}
```

**图片:alt + 桌面/移动两张图(重要)**
- 每个图位有**桌面 + 移动**两个区。图片项可简写 `"/d.png"`,或完整写 `{"desktop":"/d.png","mobile":"/m.png","alt":"描述"}`。
- `desktop` 是桌面图字段;旧字段 `image` 仍兼容,两者等价。单图模块也可直接写顶层 `"desktop":"/d.png","mobile":"/m.png"`。
- `alt`:**图片描述,务必给**(亚马逊算法/无障碍/审核都看)。未单独给则用模块级 `alt`,再兜底用内容名。
- `mobile`:移动端图(**600×450**);不给则移动端复用桌面图。桌面图横幅类建议 **1464×600**。
- 标题/副标题等**非必填**:不需要就不给(留空);但 **alt 建议每张都给**。

**推荐:按字段名填(更稳,不怕顺序错/改版)**
除了 `texts`/`bodies`(按顺序),更推荐用**命名字段**,程序按字段的 placeholder 精确填(中英双语匹配):
- `title`(标题)、`subtitle`(副标题)、`body`(正文)、`nav`(导航文本)、`img_title`(图片标题)
- 单值或列表都行(多栏/多面板用列表)。例:`{"type":"单图文","images":["/p/a.png"],"title":"主标题","subtitle":"副标题","body":"正文"}`
- 命名字段优先填,`texts`/`bodies` 作为兼容兜底。

- `images/texts/bodies` 都按**顺序**填入该模块对应的槽位(见 modules.md 各模块字段顺序)。
- 不需要的字段省略即可(如 `文本` 模块不给 images)。
- **每个模块类型的完整 spec 示例见 `spec-examples.md`**(可直接照抄)。

### 返回(JSON)
```json
{
  "ok": true,                 // 草稿是否保存成功
  "name": "...",
  "store": "XY",
  "url": "https://sellercentral.amazon.com/.../content/<id>/revision/<ts>/edit",
  "named": true,
  "validation_failed": false, // true 表示有必填项没填全/校验失败
  "warnings": ["模块1[完整图片]: alt 长 130 超 100,上传时会截断 → …"],  // 非阻塞提示(可能没有)
  "modules": [                // 每个模块的执行结果
    {"type": "完整图片", "ok": true, "images": 1, "mobile_images": 1, "texts": 1, "bodies": 1}
  ]
}
```
- 判定成功:`ok==true && validation_failed==false`。
- `warnings`(若有):**非阻塞提示**,创建照常完成,字段超长上传时会按各字段真实上限截断。按**模块实测上限**检查(见 `modules.md` 字数上限表,如完整图片正文300、单图文正文500、文本正文5000、问答问题120/回答250、对比表3标题25…),以及 **alt≤100**。看到就把对应文案改短重建。
- 把 `url` 给运营,让其在后台预览并**人工提交审核**。

### 预检(提交即查,不启动浏览器)
spec 不合格会直接返回 `{"ok":false, "validation_errors":[...]}`(不建草稿):缺 name、模块>7、未知类型、图片不存在/尺寸不足、图片张数不够、ASIN 格式错、视频非 mp4、轮播面板越界等。

### 错误
- `401` X-API-Key 无效
- `409` 服务端正忙(浏览器串行),可调 `/aplus/status` 看正在执行的任务;任务失败/超时后服务端会自动释放并重置紫鸟
- 返回里 `ok=false` + `error`:执行异常(看 error 文本)

## 调用示例(curl)
```bash
curl -s -X POST "$APLUS_BASE_URL/aplus/create" \
  -H "X-API-Key: $APLUS_API_KEY" -H "Content-Type: application/json" \
  -d '{"store":"XY","name":"Dino Labels A+","modules":[
        {"type":"完整图片","images":["/data/aplus/dino1.png"],"texts":["Waterproof Dinosaur Name Labels"],"bodies":["Durable, dishwasher safe."]}
      ]}'
```
