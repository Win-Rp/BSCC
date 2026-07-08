# BSCC 原生微信小程序工程

该目录为标书查重系统的小程序前端工程起点，使用微信小程序原生语法实现，不依赖 npm、uniapp、taro。

## 目录说明

```text
miniprogram/
├─ app.js
├─ app.json
├─ app.wxss
├─ project.config.json
├─ sitemap.json
├─ config/
│  └─ env.js
├─ utils/
│  ├─ format.js
│  ├─ request.js
│  └─ storage.js
├─ services/
│  ├─ api.js
│  └─ task.js
├─ components/
│  ├─ result-card/
│  └─ unlock-bar/
└─ pages/
   ├─ upload/
   ├─ progress/
   ├─ results/
   ├─ compare/
   ├─ recovery/
   └─ order/
```

## 已接入业务流程

- 上传 A 文件、多个 B 文件、关键字并创建任务
- 轮询任务进度，完成后跳转结果页
- 结果摘要、排行榜、免费预览片段展示
- 通过下载接口打开 A / B 原文，复用后端文件下载能力
- 多 B 结果进入对比页，未支付时自动提示去订单页
- 创建订单、展示订单号、支持复制订单号、手动刷新与自动轮询支付状态
- 按任务号/订单号/联系方式恢复任务
- 本地缓存 `taskNo`、`orderNo`、最近恢复信息

## 如何在微信开发者工具中打开

1. 打开微信开发者工具。
2. 选择“导入项目”。
3. 项目目录选择当前 `miniprogram` 目录。
4. `AppID` 可先使用测试号或你自己的小程序 AppID；仓库内默认配置为 `touristappid`，仅便于本地打开结构。
5. 导入后即可直接预览、调试页面逻辑。

## 环境配置

### 1. 接口基地址

默认接口地址定义在 `config/env.js`：

```js
baseURL: "http://127.0.0.1:8000"
```

开发建议：

- 微信开发者工具本地调试可先关闭域名校验，或改为你的局域网 IP。
- 真机调试不能使用 `127.0.0.1` 指向电脑后端，需要替换为可访问的局域网地址或已备案 HTTPS 域名。
- 所有接口请求统一从 `config/env.js` 读取，不需要逐页修改。

### 2. 合法域名与本地调试

小程序网络能力要求：

- `wx.request`
- `wx.uploadFile`
- 网络图片加载（订单二维码）

因此需要在微信公众平台配置：

- `request` 合法域名
- `uploadFile` 合法域名
- `downloadFile` / 图片资源相关域名（如二维码图片地址不是同域）

文档预览说明：

- 当前已支持通过 `GET /api/tasks/{task_no}/file/a` 与 `GET /api/tasks/{task_no}/file/b/{result_id}` 下载后打开 A / B 原文
- 小程序文档预览依赖微信客户端对文件类型的支持，常见 `pdf`、`doc`、`docx`、`xls`、`xlsx`、`ppt`、`pptx` 可优先联调验证
- 若真机打不开文档，需优先检查合法域名、HTTPS 证书、文件类型，以及下载接口返回的文件响应是否正常

本地联调阶段可在开发者工具中勾选“不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书”。

## 支付能力边界说明

当前后端接口复用的是现有 Web 版协议：

- `POST /api/orders`
- `GET /api/orders/{order_no}/status`

它返回的是 Native 下单结果与轮询状态，不是小程序 `wx.requestPayment` 所需的 JSAPI 参数。因此本工程采取的实现方式是：

1. 小程序创建订单；
2. 展示订单号与后端返回的信息；
3. 提示用户按系统提示完成支付；
4. 页面轮询订单状态；
5. 状态变为已支付后自动回到结果页并展示解锁结果。

这意味着当前阶段：

- 不调用 `wx.requestPayment`
- 不伪造 JSAPI 支付参数
- 后续若后端补齐 JSAPI 协议，再在订单页升级为小程序原生支付

## 开发约定

- 普通接口统一走 `utils/request.js` 中的 `wx.request`
- 上传任务统一走 `wx.uploadFile`
- 统一返回结构为 `{ success, data, error, statusCode }`
- 已兼容常见错误：`400`、`402`、`404`、网络错误
- 页面样式偏向可信、克制、清爽、移动办公

## 后续建议

- 如需更强的文档高亮交互，可在对比页增加滚动定位、锚点联动和片段展开能力
- 若后端补充支付二维码说明字段或 JSAPI 参数，可直接扩展订单页服务层
