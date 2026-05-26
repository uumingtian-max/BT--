# BT 高定数字代理人参考板

> 目标：把 BT 数字人从“科技 3D Demo”推进到“高定时装屋级真人代理人”。这些参考只借鉴方向和质量标准，不复制品牌视觉、不使用第三方素材、不冒用商标。

## 最接近 BT 的方向

BT 不应该像游戏 NPC，也不应该像普通 SaaS 聊天页。更接近的产品形态是：

- 高定品牌官网的克制编辑体验；
- 企业级真实数字人；
- 时装电商里的高保真人/数字双生；
- 本地 Agent 工作台的可审计执行系统。

一句话：**真人脸是门面，Agent 执行是内核，界面像一间安静的高级工作室。**

## 参考 1：Hermès 数字编辑体验

可借鉴：

- 官网不只是商品橱窗，而是带叙事和艺术层的数字空间；
- 插画/动画/产品之间有克制互动，不靠技术炫耀；
- 线上体验要像线下精品店和季节发布一样被精心策划。

落到 BT：

- 数字人舞台应少放技术标签，多做“空间感、留白、艺术层”。
- 动效只做低频呼吸、光线移动、轻微视差。
- 不要大面积橙色；橙只作为极少量签名色，主色用金棕、皮革棕、丝绸米白。

参考源：

- https://www.domusweb.it/en/news/2026/01/07/herms-new-website.amp.html

## 参考 2：Bottega Veneta 官方站与品牌气质

可借鉴：

- 克制、无噪声、重材质和工艺；
- 不依赖大 Logo 或喧闹装饰；
- 通过细节、版式、服务入口、预约/证书/护理等系统营造高级感。

落到 BT：

- 侧边信息要像展厅铭牌，不像仪表盘。
- 线条细、块面少、边框轻，按钮少而准。
- 视觉记忆点应该来自脸、材质、光，而不是 HUD、霓虹、粒子。

参考源：

- https://www.bottegaveneta.com/en-us/macro-gifts.html

## 参考 3：MetaHuman 官方质量标准

可借鉴：

- 高保真人要从真实扫描数据库、头发、眼睛、牙齿、皮肤等细节开始；
- 自定义 mesh/scan 可以转为完整 rig，再进入实时交互链路；
- 数字人不是一张脸贴图，而是面部结构、材质、绑定、动画的整体系统。

落到 BT：

- 当前 `photo.png + depth.png` 是轻量原型，下一档应接 MetaHuman 或同级数字双生流程。
- 前端 Three.js 只负责轻量实时呈现；真正高保脸应有离线建模/视频/流式渲染计划。
- 眼睛、头发、皮肤不能用统一滤镜糊过去，要分层设计。

参考源：

- https://www.metahuman.com/create

## 参考 4：Digito 数字人工作室

可借鉴：

- “不应像聊天机器人或 3D 模型，而应像一种 presence”；
- MetaHuman 级面部 rig、物理皮肤、strand hair、Unreal + Pixel Streaming 是高质量路线；
- 同一个数字人可落到 web、mobile、XR、live event。

落到 BT：

- 现阶段 Web 里做高定质感；中期可以把 SadTalker/视频作为过渡；长期可评估 Pixel Streaming/UE。
- 不是单纯“会动”，而是要有在场感：看得见呼吸、停顿、目光和状态。

参考源：

- https://digito.ai/

## 参考 5：UneeQ 企业数字人

可借鉴：

- 数字人是“品牌声音和价值观的人类化 embodiment”；
- 真实互动由外观、声音、人格、护栏、安全和 LLM 编排共同组成；
- 避免 uncanny valley，强调可被信任和可持续交互。

落到 BT：

- 小涵/黑光代理人的脸、声音、回答风格、任务边界要一致。
- 前端必须显示“她为什么在思考 / 正在做什么 / 是否安全”，而不是只显示漂亮脸。
- 记忆和技能成长要有人类确认，避免“自进化”变成不可控。

参考源：

- https://www.digitalhumans.com/features/digital-human-creation

## 参考 6：Hautech 数字双生与时装摄影

可借鉴：

- 从单张照片生成接近真人的数字双生；
- 高端时装场景强调一致的姿态、环境、光线和品牌主模型；
- 数字人不只用于聊天，还能用于目录、造型、虚拟试衣、品牌叙事。

落到 BT：

- `face.png` 不只是头像输入，应该成为“权哥专属代理人肖像资产”的起点。
- 后续可以有 `portrait_manifest.json`：照片、深度图、视频、声音、风格、授权说明。
- 每次生成/替换肖像都要有预览和回滚，不要覆盖原资产。

参考源：

- https://hautech.ai/solutions/digital-twins

## 参考 7：Replica AI / ATWIL 的实用指标

可借鉴：

- 真实感不是口号，要落到光线、阴影、织物/头发/皮肤材质、浏览器性能、隐私和授权；
- 数字肖像/数字双生必须有 consent 和控制权；
- 高端体验也必须低摩擦：浏览器可运行，不强迫安装。

落到 BT：

- 继续坚持本地优先和浏览器/Electron 可用；
- 个人脸图、深度图、视频产物默认不进 Git；
- 如果未来使用真人肖像训练或风格迁移，必须写清授权和撤回机制。

参考源：

- https://myreplica.io/
- https://atwil.in/

## BT 视觉验收标准

下一轮 Cursor 或 Codex 改数字人时，用这 10 条验收：

- 第一眼像真实高级肖像，不像游戏角色。
- 脸在第一视觉中心，UI 不抢脸。
- 肤色自然，有顶光、侧光、阴影三层。
- 眼睛有微弱湿润高光，但不夸张。
- 头发有厚度和边缘光，不是一整块黑色贴图。
- 色彩是金棕/皮革/丝绸米白，橙色只点到为止。
- 文字像展厅铭牌，少、细、准。
- 动效是呼吸和低频光，不是霓虹扫描。
- 数字人状态能对应 Agent 状态：静候、思考、执行、完成、需要确认。
- 构建必须通过，个人肖像/生成媒体不能进 Git。

## 可执行下一步

1. 给 `frontend/public/digital-human/` 增加 `portrait_manifest.example.json`，描述肖像资产、光线、授权、生成命令。
2. 在 `DigitalHumanStage` 加 5 个状态视觉：idle / thinking / executing / speaking / confirm_needed。
3. 给 Three.js shader 分层：skin warmth、hair rim、eye catchlight、soft shadow。
4. 给 `/meta/doctor` 增加 digital-human 检查：photo/depth/video/manifest 是否存在。
5. 做一个“高定预览页”，只看数字人，不带聊天干扰。
