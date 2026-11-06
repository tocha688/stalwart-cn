# 简体中文界面

本目录包含把 Stalwart 界面改成简体中文时用到的资源与脚本。

## 范围

| 界面 | 是否在本仓库 | 处理方式 |
| --- | --- | --- |
| 登录页 `/login`、`/device` | 是 | 已直接汉化 |
| 日历回复页 `/calendar/rsvp` | 是 | 已直接汉化 |
| 日历提醒邮件、会议邀请邮件 | 是 | 走 `resources/locales/i18n.yml` 的 `zh-CN` 条目 |
| WebUI（`/admin`、`/account`） | 否，是独立发布的 React 产物 | 用本目录的 `patch.py` 在产物中注入 `zh.json` |

## 一、本仓库内的界面

`resources/html-templates/` 下的 `login.html`、`calendar-rsvp.html`、`ui.js` 已改成简体中文，
`<html lang>` 为 `zh-CN`。这些文件不是直接使用的：`crates/http` 通过 `include_bytes!`
嵌入的是压缩后的 `*.min.gz`，所以改完源文件必须重新生成产物。

```bash
# 需要 html-minifier-terser、terser、gzip 与 sha256sum
npm install --no-save html-minifier-terser terser
bash resources/webui-zh/rebuild-html-assets.sh <仓库根目录> <node_modules/.bin 目录>
```

脚本会重新生成 `*.html.min`、`*.html.min.gz`、`ui.js.min.gz` 和 `ui.hash`。

产物之间有三条硬约束，脚本已经处理，手工修改时需要注意：

1. `ui.hash` **不能有结尾换行**。`crates/http/src/request.rs` 里有
   `assert!(UI_ASSET_PREFIX.len() == "ui-".len() + 12)`，多一个换行编译就会失败。
2. `ui.hash` 必须等于 `sha256(ui.css.min ‖ ui.js.min)` 的前 12 个十六进制字符。
   两个页面里的 `ui-<hash>.css` / `ui-<hash>.js` 引用必须与它一致，否则资源 404。
3. `.min.gz` 是 `.min` 的 gzip 压缩（`-9 -n`），服务端以 `Content-Encoding: gzip` 原样返回。

### 服务端文案的语言

日历提醒邮件、iTIP 邀请邮件和 RSVP 页的文案来自 `crates/common/src/i18n.rs`，
语言取自账号的 `locale` 设置，而该设置的默认值是 `en-US`。
`i18n.rs` 里的 `preferred()` 把 `en-US` 重定向到 `zh-CN`，所以新账号无需额外配置就是中文。
要恢复英文，让 `preferred()` 返回 `&EN_US_LOCALES` 即可（`en-US` 译文仍编译在产物里）。

`Accept-Language` 为 `zh`、`zh-CN` 或缺失时也会落到 `zh-CN`；`zh-TW`、`zh-HK`、`zh-Hant-*`
仍是繁体，其他语言（如 `de-DE`、`ja-JP`）保持原有译文。

## 二、WebUI

WebUI 是独立仓库发布的已编译产物，不在本仓库内，默认从
`https://github.com/stalwartlabs/webui/releases/download/v2/webui.zip` 下载。
它内部已经用了 i18next，但只注册了 `en` 一份资源，所以界面上出现的是英文。

`patch.py` 在产物中直接注入中文资源，不需要 Node 工具链，也不需要重新编译：

```bash
# 1. 下载并解压官方产物
curl -L -o webui.zip https://github.com/stalwartlabs/webui/releases/download/v2/webui.zip
mkdir webui && cd webui && unzip -q ../webui.zip && cd ..

# 2. 注入中文
python -I patch.py webui

# 3. 重新打包
cd webui && zip -qr ../webui-zh.zip . && cd ..
```

然后在管理后台把 `Application` 对象的 `resourceUrl` 指向你自己的 `webui-zh.zip`
（本地文件用 `file://` 前缀），或把 zip 放到任意 HTTPS 地址。

### 为什么是 `zh` 而不是 `zh-CN`

WebUI 用 `navigator.language.split("-")[0]` 推导语言，`zh-CN` 会被截成 `zh`，
所以资源必须注册在 `zh` 这个键下。`patch.py` 同时改写了这段初始化，让中文浏览器直接命中 `zh`。

### 局限

`zh.json` 覆盖了 WebUI 资源表里的全部 428 条文案，但**只有走 i18next 的文本会翻译**。
除资源表所在的 chunk 之外，其余 chunk 里另有约 550 条直接写在组件中的英文字符串，
它们不经过 `t()`，在不重新编译源码的前提下无法替换。这是 `patch.py` 方案的固有限制。

要完整汉化 WebUI，需要那份 React 源码：在源码里补一份 `zh` 资源文件并让组件改用 `t()`，
然后重新构建。届时可以直接复用本目录的 `zh.json` 作为翻译底稿。

### 升级注意

`patch.py` 依赖产物中的两处结构（英文资源表 `fe={accounts:`Accounts`...}` 与
`i18next` 的 `init({resources:{en:...}})` 调用）。官方更新产物后如果这两处变了，
脚本会明确报错 `anchor not found`，此时需要按新结构更新锚点。
`zh.json` 是纯翻译数据，与产物结构无关，可以一直沿用。
