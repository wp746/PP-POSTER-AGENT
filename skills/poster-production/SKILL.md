---
name: poster-production
description: 制作美食或活动宣传 KV、学习海报提示词风格；依赖 PP-POSTER-AGENT 运行核心。
---

# 海报生产

定位用户克隆的 PP-POSTER-AGENT 根目录，先读 START_HERE.md、AGENTS.md、README.md 与 prompts/POSTER-AGENT.md。此技能是发现入口，不包含另一套绕过检查的生产逻辑。

用户指令优先；不为小改增加多轮确认，不自动授予发布/发送/额外费用权限。已授予的生成修复授权有效，等待/验收/启动门禁仍有效。

检查能否读图、写文件、执行 Python。使用同一 poster CLI，事实/主体/品牌优先于风格；不读取其它项目的 Key 或资产。不能运行的宿主只做方案准备并如实说明。

实际功能以 README 和实施状态为准。单独复制此 SKILL.md 不会获得模型连接、运行环境或出图能力。
