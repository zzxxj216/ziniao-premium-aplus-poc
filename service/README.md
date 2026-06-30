# 中心服务(阶段一)— 骨架

高级 A+ 自动化的中心程序。**只此一台机器需要紫鸟**;运营侧将来通过 API 调用它(阶段二)。

## 已确认的接管机制(源自紫鸟官方 demo 源码)

```
1. 起客户端(webdriver 模式,mac):
   open -a <client> --args --run_type=web_driver --ipc_type=http --port=<port>
2. 本地控制 API:POST http://127.0.0.1:<port>,每个请求带 company/username/password
   getBrowserList → 店铺列表(browserOauth / siteId,1=美国站)
   startBrowser   → 开窗口,返回 debuggingPort / launcherPage / downloadPath
   stopBrowser / exit
3. Selenium 接管:ChromeOptions.debuggerAddress = 127.0.0.1:<debuggingPort>
4. 任务函数:func(driver, store_name, download_path)  ← 高级 A+ 逻辑写这里
```

## 本机要求(那台 Mac)

- 紫鸟 v6 客户端已安装、已登录企业账号、已添加亚马逊各站点店铺
- Python 3 + `pip install -r requirements.txt`
- 运行期间紫鸟被程序独占(webdriver 模式会接管主进程)

## 跑 M1 冒烟测试

```bash
cp config.example.yaml config.yaml          # 按本机填 client_path / 端口
export ZINIAO_COMPANY=...  ZINIAO_USERNAME=...  ZINIAO_PASSWORD=...
pip install -r requirements.txt
python smoke_test.py
```

成功 = `scratch/seller_central.png` 是已登录的 Seller Central 首页,且打印出真实 URL/标题。
这验证了"起客户端 → 开店铺 → CDP 接管 → 登进后台"整条链路打通。

## 路线

- [x] M0 接管机制核对(已完成)
- [x] **M1 冒烟测试**(已在 Mac 跑通:登录+2FA+会话持久化全验证)
- [x] M2 A+ Content Manager 导航 + 类型/模块枚举 + 19 模块规格(见 reference/premium-modules.md)
- [x] **M3 高级 A+ 制作跑通**(单模块[高级完整图片]+图,已保存草稿 ✅,见 build_draft.py)
- [ ] M3b 扩展:整文件夹多图→多模块;CONSTRUCTION 10图>7模块的取舍
- [ ] M4 其余判断 + 受控提交 + 多站点 + 封 HTTP API + 清理测试草稿

## M3 跑通的关键技术(踩坑记录,务必保留)

A+ 编辑器是 **Katal Web Components(kat-*)+ 大量 shadow DOM**,普通 selenium 选择器基本失效。解法:

1. **图片上传**:无可 send_keys 的 `<input type=file>`(「添加图片」触发原生选择器)。
   用**拖拽 hack**:JS 注入自有 `<input type=file>` → selenium send_keys 取得真实 File →
   合成 `DragEvent(drop)` + `DataTransfer` 丢到拖拽区。**已验证可上传**。
2. **shadow DOM 穿透**:所有"对话框内/编辑器内"元素(拖拽区、alt 框、按钮、名称框)
   都要用递归 walker(遍历 `shadowRoot` + 同源 `iframe.contentDocument`)定位,见 build_draft.py 的 DEEP。
3. **按钮是 `<kat-button>`**:文字在 `label` 属性里,不在 textContent → 按 `label` 属性匹配点击。
4. **名称是 `<kat-input>`**:JS 写 `value` 校验不认 → 必须取内部 `<input>` 做**真实 send_keys**+blur。
5. **加模块有时序抖动**:点「添加模块」后需重试 + 等模块磁贴出现再点。
6. 已保存草稿 URL:`/enhanced-content/content-manager/workflow/ebc-premium/content/<uuid>/revision/<ts>/edit`
7. 高级完整图片需 **桌面图(≥1464×600)+ 移动图(≥600×450),各带必填 alt**。
8. 现存测试草稿:`ZZTEST_dinosaur_0626_124313`(content id `879a676a-43a5-4e4f-b7b3-a1ad432a3a95`),用完可删。

## 已确认的真实环境事实(2026-06-26 实跑)

- 测试机:本机 Mac,紫鸟 `/Applications/ziniao.app` v6.26.3(内核 Chromium 142)
- 启动:**必须直接执行二进制**(`.../Contents/MacOS/ziniao --run_type=web_driver ...`);
  `open -a` 在 app 已运行时会去重丢参数 → 端口不监听
- 美国站店铺 siteId=1;测试店铺 Ziniao 名 `Inkelligent`(oauth `uLPCoyq73d3abGDo3NXb1w==`),
  对应亚马逊店铺名 `Okalinq`
- 登录:落 `/ap/signin`(密码紫鸟自动填)→ `/ap/mfa`(TOTP 两步验证,需人工或紫鸟自动二步验证)
  → 完成后 `sellercentral.amazon.com/home`。**会话跨开窗持久化**(关掉重开免登录/免2FA)
- 登录态判定:URL 在 `sellercentral.` 域且**不含 `/ap/`**
- A+ 内容管理器 URL:`https://sellercentral.amazon.com/enhanced-content/content-manager`
  (`/aplus/home` 是 404;amazonsell 深链会被重定向到 `/amazonsell/business`)
- **高级 A+(Premium A+)资格:已开通**(页面横幅确认)
- 现状表列:商品描述名称 / 内容类型(EBC=标准A+) / 语言 / ASIN / 上次修改 / 内容状态(已批准)
- 创建入口按钮文案:「开始创建 A+ 商品描述」
- 紫鸟原生「自动二步验证」可用于无人值守 OTP(待为各店铺配置 TOTP 种子)
- 创建入口「开始创建 A+ 商品描述」→ 跳 `/enhanced-content/content-manager/workflow`
- 创建第一屏「A+ 商品描述选择」顶层类型枚举(3 选 1):
  - 基础 A+(最多 5 模块)按钮 `创建 基础 A+`
  - **高级 A+(7 模块,含视频/大图/互动)按钮 `创建 高级 A+`** ← 目标
  - 品牌故事 按钮 `创建 品牌故事 A+`
- 分工定论:**识别/选型由 Claude Code 做;开放程序只做"创建执行"**(输入已定好的类型+素材)
- 高级 A+ 编辑器深链可直达:`/enhanced-content/content-manager/workflow/ebc-premium/content/new/edit`
  (`ebc-premium` = 高级A+;深链不被弹登录)
- 编辑器要素:商品描述名称(必填)/ 语言(默认 美国 英语)/「添加模块」按钮(在主文档,非iframe);
  顶部按钮:取消 / 保存为草稿 / 下一步:应用 ASIN;步骤条:创建内容→应用ASIN→提交→批准→已发布
- 高级 A+ 模块全清单(~19 种,单篇最多 7 个,均带「AI 效果润色」):
  优质视频图像轮播 / 包含文本的高级双图片 / 包含文本的高级背景图片 / 包含文本的高级视频 /
  带文本的单张高级图片 / 高级、简单的图像轮播 / 高级全视频 / 高级四图片和文本 /
  **高级完整图片** / 高级导航轮播 / 高级技术规格 / 高级文本 / 高级比较表1/2/3 /
  高级热点1/2 / 高级规则轮播 / 高级问答
- 纯图横幅素材最佳匹配模块 = **高级完整图片**(单张整图)
- 测试集:/Users/zane/Desktop/dinosaur (A+/ 6图 1594x986)、/Users/zane/Desktop/CONSTRUCTION (A+/ 10图 1672x941)

## 安全 / 合规备忘

- 凭据走环境变量,勿写入 config.yaml 或日志
- 仓库底座(紫鸟 demo)无 LICENSE,商用前建议向紫鸟确认授权
- 提交审核默认人工把关,程序默认只产出草稿
