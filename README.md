# PP-POSTER-AGENT

**v0.1.0 · 可移植美食与活动海报 Agent · 本地工程测试 60 项通过 · 真实模型与跨宿主试产待验证**

以 GPT Image 2 类聚合图像通道为主视觉引擎，配合视觉模型、精确文字合成和可恢复生产记录。支持美食 KV、活动 KV、自主创意和渐增风格文本学习。

**给其他智能体的第一条指令在 [START_HERE.md](START_HERE.md)。** 用户提供素材和需求，宿主整理输入，CLI 执行同一条可追溯生产链。

## 当前可用

- 同平台一把 Key 绑定 image/vision，或云雾图像 + 硅基流动视觉等双平台；不继承维护者凭据。
- OpenAI-compatible 多图视觉、生成、multipart 参考编辑；读取 base64 或独立无鉴权下载的结果 URL。
- TXT/Markdown、PDF、DOCX、PPTX 文本提取与页/幻灯片定位；页内图片需要宿主实际查看。
- 原图保护合成；明确允许时运行参考编辑 A→A QC→B，Logo/IP/人物原图独立合成。
- 多比例布局，实际字体缺字、溢出、重叠检查先于生图；精确文案、PNG 与布局图层 JSON。
- SQLite 检查点、输入/产物哈希、累计请求预算、步骤尝试上限、暂停/取消、未知结果恢复。
- 定向修复、精确文字修订复用图像、风格草稿与绑定、最终人工复核和 ZIP 导出。

## 如实边界

这是首个可执行工程版本，尚不是已证明的稳定量产服务。测试使用有明确 test 标签的模型替身，验证接口与状态行为，不证明真实 Image2 画质或食物保真。

默认 protected 无蒙版时保留**完整矩形原照片**做摄影区，不假装自动抠图。提供与规范化原图匹配的灰度蒙版可合成主体。reference_edit 可优化整体摄影表现，但结构是否保持必须经真实 QC 与看图验证。

V1 使用一个明确字体文件、直排文本块和精确资产合成。自动抠图、多字体角色/曲面文字、内置城市搜索、自动 PPT 页图渲染、二维码/专有码验证、印前、原生 App、海量队列均尚未实现。地域研究由宿主完成并写入来源卡。早期 [完整规格](Product-Spec.md) 不等于当前功能清单。

## 安装

Python 3.10+，仓库目录内运行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/poster doctor
```

Windows 将 `.venv/bin/python` 换成 `.venv\Scripts\python.exe`，poster 换成 `.venv\Scripts\poster.exe`。Windows 实机待验证。也可运行 `python -m poster_agent`。

未配置时 doctor 返回 2，并分别显示本地就绪、供应商缺失，这是正常的保护行为。

## 隐藏配置 Key

同平台同时具备图像与视觉模型：

```bash
.venv/bin/poster configure --provider yunwu --vision-model YOUR_ACTUAL_VISION_MODEL
```

云雾图像 + 硅基流动视觉：

```bash
.venv/bin/poster configure --provider yunwu --vision-provider siliconflow --vision-model YOUR_ACTUAL_VISION_MODEL
```

前者只输入一把 Key；两者均隐藏输入。自定义平台用 `--provider custom --base-url https://your-provider.example/v1`，图像别名用 `--image-model`。实际视觉模型必须显式指定，不套用旧项目型号。只有图像或只有视觉能力都不足以完成本核心全链。

非交互宿主用私有 secret UI 注入明确的 PP_IMAGE_KEY / PP_VISION_KEY，再 configure --from-env。Key 不进入聊天、命令参数或 Git。运行时只读本副本 .local，不读取其他 Agent 配置、OPENAI_API_KEY 或环境代理凭据。

`poster doctor --probe` 只查模型列表，不生图，不证明编辑和视觉已通过。[供应商合同](docs/PROVIDERS.md)

如果代理把域名映射到 198.18.0.0/15，configure 时明确加 `--allow-fake-dns`；只对已配置的供应商域名生效，保留 TLS 证书校验、DNS 地址固定和其它私网拦截。未列入配置的结果 CDN 不获得这个例外。默认关闭，不改动系统代理。

## 创建、计划、生产

宿主根据用户素材填写 [美食 brief](examples/food.brief.json) 或 [活动 brief](examples/event.brief.json)，普通用户不必手写 JSON。路径相对 brief，字体必须真实可用并允许使用。

```bash
.venv/bin/poster init --brief /path/to/my-brief.json
.venv/bin/poster plan projects/JOB_ID --execute --max-calls 20
.venv/bin/poster status projects/JOB_ID
.venv/bin/poster run projects/JOB_ID --execute --max-calls 20
```

max-calls 是项目**累计模型请求次数**，包含分析、布局、图像、QC，不是人民币价格。继续不重置已用次数，每个请求步骤最多 3 次，不无限自动重试。货币限制目前配合供应商端额度；缺可靠用量不猜费用。

plan 调用分析和布局，生成标为 LAYOUT_ONLY 的本地示意，不调用图像模型。run 复用已完成步骤。用户授权直接完成时可直接 run。通过软件 QC 后为 AWAITING_REVIEW：

```bash
.venv/bin/poster review projects/JOB_ID --accept --reviewer YOUR_NAME
.venv/bin/poster export projects/JOB_ID --output output/my-poster.zip
```

必须实际看各比例图片才能 review。含 PDF/Office 时另核对页图后加 --sources-reviewed。导出图片、底图、文字/图层 JSON、事实、素材哈希及验收记录；不转发字体文件。首版数字 PNG 不标作印刷就绪。

## 修改和恢复

```bash
# 复制 plan 产物后编辑，不修改被哈希保护的原文件
.venv/bin/poster adopt-plan projects/JOB_ID --canvas 0 --plan /path/to/revised-plan.json
.venv/bin/poster repair projects/JOB_ID --step base_0 --feedback /path/to/feedback.txt
.venv/bin/poster revise-copy projects/JOB_ID --copy /path/to/copy.json --facts /path/to/facts.json --keep-design
.venv/bin/poster run projects/JOB_ID --execute --max-calls 30
```

文字修订保留 ID、角色和设计，提供本次采用的完整事实表；旧输入归档。换主题、主体或新增角色请新建 job。溢出先修布局，不删字。修改后最终验收失效，按实际依赖决定复用。

若质检存在可定位的误判，用 repair 的 subject_qc/base_qc_N/final_qc_N 步骤提供复查线索，再 run；它重新调用视觉检查，不能手写 PASS 或放松硬规则，仍受三次尝试和总请求预算限制。

```bash
.venv/bin/poster pause projects/JOB_ID
.venv/bin/poster cancel projects/JOB_ID
.venv/bin/poster recover projects/JOB_ID --acknowledge
```

暂停/取消在当前不可中断请求返回后生效，仍可能产生费用。崩溃先确认旧进程结束。未知请求先查供应商，再 `recover --acknowledge --resolve ATTEMPT_ID --reason '已核对结果并接受重试费用风险'`；它只允许新请求，不伪造旧成功。专用异步查询/未知结果导入尚未实现。

## 增长风格库

```bash
.venv/bin/poster learn-style --source /path/to/prompt.txt --id editorial-v1 --execute
.venv/bin/poster attach-style projects/NEW_JOB_ID --style .local/styles/editorial-v1/style.json
.venv/bin/poster run projects/NEW_JOB_ID --execute --max-calls 20 --experimental-style
```

学习一次文字/视觉模型，不调用图像模型。同一 ID 不覆盖。V1 学习文本，参考图可由宿主实际看图转成观察规则；所有新风格为草稿/试验，不自动宣称已验证。[完整风格设计](docs/STYLE-LIBRARY.md)

## 维护

```bash
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_release.py
.venv/bin/python -m build
```

同步版本、能力、验证和测试数。GitHub Actions 在 Linux/Windows 执行工程测试，只有实际绿色结果才算相应 CI 证据。见 [CHANGELOG](CHANGELOG.md)、[实施状态](docs/IMPLEMENTATION-STATUS.md)、[逐步验收](docs/VALIDATION.md)。
