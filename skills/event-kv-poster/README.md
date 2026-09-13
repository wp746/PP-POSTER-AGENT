# Event KV Poster Skill · P01–P18

可复制目录：`skills/event-kv-poster/`。

宿主只需要提供两类能力：

1. 多模态资料理解：读取用户文字、图片、Logo/IP、PDF/PPT/Word/网页正文，产出 `references/io-schema.md` 中的 factual brief。
2. 图像生成 adapter：`generate(prompt, reference_images, aspect_ratio)`，一次调用只返回一张完整海报。

Agent 入口应读取 `SKILL.md`，需要选风格时读取 `references/style-library.md`。P01–P18 的锁定名称、核心定义和元提示词同时记录在 `registry.json` 与 style library 中。

默认合同：3 张独立图、9:16、最终 2160×3840；A 场景/地域融合、B 活动核心、C 概念创意；用户指定 Pxx、比例、文字、素材、张数时覆盖默认值。AUTO 才进行风格路由。

供应商不是 Skill 的组成部分。云雾、OpenAI-compatible 或其他图像接口都应通过 `references/provider-contract.md` 的 adapter 接入；Key 永不进入 Skill、Prompt 或 Git。
