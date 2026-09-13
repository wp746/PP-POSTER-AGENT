# P01–P18 Style Library

Shared rules: user-specified constraints override defaults; hard facts are immutable; one generation call should produce one complete canvas; default is 3 independent outputs; do not force geographic landmarks when irrelevant.

## P01｜空间嵌字
**Full name:** 透视建筑 × 空间嵌字海报
**Core:** 超大标题物理嵌入建筑表面、曲线、开口与消失点；先建空间再放字。
**Template inputs:** `title, project, architecture, movement, subject, colors, support_copy`

<!-- P01-META-START -->
```text
先建立 {{architecture}} 的准确透视与消失点，再把超大主标题「{{title}}」像真实建筑图形一样嵌入空间表面；根据 {{movement}} 产生下降/后退/弯曲/上升等运动。{{subject}} 仅作尺度锚点。配色 {{colors}}。只保留 {{support_copy}}。文字必须服从透视、遮挡、材质与接触关系，禁止平贴字、假3D、弱空间。
```
<!-- P01-META-END -->

## P02｜透视构字
**Full name:** 透视字体 × 空间构字海报
**Core:** 字体本身成为主要空间结构，沿道路、走廊、楼梯或抽象空间伸展。
**Template inputs:** `title, project, scene, subject, perspective_type, colors, support_copy`

<!-- P02-META-START -->
```text
让「{{title}}」成为 {{scene}} 中最主要的空间结构，占画面35%–60%；按 {{perspective_type}} 拉伸、折叠、后退或跨越楼梯/通道。{{subject}} 是次级尺度锚点。配色 {{colors}}，信息 {{support_copy}}。保持可读、强深度、清洁层级；禁止漂浮字、普通装饰3D和随机扭曲。
```
<!-- P02-META-END -->

## P03｜密度编辑
**Full name:** 高密度编辑 × 展览视觉海报
**Core:** 1个绝对主锚点+2–3个次锚点，高密度但有秩序。
**Template inputs:** `theme, cn_title, en_title, hero, irregular_image_method, edge_pressure, auxiliary_system, background_layer, colors, date_org`

<!-- P03-META-START -->
```text
围绕 {{theme}} 建立1个绝对主视觉 {{hero}} 与2–3个次级锚点；主图采用 {{irregular_image_method}}，拒绝普通矩形图。超大中文「{{cn_title}}」通过 {{edge_pressure}} 与图像交叠；英文 {{en_title}}、{{date_org}} 形成强字号跳跃。只使用一种 {{auxiliary_system}}，背景弱化为 {{background_layer}}。色彩 {{colors}}。成熟出版物感，丰富但不乱，禁止PPT信息图。
```
<!-- P03-META-END -->

## P04｜中轴对峙
**Full name:** 中轴夹景 × 双主体对峙海报
**Core:** 稳定垂直中轴，左右主体夹压中央标题与信息。
**Template inputs:** `theme, cn_title, en_title, left_subject, right_subject, composition, background, title_color, material, date_venue`

<!-- P04-META-START -->
```text
建立严格垂直中轴；{{left_subject}} 与 {{right_subject}} 按 {{composition}} 从左右施加视觉重量，保持重量平衡但不机械镜像。中心放「{{cn_title}}」与 {{en_title}}，允许纵排、裁切、穿插。背景 {{background}}，标题 {{title_color}}，主体材质 {{material}}，信息 {{date_venue}}。Museum Exhibition × Contemporary Editorial。
```
<!-- P04-META-END -->

## P05｜扇形流场
**Full name:** 扇形构图 × 曲线流场海报
**Core:** 扇形/弧线/放射/运动弧线作为视觉骨架与节奏。
**Template inputs:** `theme, title, concept, fan_logic, visual_material, colors, typography, background, text_details`

<!-- P05-META-START -->
```text
以 {{fan_logic}} 建立一条清晰的大轮廓，围绕 {{concept}} 组织 {{visual_material}}、留白与标题「{{title}}」。曲线必须表达概念而非装饰；配色 {{colors}}，排版 {{typography}}，背景 {{background}}，文字 {{text_details}}。整体是被艺术指导过的编辑拼贴，流动但不失主视觉。
```
<!-- P05-META-END -->

## P06｜曲线编辑
**Full name:** 曲线骨架 × 当代社论海报
**Core:** 唯一主曲线组织主体、文字、信息与留白。
**Template inputs:** `theme, cn_title, en_title, hero, curve_method, auxiliaries, primary, secondary, accent`

<!-- P06-META-START -->
```text
先确定唯一最强主曲线，以 {{curve_method}} 串联 {{hero}}、中文「{{cn_title}}」、英文 {{en_title}}、{{auxiliaries}} 与留白。色彩 {{primary}} + {{secondary}} + {{accent}}。其余元素必须顺从主曲线，2–3种视觉语言以内，后现代编辑感，禁止多方向竞争。
```
<!-- P06-META-END -->

## P07｜穿梭巨字
**Full name:** 超大字体 × 主体穿梭空间海报
**Core:** 巨字成为可信建筑结构，主体在字形中穿行/攀爬。
**Template inputs:** `brand, event, main_word, subject, architecture, movement, primary, accent`

<!-- P07-META-START -->
```text
把「{{main_word}}」变成 {{architecture}} 中的巨大可穿行结构，让 {{subject}} 以 {{movement}} 与字形真实互动。必须有前中后景、字在人前/后穿插、接触阴影与可信材质。品牌 {{brand}}，活动 {{event}}，主色 {{primary}}，强调色 {{accent}}。禁止普通“人物+大字”和随机3D字母。
```
<!-- P07-META-END -->

## P08｜材质变字
**Full name:** 材质/光学变形 × 装置排版海报
**Core:** 文字被织物、地形、镜面、水等介质物理改造。
**Template inputs:** `title, project, environment, mechanism, subject, primary`

<!-- P08-META-START -->
```text
让主标题「{{title}}」占35%–55%，被 {{environment}} 通过 {{mechanism}} 真实改造：拉伸、弯曲、分裂、压缩、反射或折射。物理规律、透视、遮挡必须可信。{{subject}} 只作尺度参考。项目 {{project}}，主色 {{primary}}。像当代装置艺术，禁止随意液化和无物理原因的变形。
```
<!-- P08-META-END -->

## P09｜斜轴编辑
**Full name:** 斜向势能 × 文化编辑海报
**Core:** 隐藏对角轴统一主视觉、标题、纹样、日期和留白。
**Template inputs:** `theme, cn_title, en_title, hero, pattern, primary, secondary, date_org`

<!-- P09-META-START -->
```text
建立单一隐藏斜轴，让 {{hero}}、中文「{{cn_title}}」、{{en_title}}、{{pattern}}、{{date_org}} 沿同一方向递进。背景只做弱纸张/图纸/档案信息层。配色 {{primary}} + {{secondary}}。成熟印刷与艺术出版物气质，禁止显眼的装饰斜线代替构图。
```
<!-- P09-META-END -->

## P10｜巨构黑场
**Full name:** 3D巨构字体 × 暗黑专辑封面海报
**Core:** 暗场匿名人物+深挤出巨字+Swiss微信息。
**Template inputs:** `theme, main_title, subject, microcopy, accent`

<!-- P10-META-START -->
```text
以深黑环境和匿名 {{subject}} 建立神秘气氛；超粗浓缩主标题「{{main_title}}」深度挤出并朝镜头推进，部分裁出画布，与人物前后穿插。材质哑光混凝土/粗粝表面，电影边缘光、雾与长阴影；加入克制 {{microcopy}}，强调色 {{accent}}。像收藏级专辑封面，不做会议舞台或普通科技霓虹。
```
<!-- P10-META-END -->

## P11｜对角主轴
**Full name:** 对角构图 × 单轴张力海报
**Core:** 先立斜轴，再组织主体、标题和留白；商业信息清晰。
**Template inputs:** `theme, subject_type, subject, cn_title, en_title, diagonal_method, axis, colors, date_org`

<!-- P11-META-START -->
```text
先建立 {{axis}} 的唯一对角主轴，按 {{diagonal_method}} 组织 {{subject_type}} 主体 {{subject}}、中文「{{cn_title}}」、{{en_title}} 与 {{date_org}}。主体承担主要重量，保留25%–40%有效留白。配色 {{colors}}。要求成熟商业编辑张力，禁止多斜轴、PPT模块化和平均分栏。
```
<!-- P11-META-END -->

## P12｜汉字时尚
**Full name:** 超大汉字 × 几何人物时尚海报
**Core:** 超大汉字做骨架，几何人物进行明确文化行为。
**Template inputs:** `theme, core_character, behavior, object_symbol, colors, support_copy`

<!-- P12-META-START -->
```text
围绕 {{theme}}，让核心汉字「{{core_character}}」成为构图骨架；几何扁平人物执行 {{behavior}}，不是摆拍；{{object_symbol}} 作为文化锚点。使用 {{colors}}，以杂志式中英信息 {{support_copy}} 组织密区与留白。避免古风插画、俗套红金国潮和写实摆拍。
```
<!-- P12-META-END -->

## P13｜概念命题
**Full name:** 高级概念 × 文学命题海报
**Core:** 巨大中文主词+唯一视觉隐喻+极简小字。
**Template inputs:** `core_word, keywords, fate_line, summary`

<!-- P13-META-START -->
```text
先分析「{{core_word}}」的表层义、深层寓意、情绪、文化联想与命运张力，只提炼一个最准确视觉隐喻。巨大中文「{{core_word}}」是绝对主体；小字只允许三处：左上 {{keywords}}、右侧竖排 {{fate_line}}、左下 {{summary}}。极简、克制、展览级，禁止额外长文和泛化人物插画。
```
<!-- P13-META-END -->

## P14｜轮廓夹景
**Full name:** 轮廓中轴 × 东方夹景海报
**Core:** 左右轮廓围出中央空间，中央留白也是构图主体。
**Template inputs:** `theme, cn_title, en_title, left_contour, right_contour, center_content, framing_method, primary, secondary, date_venue`

<!-- P14-META-START -->
```text
用 {{left_contour}} 与 {{right_contour}} 按 {{framing_method}} 围出明确中央空间，把「{{cn_title}}」、{{en_title}} 或 {{center_content}} 放入中轴。双侧只平衡重量，不机械镜像。色彩 {{primary}} + {{secondary}}，信息 {{date_venue}} 归入2–3区。空间先于装饰，适合文化、门店、扫码与品牌信息。
```
<!-- P14-META-END -->

## P15｜体积显字
**Full name:** 体积介质 × 空间显字海报
**Core:** 悬丝/点阵/光束/线网从指定角度显现文字。
**Template inputs:** `main_word, project, medium, spatial_mechanism, subject, primary, support_copy`

<!-- P15-META-START -->
```text
让「{{main_word}}」由 {{medium}} 分布在真实3D空间，并通过 {{spatial_mechanism}} 只在目标相机角度完整显字；侧视保持碎片化。建立前中后景与精确遮挡，{{subject}} 只作尺度参照。项目 {{project}}，主色 {{primary}}，信息 {{support_copy}}。禁止普通3D字、随机霓虹和弱深度。
```
<!-- P15-META-END -->

## P16｜展陈装置
**Full name:** 博物馆装置 × 建筑展陈海报
**Core:** 文字/卡片/品牌符号成为博物馆空间中的主展品。
**Template inputs:** `theme, installation_subject, architecture, mechanism, primary, secondary, support_copy`

<!-- P16-META-START -->
```text
在干净的当代博物馆式 {{architecture}} 中，让 {{installation_subject}} 成为真正展陈装置，并通过 {{mechanism}}（透镜/棱镜/水面模块/透明层板等）建立空间关系。主题 {{theme}}，配色 {{primary}} + {{secondary}}，辅助 {{support_copy}}。自然日光、浅色石材/混凝土、清晰阴影、极少微文案，安静理性而高级。
```
<!-- P16-META-END -->

## P17｜物理形变
**Full name:** 物理作用 × 空间形变海报
**Core:** PRESS/TWIST/FOLD/BALANCE等明确机制驱动文字变形。
**Template inputs:** `project, cn_title, en_title, main_word, mechanism, architecture, primary, secondary, date_location`

<!-- P17-META-START -->
```text
在 {{architecture}} 中，让主词「{{main_word}}」因 {{mechanism}} 的真实力学作用而成立：挤压、扭转、折叠或悬挂平衡。变形必须由受力关系解释，不是普通3D字。项目 {{project}}，标题 {{cn_title}} / {{en_title}}，配色 {{primary}} + {{secondary}}，信息 {{date_location}}。冻结高张力瞬间，结构清晰可信。
```
<!-- P17-META-END -->

## P18｜城市社论
**Full name:** 城市建筑 × 青年社论海报
**Core:** 青年人物+粗野建筑+巨型英文+空间图形统一透视场。
**Template inputs:** `main_title, concept, subject, architecture, spatial_graphic, accent, support_copy`

<!-- P18-META-START -->
```text
使用纯英文排版（除非用户明确覆盖）。在 {{architecture}} 中把真实 {{subject}}、超大浓缩「{{main_title}}」与唯一 {{spatial_graphic}} 统一到同一个透视系统；文字沿建筑透视拉伸、裁切、被人物/混凝土遮挡。概念 {{concept}}，强调色 {{accent}}，辅助 {{support_copy}}。人物与建筑、文字、空间图形同等重要，像国际青年文化杂志，禁止CGI塑料感与无意义微文案。
```
<!-- P18-META-END -->
