# 聚合接口与来源

核查日期：2026-09-05。未调用用户真实账号，未复制旧项目私有配置。

- GPT Image 2 官方支持生成/编辑，本核心使用 `/images/generations` 和 multipart `/images/edits`，不把它当文字对话模型；不传 `input_fidelity`。[OpenAI 图像指南](https://developers.openai.com/api/docs/guides/image-generation)
- SiliconFlow 官方使用 `https://api.siliconflow.cn/v1`、`/chat/completions`，图像可以 URL/base64 传入；实际模型 ID 由当前账号选择。[官方视觉说明](https://docs.siliconflow.cn/docs/userguide/capabilities/vision)
- Yunwu 官网说明 OpenAI-compatible API 与不同组别。`https://yunwu.ai/v1` 是可修改的预设；实际模型、组别、参数与同步返回需本次 job 验证，营销承诺不是 SLA。[官网](https://yunwu.ai/)

同平台实际提供图像和视觉模型时可一把 Key 绑定两角色。只有其中一类能力时补另一通道。

base_url 含实际 API 前缀，必须 HTTPS，不含 userinfo/query/fragment。请求不跟随重定向、不回显错误正文；结果 URL 单独 GET，不携带 API Key。拒绝本机/私网目标，不自动读取环境代理凭据。对明确的可信供应商进行配置，不能把任意第三方 URL 作为 API 根。

V1 不抓取正文网页，由宿主研究工具完成。受保护/跳转下载或自定义异步格式会显式失败；不把 Key 转发 CDN。记录模型、请求 ID（可用时）、真实尺寸、父参考/产物哈希、用量（可用时）与错误。模型列表成功不代表真实编辑通过。

支持显式 allow_fake_dns：仅对当前配置的供应商域名允许代理 198.18.0.0/15 映射，仍验证原域名 TLS，并固定已检查的 IP 防止二次 DNS 换址。不允许回环、其它私网或任意结果 URL 继承该例外。默认关闭。
