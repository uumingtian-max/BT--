# 工具：Playwright 浏览器

Triggers: browser_navigate,browser_screenshot,browser_click_and_extract,browser_fill_form,browser_fill,playwright,chromium,无头浏览器,浏览器自动化,打开网页,打开网站,访问网址,网页截图,截图网页,页面截图,点按钮,点击元素,填表单,提交表单,登录网页,抓页面,爬网页,网页测试,e2e,端到端,自动化测试网页,Browser,@Browser,browser automation,web automation,tool_browser_playwright

---

**何时使用**：用户要**用浏览器操作网页**（打开 URL、截图、点击、填表、提交、抓正文）或提到 Playwright/Chromium/无头浏览器/`@Browser` 时，**必须**挂载本技能；纯 API 调试用 `tool_http_request`，桌面窗口操作用 `tool_windows_gui`。

## 执行步骤

1. 先 `browser_navigate`（`url`、`wait_ms`）；需要留证时同轮 `browser_screenshot`（`output_path` 默认 `outputs/browser_shot.png`）。
2. 点击/取文：`browser_click_and_extract`（`url`、`selector`、`extract_selector`）。
3. 填表：`browser_fill_form`（`url`、`fields` 对象、可选 `submit_selector`）；选择器须可验证；**勿**在回复里写用户密码。
4. 失败贴 Playwright 报错；若缺浏览器执行 `playwright install chromium`（见 `PLAYWRIGHT_BROWSERS_PATH`）。

## 避免

- 未调用工具就声称「已打开/已点击/已提交」。
- 未经确认自动登录、支付、删数据、过验证码绕过。
- 将内网管理页、凭证页内容全文塞进聊天或记忆。
- 反爬/指纹绕过用于未授权场景（见 `trust_and_decline`）。

## ONYX 对接

- 工具：`browser_navigate` · `browser_screenshot` · `browser_click_and_extract` · `browser_fill_form`
- 分组：`GET /agent/tools` → `browser_automation`
- 依赖：`pip install -r requirements-extras.txt` + `playwright install chromium`

## 关联技能

- `multimodal_desktop_agent`
- `tool_http_request`
- `trust_and_decline`
- `tool_reliability`

## 自测用语（习惯体检 / 人工抽检）

- 打开 https://example.com 截个图给我
- 在这个登录页填账号密码并提交（我先确认）
