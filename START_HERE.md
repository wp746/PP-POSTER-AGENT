# 从这里开始 · PP-POSTER-AGENT v0.1.0

将下面这段直接复制给 WorkBuddy、豆包工作、千万办公、Hermes 或其他宿主智能体，在已克隆本仓库的目录中使用：

```text
请接手当前目录的 PP-POSTER-AGENT。先读 AGENTS.md、README.md、docs/IMPLEMENTATION-STATUS.md 和 prompts/POSTER-AGENT.md。
先确认你能读写文件、执行 Python 3.10+、查看真实图片。用隔离环境安装，不读取其它项目或宿主全局配置中的 Key。
运行 poster doctor。已有 clone-local 配置直接使用；缺失时让我通过隐藏输入或 secret UI 配置聚合平台，不在聊天或命令参数里粘贴 Key。
同平台实际具备图像与视觉模型时，一把 Key 可以绑定两个角色；只有其中一种则需补齐另一通道。实际模型名称按我账号可用项配置。
分别报告本地工程与模型连接状态，不出无业务意义的测试图。
然后问我制作美食 KV、活动 KV 还是新增风格。从我提供的材料整理 brief，不要求我手写 JSON。
锁住食物原结构、装盘和器皿；核对活动事实，先确定主题再设计；在我的授权范围内运行计划、生产和质检。
结果未知的请求不得直接重发。只有查看真实成品并完成检查才可报告成功。
如果不能执行或看图，说明缺少的能力，不伪装成完整生产。
```

先用 [README](README.md) 安装，宿主接入条件见 [PORTABILITY](docs/PORTABILITY.md)，当前边界见 [实施状态](docs/IMPLEMENTATION-STATUS.md)。详细设计按需读取：

1. [美食生产规则](docs/FOOD-PLAYBOOK.md)：主体与器皿保护、品类适配、Stage A/B、质检。
2. [活动生产手册](docs/EVENT-PLAYBOOK.md)：常见活动分类、资料提取、主题与地域研究。
3. [风格库设计](docs/STYLE-LIBRARY.md)：逐步学习、参数化、版本、兼容性、验证。
4. [AI 提示词合同](docs/PROMPT-CONTRACTS.md)：分析、创意、图像任务与质检的输入输出。

当前已实现可执行 CLI 与工程测试，真实供应商、业务图像、各宿主和持续量产仍需按 [逐步验收](docs/VALIDATION.md) 验证。不要把早期完整设计当成已实现功能清单。
