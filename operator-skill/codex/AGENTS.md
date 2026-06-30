# 紫鸟高级 A+ 制作(Codex 版指令)

> 把"一个素材文件夹"变成亚马逊后台的**高级 A+ 草稿**。识别/选型/文案由你(Codex)做,
> **创建执行由中心服务完成**——你只按下面契约调它的 HTTP 接口。建完只是草稿,运营预览后手动提交。

## 何时用
用户要给亚马逊商品做**高级 A+(Premium A+)**(给了一组图/文案)时用本指令。
不要用于:标准 A+(走 SP-API)、改价/库存、直接改 listing。

## 配置(每台机器填一次)
读环境变量(或本文件同目录 `.env`):
- `APLUS_BASE_URL` = 中心服务地址(那台装了紫鸟的公共电脑),如 `http://10.0.0.5:8848`
- `APLUS_API_KEY`  = 服务方给的密钥

## 工作流
1. **看素材 + 排版规划**(详见 `reference/layout-planning.md`):逐张真的看图。
   - **先分类**:「成品横幅」(文字已印在图里)→ 每张用「完整图片」,只配 `alt`、不另写标题/正文;多张用「轮播」打包。「原始照片」(无文字)→ 单图文/双图/四图/背景,由你写文案。
   - **图多守上限**:一篇**最多 7 个模块**;图多时用轮播(1 模块装 2~6 张)打包。图太大不用管,程序自动缩放。
   - **图不达标就重绘**:某图尺寸不够/比例不符/质量差/缺图时,**用你的绘图能力**按该模块目标尺寸(见 modules.md,如完整图片 1464×600、移动 600×450)重画一张,贴合商品/品牌;**先和用户确认再画**,AI 生成的在 spec 里标 `"ai_generated": true`。
2. **先和用户确认排版**:把"模块清单 + ASCII 草图"发给用户,确认/调整后再建;缺 ASIN/视频就回去问,别编造。
3. **构造 spec 调接口**(见下)。
4. **看返回**:`ok=true` 且 `validation_failed=false` 即建成,把 `url` 给用户预览。
5. 不满意改 spec 重建(草稿可反复改);满意后**用户手动提交审核**(并确认 AI 披露)。

## 调用方式(HTTP)
**先传图(服务在别的机器时必做)**——中心服务只能读它自己机器上的路径:
```bash
curl -s -X POST "$APLUS_BASE_URL/aplus/upload" -H "X-API-Key: $APLUS_API_KEY" \
  -F "files=@/本地/桌面图.png" -F "files=@/本地/移动图.png"
# 返回 {"paths":{"桌面图.png":"/服务端/uploads/xxx/桌面图.png", ...}};把这些服务端路径填进 spec
```
再创建:
```bash
curl -s -X POST "$APLUS_BASE_URL/aplus/create" \
  -H "Content-Type: application/json" -H "X-API-Key: $APLUS_API_KEY" \
  --data-binary @spec.json
```
`GET $APLUS_BASE_URL/health` 探活;同机部署可跳过上传、直接用本地路径。

## spec 格式(完整示例见 `reference/spec-examples.md`)
```json
{
  "store": "店铺名(可选)",
  "name": "内容描述名称(必填)",
  "modules": [
    {"type":"完整图片","ai_generated":true,
     "images":[{"desktop":"/abs/d.png","mobile":"/abs/m.png","alt":"图片描述"}]},
    {"type":"轮播","variant":"简单","ai_generated":true,
     "panels":[{"image":"/abs/p1.png","alt":"描述"},{"image":"/abs/p2.png","alt":"描述","texts":["可选标题"]}]},
    {"type":"问答","texts":["问题1","回答1","问题2","回答2"]}
  ]
}
```
- 模块类型(19 类):完整图片/单图文/双图/四图/文本/背景图片/问答/技术规格/轮播(variant 简单·规则·导航·视频图像)/视频/含文本视频/对比表1·2·3/热点1·2。
- 图片可简写为字符串路径,或 `{desktop, mobile, alt}`;旧字段 `image` 仍兼容;**alt 务必给**;标题等非必填项不给即留空。
- 路径必须是**中心服务那台机器**可访问的绝对路径(同机/共享盘)。
- 字段细节见 `reference/api.md` 和 `reference/modules.md`;"A+ 是什么"见 `reference/about-aplus.md`。

## 护栏
程序只建草稿、绝不自动提交;一次一个商品(并发返回 409;可先查 `/aplus/status` 看当前任务与运行时长);只用用户给的素材,缺就问。
