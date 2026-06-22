"""风格描述 profile 字典：style_id → 结构化字段，供 style_description_builder 组装 Markdown。"""
from __future__ import annotations

STYLE_PROFILES: dict[str, dict] = {
    "2d_cartoon_illustration": {
        "summary": '商业二维卡通插画美学，形体概括、轮廓锐利、色块分区明确。强调角色表情可读与构图平面感，适合品牌IP、绘本、竖屏短剧分镜与海报。画面完成度偏向印刷级矢量感而非赛璐璐动画帧。',
        "category": '二维插画/商业卡通',
        "artist_refs": 'Adventure Time 美术组、Gravity Falls 设定、国内绘本与条漫插画师',
        "era_texture": '当代数字绘画，可参照复古四色印刷网点',
        "line_control": '外轮廓粗线封边，内线简化，silhouette 优先于体积',
        "lighting_color": '平涂或轻渐变，赛璐璐二层阴影，光源方向全片统一',
        "palette_strategy": '主体高饱和三原色组合，背景降对比留呼吸',
        "atmosphere": '轻快、友好、叙事清晰，适合全年龄喜剧',
        "materials": '布料以色块与简单纹理暗示，金属用高光块面，避免写实材质',
        "quality": '边缘抗锯齿干净，缩略图可辨角色，分层导出友好',
        "taboos": '3D写实渲染, 脏噪颗粒, 错误人体比例, 过度厚涂糊边',
        "characters_zh": '头身比偏Q或中等，五官简化放大，眼睛与嘴型是情绪主通道。服饰纹样图形化，配色不超过三色块为主。动作夸张但关节清晰，适合小图仍识别角色身份。',
        "characters_en": 'stylized cartoon character, bold clean outlines, expressive oversized eyes, simplified features, dynamic friendly pose, flat graphic clothing patterns',
        "scenes_zh": '场景以色块分层构图，透视可适度卡通化。学校、公园、房间等日常空间用固定色板，背景细节克制以突出主体。留白区预留给字幕与对话框。',
        "scenes_en": 'colorful storybook backgrounds, simple perspective interiors, flat layered hills, park and classroom settings, graphic environment design',
        "colors": '明黄, 天蓝, 珊瑚红, 草绿, 柔白, 深棕描边',
        "image_prompt": '2D cartoon illustration, bold clean outlines, flat vibrant colors, expressive character design, simplified shapes, commercial animation key art, crisp edges, storybook aesthetic, high readability, graphic composition, masterpiece quality',
        "video_prompt": 'bouncy cartoon motion, squash and stretch timing, character wave gesture, flat color background, smooth 2D animation energy, playful movement',
        "references": [
        'Adventure Time (2010)',
        'Gravity Falls (2012)',
        'Bluey (2018)',
        '国产商业绘本插画',
        ],
    },
    "3d_american_cartoon_game": {
        "summary": '主机级3D美式卡通游戏美术：夸张比例、装备图标化、关卡可读性优先。借鉴MOBA与平台动作游戏的角色雕塑感与场景层级设计，强调战斗姿态与材质分区。适用于游戏过场、宣传KV与IP设定。',
        "category": '三维数字渲染/美式卡通游戏',
        "artist_refs": 'Blizzard cinematics、Pixar character art、Riot Games 角色设定、Epic stylized assets',
        "era_texture": '2010s–2020s 主流游戏CG工业标准',
        "line_control": '模型轮廓为主，rim light 与描边 shader 强化读形',
        "lighting_color": '三点布光+环境HDRI，强调体积与材质响应',
        "palette_strategy": '阵营色区分，高光区饱和、阴影降饱和',
        "atmosphere": '英雄主义、活力、family-friendly 动作感',
        "materials": 'stylized PBR：皮肤 subsurface、金属 roughness、布料各向异性',
        "quality": '4K细节、抗锯齿干净、景深可按电影镜头使用',
        "taboos": '2D平涂, 低模破面, 错误透视, 过度HDR过曝, 恐怖血腥',
        "characters_zh": '肩宽体块、手脚略放大，盔甲与武器造型图标化。面部 rig 友好，眉弓与下颌线清晰。毛发与披风在战斗pose仍保持轮廓，装备分层便于换色变体。',
        "characters_en": 'chunky heroic proportions, oversized hands and feet, stylized armor, expressive face, action game idle pose, vibrant costume design',
        "scenes_zh": '竞技场、浮空平台、卡通要塞与饱和天空盒构成关卡视觉。前景收集物与中景战斗区层次明确，远景用大气透视降细节。粒子与法术光效 stylized 而非写实。',
        "scenes_en": 'stylized game arena, floating platforms, cartoon fortress, saturated skybox, collectible props, heroic environment',
        "colors": '宝石蓝, 熔岩橙, 翡翠绿, 皇家紫, 金饰高光, 深灰阴影',
        "image_prompt": '3D American cartoon game art, chunky stylized proportions, vibrant PBR materials, heroic character design, stylized game environment, rim lighting, saturated colors, action game key visual, Unreal Engine quality, cinematic composition, 4k render',
        "video_prompt": 'heroic game character idle animation, stylized combat pose shift, rim light sweep, floating platform parallax, energetic cartoon game motion',
        "references": [
        'Overwatch (2016)',
        'Fortnite stylized assets (2017)',
        'Ratchet & Clank (2021)',
        'World of Warcraft cinematics',
        ],
    },
    "3d_american_cartoon_render": {
        "summary": '电影级3D美式卡通渲染管线：Pixar/DreamWorks 式形体语言与物理光照结合。皮肤次表面、布料与毛发系统完整，镜头景深与运动模糊可按动画电影标准执行。适合院线动画风短片与高品质品牌片。',
        "category": '三维动画电影渲染',
        "artist_refs": 'Pixar shading、DreamWorks lighting、Illumination character team',
        "era_texture": '2015–2020s 动画电影工业级渲染',
        "line_control": '无硬描边，靠造型转折与光影分离形体',
        "lighting_color": '物理天空光+区域主光，全局 illumination 柔和',
        "palette_strategy": '情绪驱动色温偏移，阴影偏冷高光偏暖',
        "atmosphere": '温暖、幽默、家庭向，偶有冒险张力',
        "materials": '完整 PBR + subsurface scattering，毛发 clump 结构，织物 weave 细节',
        "quality": '院线动画分辨率，motion blur 与 DOF 电影化',
        "taboos": '2D赛璐璐, 低多边形, 塑料感皮肤, 霓虹赛博, 恐怖元素',
        "characters_zh": '头身比约1:5–1:6，五官温和夸张，酒窝与眉动表演丰富。服饰物理模拟自然，发型 clump 分组清晰。肢体动作遵循动画十二法则，重量感可信。',
        "characters_en": 'Pixar style 3D character, soft subsurface skin, expressive eyebrows, appealing proportions, detailed fabric simulation, warm friendly face',
        "scenes_zh": '郊区住宅、小镇主街、奇幻森林等动画电影常见空间。环境 storytelling 道具丰富，前景引导线明确。天空与云有体积感，地面反射适度。',
        "scenes_en": 'suburban animated film set, stylized neighborhood, volumetric clouds, warm golden hour lighting, detailed environment storytelling props',
        "colors": '暖桃肤, 天蓝, 草绿, 砖红, 柔黄阳光, 紫灰阴影',
        "image_prompt": '3D American cartoon film render, Pixar quality lighting, subsurface skin scattering, appealing character design, warm cinematic atmosphere, detailed stylized environment, soft global illumination, depth of field, animation movie still, 4k',
        "video_prompt": 'smooth Pixar style character performance, gentle camera dolly, fabric and hair simulation, warm lighting shift, family animation film motion',
        "references": [
        'Inside Out (2015)',
        'Coco (2017)',
        'The Mitchells vs. the Machines (2021)',
        'Luca (2021)',
        ],
    },
    "3d_blind_box_paint": {
        "summary": '盲盒手办涂装美学：Q版比例、哑光或半光塑料感、印刷级色块边界。借鉴 POP MART 与潮玩展陈视觉，强调可爱读形与陈列感。适合IP衍生品、电商主图与收藏展示场景。',
        "category": '三维潮玩/盲盒涂装',
        "artist_refs": 'POP MART 设计团队、52TOYS、Good Smile Company Nendoroid 涂装',
        "era_texture": '当代潮玩量产涂装，干净无旧化',
        "line_control": '模型硬边分割色块，无缝合线可见',
        "lighting_color": '棚拍三点光，柔和渐变阴影，无强烈戏剧光比',
        "palette_strategy": '马卡龙或高饱和糖果色，限定色编号感',
        "atmosphere": '可爱、收藏、陈列、社交分享友好',
        "materials": 'PVC哑光/半光，透明件注塑感，金属电镀局部',
        "quality": '产品摄影级锐度，白底或渐变背景',
        "taboos": '写实人体, 破损旧化, 血腥, 复杂场景叙事, 2D手绘感',
        "characters_zh": '二头身或三头身Q版，眼睛占面部1/3，腮红印刷点。发型块状分组，配件磁吸可换。表情系列化：微笑、眨眼、隐藏款特殊色。',
        "characters_en": 'blind box vinyl figure, chibi proportions, glossy painted eyes, cute simplified face, collectible toy aesthetic, smooth plastic surface',
        "scenes_zh": '纯白或浅粉渐变背景，偶配展示底座与透明亚克力盒。系列排列构图，隐藏款用特殊光效突出。',
        "scenes_en": 'product photography setup, white seamless backdrop, acrylic display base, collectible figure lineup, soft studio lighting',
        "colors": '樱花粉, 薄荷绿, 柠檬黄, 天空蓝, 奶油白, 淡紫',
        "image_prompt": 'blind box vinyl figure, chibi collectible toy, smooth PVC paint finish, studio product photography, soft three point lighting, cute character design, pastel color scheme, clean white background, high detail toy render, 4k',
        "video_prompt": 'rotating blind box figure showcase, soft studio light sweep, subtle idle bobbing motion, product reveal spin, collectible toy presentation',
        "references": [
        'POP MART Molly series',
        'SKULLPANDA (2020)',
        'Dimoo world (2019)',
        'Nendoroid product shots',
        ],
    },
    "3d_cartoon_animation": {
        "summary": '全流程3D卡通动画风格：强调运动曲线、表情表演与场景互动。造型介于游戏与电影之间，rig 友好、口型同步清晰。适合系列动画、表情包衍生与短视频角色演绎。',
        "category": '三维卡通动画',
        "artist_refs": 'Cartoon Network 3D shorts、Laika stylized CG、国内3D少儿动画团队',
        "era_texture": '数字动画当代标准，帧率24/30fps 动画感',
        "line_control": '造型块面清晰，动画拉伸时保持体积守恒',
        "lighting_color": '简化三点光，阴影形状服务于表演',
        "palette_strategy": '角色固有色+场景互补色背景',
        "atmosphere": '活泼、节奏快、表演夸张',
        "materials": '卡通 shader，边缘 soft rim，材质种类有限但区分明确',
        "quality": '动画预览到成片一致，无闪烁纹理',
        "taboos": '写实绑定变形, 恐怖表情, 静态概念图感, 帧间闪烁',
        "characters_zh": '比例弹性大， squash & stretch 明显。五官位置固定便于口型，眉毛独立控制器。服装跟随身体拉伸但图案不严重扭曲。',
        "characters_en": '3D cartoon animated character, squash and stretch ready, expressive rig friendly face, bouncy proportions, clear silhouette in motion',
        "scenes_zh": '模块化场景块，便于镜头切换。道具可交互，地面有明确接触阴影。背景色随情绪变但不换风格。',
        "scenes_en": 'modular cartoon environment, interactive props, clear ground contact shadows, colorful animated set design',
        "colors": '亮橙, 电蓝, 草绿, 热粉, 纯白高光, 深紫阴影',
        "image_prompt": '3D cartoon animation style, bouncy character design, squash and stretch proportions, vibrant colors, clear silhouette, animated series quality, soft rim lighting, expressive pose, clean cartoon shading, 4k still frame',
        "video_prompt": 'bouncy 3D cartoon walk cycle, squash stretch body motion, expressive face acting, snappy animation timing, playful character movement',
        "references": [
        'The Amazing World of Gumball CG segments',
        'Kipo and the Age of Wonderbeasts (2020)',
        'Glitch Techs (2020)',
        ],
    },
    "3d_cartoon_render": {
        "summary": '通用3D卡通渲染风格：stylized shader 与适度物理光结合，平衡可爱与完成度。适用于宣传图、封面与单帧插画，非严格动画管线但保留立体读形。',
        "category": '三维风格化渲染',
        "artist_refs": 'Beeple stylized rounds、国内MCN 3D头像、Blender NPR 社区',
        "era_texture": '2020s 社交媒体3D插画流行审美',
        "line_control": '可选轮廓线 post-process，造型圆角友好',
        "lighting_color": '单主光+环境色，阴影边缘 soft',
        "palette_strategy": '渐变背景衬托主体，角色饱和',
        "atmosphere": '时尚、年轻、数字原生',
        "materials": '塑料、哑光陶瓷、简单金属，避免复杂 PBR',
        "quality": '社媒封面级，中心构图，主体占画面60%',
        "taboos": '恐怖写实, 低模, 杂乱背景, 2D混合不一致',
        "characters_zh": '圆润体块，简化五官，腮红与高光点强化可爱。发型几何化，配饰 oversized。姿态适合竖屏封面与头像裁切。',
        "characters_en": 'cute 3D cartoon render, rounded forms, smooth stylized shading, soft gradients, social media avatar style, friendly expression',
        "scenes_zh": '渐变背景或简化几何场景，悬浮元素点缀。少环境叙事，多主体展示。',
        "scenes_en": 'gradient backdrop, floating geometric shapes, minimal stylized environment, social media key visual layout',
        "colors": '珊瑚粉, 薰衣草紫, 薄荷青, 奶油黄, 纯白, 浅灰',
        "image_prompt": '3D cartoon render, rounded stylized character, soft gradient background, smooth NPR shading, cute aesthetic, clean modern design, social media key visual, soft lighting, vibrant pastel colors, high quality still render',
        "video_prompt": 'gentle 3D character turn, soft lighting rotation, floating elements drift, smooth stylized render motion, social media loop animation',
        "references": [
        'Blender NPR community renders',
        '国内3D虚拟头像风格',
        'Kawaii 3D icon design trends',
        ],
    },
    "3d_character_simple_cartoon": {
        "summary": '极简3D卡通角色风格：低面数友好、色块少、识别靠轮廓与主色。适合快速量产、教育内容与移动端性能敏感项目。',
        "category": '三维简约卡通',
        "artist_refs": 'Crossy Road 角色、Fall Guys 简化形体、Google Doodle 3D',
        "era_texture": '移动端与休闲游戏当代审美',
        "line_control": '大面转折，无微细节，silhouette 极度清晰',
        "lighting_color": '单方向光，一层阴影，无复杂反射',
        "palette_strategy": '每角色不超过4色，高对比',
        "atmosphere": '轻松、即时可读、全年龄',
        "materials": '统一 matte 或 slight specular，无纹理贴图依赖',
        "quality": '小图标仍可识别，三角面数可控',
        "taboos": '精细毛孔, 复杂布料, 写实比例, 多材质混合',
        "characters_zh": '几何体组合身体，球体头、圆柱四肢。眼睛两点，嘴一条线。配色跳色区分角色，无渐变皮肤。',
        "characters_en": 'simple 3D cartoon character, geometric body shapes, minimal facial features, bold solid colors, mobile game aesthetic, clear silhouette',
        "scenes_zh": '纯色或简单地面平面，背景一块色。道具同样几何化。',
        "scenes_en": 'flat color background, simple ground plane, geometric props, minimal environment design',
        "colors": '纯红, 纯蓝, 纯黄, 纯白, 纯黑阴影',
        "image_prompt": 'simple 3D cartoon character, geometric minimal design, bold flat colors, mobile game style, clean silhouette, single light source, matte shading, low poly aesthetic, friendly shape language, 4k',
        "video_prompt": 'simple bouncy walk cycle, geometric character hop, minimal environment, snappy mobile game motion, clear silhouette movement',
        "references": [
        'Crossy Road (2014)',
        'Fall Guys (2020)',
        "Alto's Odyssey stylized elements",
        ],
    },
    "3d_cn_fantasy_animation": {
        "summary": '国风3D奇幻动画美学：水墨意境与三维体积并存，借鉴国产奇幻动画电影的角色雕塑与场景宏大叙事。飞檐、云纹、法术光效具有东方符号，光效偏写意而非硬科幻。',
        "category": '三维国风奇幻动画',
        "artist_refs": '追光动画、彩条屋美术、《哪吒》《白蛇》设定团队',
        "era_texture": '2018–2024 国产3D动画电影黄金期',
        "line_control": '衣纹与发丝的流动线条，面部保留东方五官比例',
        "lighting_color": '体积光穿云，夜景靛青+金点缀',
        "palette_strategy": '石青石绿朱红金，肤色暖黄偏粉',
        "atmosphere": '仙侠、史诗、东方奇幻浪漫',
        "materials": '绸缎 anisotropic、金属甲胄雕刻、水墨远山贴图',
        "quality": '院线级4K，毛发与布料解算',
        "taboos": '日式赛璐璐, 欧美超英比例, 霓虹赛博, 西方哥特',
        "characters_zh": '眉眼细长，鼻线柔和，唇色朱红。仙侠服饰宽袖飘带，发簪步摇随动。武将铠甲融合历史与幻想纹样，妖兽保留兽形但具人态表情。',
        "characters_en": 'Chinese fantasy 3D character, flowing hanfu silk, elegant elongated proportions, ornate hair accessories, xianxia warrior design, expressive oriental features',
        "scenes_zh": '云海仙山、凌霄殿、江南水乡、妖界秘境。层峦水墨远景，中景建筑斗拱清晰，前景灵气粒子。',
        "scenes_en": 'misty celestial mountains, Chinese palace with curved eaves, ink wash clouds, lotus pond, fantasy xianxia landscape',
        "colors": '石青, 石绿, 朱红, 藤黄, 金箔, 靛蓝夜',
        "image_prompt": '3D Chinese fantasy animation, xianxia character in flowing robes, misty celestial mountains, ink wash inspired environment, volumetric god rays, mineral blue and vermillion palette, ornate Chinese architecture, cinematic lighting, film quality render, 4k',
        "video_prompt": 'flowing ribbon and silk motion, mist drifting across mountains, gentle camera crane over palace, xianxia spell light particles, ethereal Chinese fantasy atmosphere',
        "references": [
        '哪吒之魔童降世 (2019)',
        '白蛇：缘起 (2019)',
        '深海 (2023)',
        '长安三万里 (2023)',
        ],
    },
    "3d_cn_fantasy_hd": {
        "summary": '高清国风3D奇幻：在奇幻动画基础上强化皮肤毛孔级细节、环境物理与IMAX级构图。适合旗舰宣传、海报与大银幕静帧，材质与光追完成度拉满。',
        "category": '三维国风奇幻/高清写实向',
        "artist_refs": '追光《长安三万里》场景组、UE5 国风社区、腾讯光子美术',
        "era_texture": '2022–2025 国产3D HD 电影工业',
        "line_control": '微观面部皱纹与宏观衣纹并存',
        "lighting_color": 'HDR 环境光，月光与烛火多源',
        "palette_strategy": '矿物颜料色+现代调色胶片感',
        "atmosphere": '史诗、厚重、历史与神话交织',
        "materials": '高清 PBR 木石金属，丝绸高频细节，皮肤 displacement',
        "quality": '8K 静帧可用，光追反射与SSS',
        "taboos": '低模, 塑料皮肤, Anime eyes, 现代街景穿帮',
        "characters_zh": 'Historical-accurate 服饰结构，面部年龄感真实。须发丝丝分明，伤痕与妆面有叙事。持械手部的老茧与金属磨损可见。',
        "characters_en": 'hyperdetailed Chinese fantasy hero, realistic skin texture, ornate historical armor, flowing beard strands, cinematic portrait lighting, epic warrior presence',
        "scenes_zh": '万里长城、黄河渡口、盛唐长安街市，人群与旗帜的中景密度高。烟尘与旗帜物理模拟，天空体积云层次分明。',
        "scenes_en": 'hyperdetailed Tang dynasty cityscape, Yellow River mist, Great Wall vista, crowd filled ancient street, epic historical fantasy environment',
        "colors": '赭石, 靛青, 朱砂, 松绿, 绢白, 炭黑',
        "image_prompt": 'hyperdetailed 3D Chinese fantasy HD render, Tang dynasty architecture, realistic PBR materials, cinematic epic lighting, volumetric atmosphere, intricate costume embroidery, ray traced reflections, IMAX composition, 8k quality, film still',
        "video_prompt": 'slow epic crane shot over ancient city, flags and dust simulation, candlelight flicker interior, majestic Chinese fantasy HD atmosphere, smooth cinematic camera move',
        "references": [
        '长安三万里 (2023)',
        '封神第一部 (2023)',
        'UE5 国风场景社区作品',
        ],
    },
    "3d_cn_style_hd": {
        "summary": '高清国风3D通用风格：强调东方建筑、园林与人物的完成度，不限于纯奇幻，可覆盖历史、武侠与神话。渲染偏写实但保留东方造型比例。',
        "category": '三维国风高清',
        "artist_refs": '《原神》场景美术、《黑神话：悟空》环境组、宋代美学研究参考',
        "era_texture": '当代3A级国风数字美术',
        "line_control": '建筑飞檐曲线与人物体态修长',
        "lighting_color": '自然光为主，晨昏色温变化细腻',
        "palette_strategy": '青绿山水+木构暖棕+点缀朱红',
        "atmosphere": '诗意、沉静、文化厚度',
        "materials": '木石砖瓦 PBR，苔藓与风化，丝绸与麻布',
        "quality": '游戏 cinematics 至电影静帧之间',
        "taboos": '日式鸟居主导, 泰式寺庙混淆, 赛博元素, 低清贴图',
        "characters_zh": '汉服、武侠劲装、道士袍等品类齐全。发型盘髻或束发，配饰玉佩剑穗。表情内敛，动作有武术套路感。',
        "characters_en": 'Chinese style 3D character, hanfu or wuxia outfit, jade accessories, topknot hairstyle, martial arts stance, refined oriental beauty',
        "scenes_zh": '苏州园林、福建土楼、故宫角楼、竹林小径。四季植被变化，雨雾天气常见。',
        "scenes_en": 'Chinese classical garden, bamboo forest path, traditional wooden architecture, misty Jiangnan water town, pagoda on hill',
        "colors": '青绿, 檀棕, 瓦灰, 朱门, 雪白, 苔绿',
        "image_prompt": '3D Chinese style HD environment, traditional architecture with curved eaves, bamboo and mist, PBR wood and stone materials, natural cinematic lighting, Jiangnan aesthetic, detailed cultural props, game cinematic quality, 4k render',
        "video_prompt": 'slow pan through Chinese garden, bamboo sway in breeze, mist rolling over pond, traditional architecture reveal, serene national style atmosphere',
        "references": [
        '黑神话：悟空 (2024)',
        '原神璃月场景',
        '燕云十六声美术',
        ],
    },
    "3d_digital_sculpt": {
        "summary": '数字雕塑展示风格：ZBrush 式高模细节、灰模或单材质渲染，强调形体结构与表面雕刻。适合角色原型、怪物设计与艺术集展示。',
        "category": '三维数字雕塑',
        "artist_refs": 'Mike Nash、Simon Lee、Kojima Productions 概念雕塑',
        "era_texture": '当代数字雕刻工作流标准',
        "line_control": '无描边，靠转折面与雕刻纹理读形',
        "lighting_color": '旋转棚拍光，强调凹凸与法线',
        "palette_strategy": '灰模clay色或单色系材质球',
        "atmosphere": '工作室、原型、艺术研究',
        "materials": 'Clay、wax、或 patina 金属，displacement 主导',
        "quality": '亿级面数烘焙感，毛孔级雕刻',
        "taboos": '最终游戏低模, 鲜艳卡通色, 完整场景叙事',
        "characters_zh": '肌肉解剖准确或怪物异形结构清晰。皮肤褶皱、疤痕、毛孔雕刻可见。_pose 展示扭转与重量。',
        "characters_en": 'digital sculpt bust, ZBrush clay render, anatomical muscle detail, monstrous creature design, displacement pores, studio turntable pose',
        "scenes_zh": '中性灰背景，偶配简单底座。无环境，纯形体研究。',
        "scenes_en": 'neutral gray backdrop, sculpting turntable base, studio lighting rig, minimal presentation environment',
        "colors": '粘土灰, 蜡白, 青铜绿锈, 深褐, 高光白',
        "image_prompt": 'digital sculpt ZBrush render, high poly clay material, anatomical detail, dramatic studio lighting, displacement surface texture, creature design bust, neutral gray background, art station quality, 4k turntable still',
        "video_prompt": 'slow turntable rotation of digital sculpt, studio light sweep across clay surface, reveal anatomical detail, sculpt presentation motion',
        "references": [
        'ZBrush Central featured sculpts',
        'Death Stranding concept sculptures',
        'Love Death + Robots creature maquettes',
        ],
    },
    "3d_diorama_miniature": {
        "summary": '立体沙盘微缩场景：等距或浅景深呈现手工模型感，材质像打印/粘土/微缩模型。适合叙事小品、游戏地图与复古玩具美学。',
        "category": '三维微缩沙盘',
        "artist_refs": 'Teemu Vilppula diorama、Slinkachu 微缩摄影、Tabletop World',
        "era_texture": '手工模型与3D打印当代融合',
        "line_control": '硬边模型感，可见层纹或笔刷痕',
        "lighting_color": '小台灯式暖光，浅景深虚化',
        "palette_strategy": '低饱和复古玩具色，局部跳色',
        "atmosphere": '手工、温暖、叙事小品、收藏模型',
        "materials": '哑光塑料、纸感、假草粉、微缩树木',
        "quality": 'macro 摄影感，1:87 比例暗示',
        "taboos": '真人大小比例, 现代UI, 写实皮肤, 空无一物',
        "characters_zh": '微缩人偶，关节可见或固定pose。面部简化，服装像涂装模型。',
        "characters_en": 'miniature figurine scale character, painted tabletop model, tiny simplified face, diorama scale human figure',
        "scenes_zh": '小房子、铁路、战场、奇幻塔楼组成沙盘。地面有假草、碎石、微缩树。',
        "scenes_en": 'miniature diorama village, tiny houses and trees, tabletop terrain, shallow depth of field, model railroad aesthetic',
        "colors": '模型绿, 土褐, 砖红, 天蓝, 玩具黄',
        "image_prompt": '3D diorama miniature scene, tabletop scale models, shallow depth of field, warm desk lamp lighting, handcrafted toy aesthetic, tiny buildings and figures, macro photography style, matte painted surfaces, cozy narrative vignette, 4k',
        "video_prompt": 'slow macro pan across miniature diorama, shallow focus shift, tiny figure subtle movement, warm lamp glow, handcrafted model world reveal',
        "references": [
        'Teemu Vilppula dioramas',
        'Simon Stålenhag miniatures',
        'Fallout board game terrain',
        ],
    },
    "3d_enhanced_cartoon_render": {
        "summary": '增强型3D卡通渲染：在基础卡通shader上叠加高质量SSS、景深与后期辉光。比简单卡通render更电影化，比Pixar级更 stylized。适合广告与MV主视觉。',
        "category": '三维增强卡通渲染',
        "artist_refs": 'Apple Motion 广告、韩国3D MV、Midas 卡通广告案例',
        "era_texture": '2020s 高端商业3D广告',
        "line_control": '圆角形体+可选 thin outline bloom',
        "lighting_color": '多色轮廓光，bloom 可控',
        "palette_strategy": '品牌色+互补渐变背景',
        "atmosphere": '时尚、高级、数字艺术',
        "materials": '半光塑料、果冻质感、金属点缀',
        "quality": '广告TVC静帧，16:9与9:16双版本',
        "taboos": '粗糙低模, 恐怖, 过度噪点, 写实老人',
        "characters_zh": '潮流服饰，夸张配饰，皮肤有 subtle SSS。发型高光条带状，像沙龙广告。',
        "characters_en": 'enhanced 3D cartoon character, glossy stylized skin, fashion forward outfit, salon hair highlights, commercial ad aesthetic',
        "scenes_zh": '抽象几何舞台、渐变空间、悬浮产品。灯光色片可换。',
        "scenes_en": 'abstract geometric stage, gradient studio space, floating product elements, commercial key visual environment',
        "colors": '电紫, 珊瑚, 青柠, 银白, 深蓝',
        "image_prompt": 'enhanced 3D cartoon render, glossy stylized materials, cinematic bloom and depth of field, fashion commercial lighting, vibrant gradient background, high end advertising quality, smooth character design, 4k key visual',
        "video_prompt": 'smooth camera orbit around enhanced cartoon character, color gel lighting shift, subtle bloom pulse, commercial motion graphics energy, polished 3D ad motion',
        "references": [
        'Apple Services 3D ads',
        'K-pop 3D MV visuals',
        'Behance enhanced cartoon renders',
        ],
    },
    "3d_fantasy_rpg": {
        "summary": '西方奇幻RPG 3D美术：矮人铠甲、精灵弓手、龙与地下城式怪物与中世纪建筑。PBR材质与魔法光效并存，UI图标与过场CG统一语言。',
        "category": '三维奇幻RPG',
        "artist_refs": 'Blizzard WoW、Bethesda、Larian BG3 美术',
        "era_texture": '2005–2025 RPG 美术演进，偏当代 remaster',
        "line_control": '盔甲硬边与布料软边对比',
        "lighting_color": '火炬、魔法球、月光多源',
        "palette_strategy": '阵营色+稀有度金属色（金紫橙）',
        "atmosphere": '冒险、史诗、桌游叙事',
        "materials": '锻铁、皮革、宝石、魔法粒子',
        "quality": '游戏 cinematics 级，可向下兼容实机',
        "taboos": '科幻机甲, 现代枪械, 日式school uniform, 低模',
        "characters_zh": '种族特征明确：尖耳精灵、络腮矮人、兽人獠牙。装备槽位视觉化，武器有使用磨损。披风与链甲层次叠穿。',
        "characters_en": 'fantasy RPG character, elven archer or dwarven warrior, ornate medieval armor, magical glowing weapon, adventure gear, heroic stance',
        "scenes_zh": '酒馆、地牢、森林遗迹、龙巢。宝箱与骷髅叙事道具。雾与火把动态光。',
        "scenes_en": 'medieval fantasy tavern, dungeon corridor torches, ancient forest ruins, dragon lair treasure, RPG adventure environment',
        "colors": '钢灰, 皮革棕, 魔法蓝, 毒绿, 宝金, 血红',
        "image_prompt": '3D fantasy RPG scene, elven warrior in ornate armor, medieval dungeon torchlight, magical particle effects, PBR metal and leather, epic adventure composition, game cinematic quality, detailed fantasy environment, 4k render',
        "video_prompt": 'torch flicker in dungeon, character draws glowing sword, magical particles swirl, fantasy RPG cinematic camera push, adventure atmosphere motion',
        "references": [
        'World of Warcraft (2004–)',
        "Baldur's Gate 3 (2023)",
        'Diablo IV (2023)',
        'Elder Scrolls V (2011)',
        ],
    },
    "3d_game_render": {
        "summary": '实时游戏引擎渲染风格：Unreal/Unity 即时画面美学，Lumen/Nanite 或 stylized 游戏shader。强调可玩视角与关卡可读性。',
        "category": '三维游戏引擎渲染',
        "artist_refs": 'Epic Games demos、PlayStation first-party、国产3A实机',
        "era_texture": '2020s 次世代实机或接近实机',
        "line_control": 'LOD友好，远景简化',
        "lighting_color": '动态天光+补光探针',
        "palette_strategy": '关卡引导色与危险区对比',
        "atmosphere": '沉浸、可探索、交互暗示',
        "materials": '引擎PBR标准，tiling 可控',
        "quality": '60fps 美感，无过锐AA',
        "taboos": '离线渲染过度景深, 不可玩构图, 2D混合',
        "characters_zh": '游戏主角第三人称比例，装备可见，动画状态机友好。NPC 脸型模块化。',
        "characters_en": 'video game protagonist, third person adventure gear, engine ready character model, gameplay pose, interactive hero design',
        "scenes_zh": '开放世界片段、室内关卡、战斗竞技场。路径与掩体布局清晰。',
        "scenes_en": 'open world game environment, explorable ruins, gameplay readable layout, dynamic sky system, next gen game graphics',
        "colors": '环境固有色, 任务标记黄, 危险红, UI蓝',
        "image_prompt": 'real time game engine render, next gen graphics, Unreal Engine quality, explorable 3D environment, dynamic lighting, PBR materials, gameplay cinematic shot, detailed game world, 4k screenshot aesthetic',
        "video_prompt": 'third person game camera follow, dynamic time of day shift, foliage wind animation, real time game engine motion, explorable world movement',
        "references": [
        'Unreal Engine 5 Matrix demo',
        'Horizon Forbidden West (2022)',
        '黑神话：悟空 实机',
        ],
    },
    "3d_glossy_latex": {
        "summary": '高光乳胶/漆皮3D风格：极端 specular 与 tight highlight，形体像充气或浇铸橡胶。流行于时尚插画、俱乐部视觉与超现实产品艺术。',
        "category": '三维高光乳胶/漆皮',
        "artist_refs": 'Kaws 乙烯基延伸美学、Jeff Koons 气球、3D latex fashion renders',
        "era_texture": '当代数字时尚与pop surrealism',
        "line_control": '无缝圆角，反射轮廓即边界',
        "lighting_color": '硬光产生长条高光，环境映射强',
        "palette_strategy": '单色大面积+少量对比色',
        "atmosphere": '前卫、 glossy、超现实时尚',
        "materials": 'latex、vinyl、liquid metal，IOR 高反射',
        "quality": '产品级反射干净，无噪点',
        "taboos": ' matte皮肤, 自然户外, 历史服饰, 脏旧',
        "characters_zh": '人体或人偶漆皮化，五官简化或面具化。姿态像模特或 mannequin，关节反射强烈。',
        "characters_en": 'glossy latex 3D figure, inflatable shiny surface, mannequin pose, tight specular highlights, fashion surreal character',
        "scenes_zh": '纯色无缝背景或镜面地面，偶配几何道具。',
        "scenes_en": 'seamless studio backdrop, mirror floor reflection, geometric prop, high gloss product stage',
        "colors": '漆红, 液态银, 深黑, 荧光粉, 纯白高光',
        "image_prompt": 'glossy latex 3D render, tight specular highlights, inflatable shiny vinyl surface, fashion mannequin figure, mirror floor reflection, studio hard lighting, pop surreal aesthetic, ultra clean reflections, 4k',
        "video_prompt": 'slow rotation of glossy latex figure, specular highlight travel, mirror reflection ripple, surreal fashion object motion, studio light sweep',
        "references": [
        'Jeff Koons balloon dog aesthetic',
        '3D latex fashion editorials',
        'Kaws companion vinyl',
        ],
    },
    "3d_hd_realistic_render": {
        "summary": '高清写实3D渲染：建筑可视化与产品级光线追踪，材质物理准确，构图像建筑摄影或汽车广告。人物若出现则接近数字人类。',
        "category": '三维高清写实渲染',
        "artist_refs": 'Brick Visual、MIR、The Mill automotive',
        "era_texture": '2020s archviz 与产品渲染标准',
        "line_control": '摄影构图，无风格化变形',
        "lighting_color": 'HDRI 真实太阳高度角，室内IES灯',
        "palette_strategy": '真实世界色温，品牌色仅小面积',
        "atmosphere": '专业、可信、商业交付',
        "materials": '完整PBR库：玻璃、混凝土、车漆',
        "quality": '8K archviz，打印可用',
        "taboos": '卡通比例, toon shader, 过度饱和, 幻想元素',
        "characters_zh": '若有人物，数字人类级别皮肤与毛发，商务或生活化着装。',
        "characters_en": 'photorealistic 3D human, digital human skin, business casual outfit, natural portrait pose, ray traced subsurface',
        "scenes_zh": '现代建筑内外、展厅、城市天际线。黄金时刻或阴天soft light。',
        "scenes_en": 'photorealistic modern architecture interior, city skyline vista, architectural visualization, natural daylight, clean minimalist space',
        "colors": '混凝土灰, 玻璃蓝反射, 木暖棕, 植物绿, 天空渐变',
        "image_prompt": 'photorealistic 3D HD render, architectural visualization quality, ray traced global illumination, physically accurate materials, natural daylight, clean modern interior, ultra detailed surfaces, commercial photography composition, 8k',
        "video_prompt": 'slow architectural camera dolly, natural light shift across glass facade, photorealistic environment motion, clean corporate visualization flythrough',
        "references": [
        'Brick Visual archviz',
        'Unreal Archviz samples',
        'The Mill automotive renders',
        ],
    },
    "3d_impasto_paint": {
        "summary": '3D impasto 油画风格：几何体或角色表面像厚涂颜料堆叠，笔刷方向可见，光在颜料棱脊上跳动。数字雕塑与古典绘画的混合美学。',
        "category": '三维厚涂油画',
        "artist_refs": 'Van Gogh 3D interpretations、Adobe Substance 油画笔刷实验',
        "era_texture": 'Post-impressionist 数字再诠释',
        "line_control": '笔刷脊线替代描边',
        "lighting_color": '侧光强调颜料厚度阴影',
        "palette_strategy": '互补色并置，颜料混合不完全',
        "atmosphere": '艺术画廊、情感强烈、手工感',
        "materials": 'displacement 油画堆叠，canvas 底纹',
        "quality": '近看笔刷细节，远看构图完整',
        "taboos": '平滑PBR, 摄影写实, 霓虹, 低面',
        "characters_zh": '肖像或全身像，面部由色块与笔触构成，表情印象派。',
        "characters_en": 'impasto painted 3D portrait, thick brushstroke surface, post impressionist figure, visible paint ridges, artistic sculptural form',
        "scenes_zh": '星空、麦田、卧室等名画场景三维化，笔触延续到背景。',
        "scenes_en": 'impasto painted landscape, swirling brushstroke sky, post impressionist 3D environment, thick oil paint terrain',
        "colors": '钴蓝, 铬黄, 氧化绿, 朱红, 薰衣草, 象牙黑',
        "image_prompt": '3D impasto oil paint render, thick visible brushstrokes, post impressionist style, paint ridges catching light, artistic portrait or landscape, canvas texture, gallery quality digital sculpture, vibrant complementary colors, 4k',
        "video_prompt": 'camera move revealing brushstroke depth, light shift across paint ridges, swirling impasto sky motion, artistic painted 3D scene animation',
        "references": [
        'Van Gogh immersive 3D exhibits',
        'Brushstroke VR experiences',
        'ArtStation impasto 3D studies',
        ],
    },
    "3d_jelly_plastic": {
        "summary": '果冻塑料3D风格：半透明 subsurface、内发光、Q弹变形。像软糖、硅胶玩具或bubble UI 的立体版。',
        "category": '三维果冻/半透明塑料',
        "artist_refs": 'Apple emoji 3D、各种 jelly UI motion、盲盒透明款',
        "era_texture": '2020s 3D icon 与 motion design',
        "line_control": '圆角无硬边，折射即轮廓',
        "lighting_color": '背光透射+正面补光',
        "palette_strategy": '糖果半透明叠色',
        "atmosphere": '可爱、软萌、数字原生',
        "materials": 'SSS plastic、clear coat、bubble inclusion',
        "quality": '图标至海报均可，边缘无锯齿',
        "taboos": '写实皮肤, 金属, 恐怖, 脏迹',
        "characters_zh": '物体或生物果冻化，内部可能有气泡层。眼睛像嵌入的糖珠。',
        "characters_en": 'jelly plastic 3D character, translucent subsurface, cute blob form, candy color body, soft bouncy appearance',
        "scenes_zh": '渐变背景，悬浮同类 jelly 元素，像APP开屏。',
        "scenes_en": 'pastel gradient space, floating jelly objects, soft caustics, playful 3D icon environment',
        "colors": '半透明桃, 薄荷, 柠檬, 葡萄紫, 奶白',
        "image_prompt": '3D jelly plastic render, translucent subsurface scattering, candy colors, soft bouncy form, caustic light transmission, cute character or object, pastel gradient background, clean modern 3D icon aesthetic, 4k',
        "video_prompt": 'jelly character wobble bounce, subsurface light pulse, soft squash deformation, playful elastic motion, candy color shimmer',
        "references": [
        'Apple Memoji 3D style',
        'Microsoft Fluent 3D icons',
        'Jelly motion design reels',
        ],
    },
    "3d_pbr_realistic": {
        "summary": '标准PBR写实3D：金属度/粗糙度工作流，IBL照明，适合产品、硬表面与写实角色。无风格化偏移，科学准确优先。',
        "category": '三维PBR写实',
        "artist_refs": 'Quixel Megascans、Substance 3D 社区、Weta Digital 硬表面',
        "era_texture": '当代VFX与游戏共用PBR标准',
        "line_control": '真实比例与摄影构图',
        "lighting_color": '物理正确，能量守恒',
        "palette_strategy": '真实世界 albedo，后期调色克制',
        "atmosphere": '可信、工业、交付导向',
        "materials": 'Quixel级扫描材质，macro detail',
        "quality": 'film/VFX asset 级',
        "taboos": 'toon outline, 错误金属度, 过度bloom',
        "characters_zh": '写实绑定，毛孔位移，服装 physically based。',
        "characters_en": 'PBR realistic human, scanned skin texture, physically based clothing, neutral studio pose, accurate proportions',
        "scenes_zh": '工业车间、实验室、现代办公室，道具有使用痕迹。',
        "scenes_en": 'PBR realistic interior, industrial workshop, physically based props, accurate material response, studio HDRI lighting',
        "colors": '真实albedo, 中性灰环境, 金属 specular, 橡胶 matte',
        "image_prompt": 'PBR realistic 3D render, physically based materials, accurate metalness and roughness, HDRI studio lighting, photorealistic hard surface details, industrial quality textures, commercial product visualization, 4k',
        "video_prompt": 'studio HDRI rotation, subtle material specular shift, PBR accurate light response, product turntable motion, realistic environment parallax',
        "references": [
        'Quixel Megascans library',
        'Substance 3D showcase',
        'Love Death + Robots realistic episodes',
        ],
    },
    "3d_stylized_render": {
        "summary": '通用3D风格化渲染：介于卡通与写实之间，常见于独立游戏与动画短片。形状语言统一，材质简化但光影有体积。',
        "category": '三维风格化渲染',
        "artist_refs": 'Studio Ghibli 3D experiments、RiME、Journey 美术',
        "era_texture": '2010s 独立游戏美学延续',
        "line_control": '简化形体，夸张比例可选',
        "lighting_color": '绘画式明暗，非严格物理',
        "palette_strategy": '有限色板，像调色盘选色',
        "atmosphere": '诗意、探索、情感优先',
        "materials": '手绘贴图混合PBR',
        "quality": '艺术方向一致比分辨率更重要',
        "taboos": '两种风格混搭, 写实脸+卡通身, HDR过曝',
        "characters_zh": '头略大或四肢简化，服装色块大。表情温和，眼睛有高光点。',
        "characters_en": 'stylized 3D character, painterly shading, simplified proportions, emotive eyes, indie game aesthetic, cohesive shape language',
        "scenes_zh": '沙丘、遗迹、浮岛，留白多，远景大气。',
        "scenes_en": 'stylized desert ruins, floating islands, painterly sky gradient, minimalist poetic landscape, indie game environment',
        "colors": '暮紫, 沙金, 海蓝, 珊瑚, 柔白雾',
        "image_prompt": 'stylized 3D render, painterly lighting, simplified shapes, indie game aesthetic, emotive character design, poetic landscape, limited color palette, artistic shading, cohesive art direction, 4k',
        "video_prompt": 'gentle wind through stylized landscape, character scarf flutter, painterly light shift, poetic indie game camera drift, emotional atmosphere',
        "references": [
        'Journey (2012)',
        'RiME (2017)',
        'Gris (2018)',
        'Kena: Bridge of Spirits (2021)',
        ],
    },
    "3d_surreal_render": {
        "summary": '3D超现实渲染：达利/马格利特式空间悖论，真实材质置于不可能场景。梦境逻辑、比例错位、无限延伸。',
        "category": '三维超现实主义',
        "artist_refs": 'Salvador Dalí、René Magritte 3D homages、Beeple surreal',
        "era_texture": '当代艺术数字再创作',
        "line_control": '写实物体+非写实组合',
        "lighting_color": '戏剧单光源或平光梦境',
        "palette_strategy": '沙漠暖调或冷蓝梦境对比',
        "atmosphere": '梦境、不安、哲学隐喻',
        "materials": '写实 PBR 与 melting/deforming 混合',
        "quality": '概念艺术印刷级',
        "taboos": '纯卡通, 商业产品照, 解释性文字',
        "characters_zh": '人物常静止或重复，脸被物体替代，或肢体融化。',
        "characters_en": 'surreal 3D figure, melting clock aesthetic, face obscured by object, dreamlike stiff pose, metaphysical character',
        "scenes_zh": '沙漠长影、浮空岩石、门框通向海、巨大物体在客厅。',
        "scenes_en": 'surreal desert landscape, floating rocks, doorframe opening to ocean, oversized object in room, dream paradox architecture',
        "colors": '沙漠金, 天空蓝, 本白, 深影褐, 梦境紫',
        "image_prompt": '3D surreal render, dreamlike impossible architecture, melting forms, desert horizon long shadows, metaphysical composition, photorealistic objects in paradox scene, Dalí inspired aesthetic, cinematic surrealism, 4k',
        "video_prompt": 'slow surreal camera drift, melting object morph, impossible door reveal, dreamlike floating motion, metaphysical scene transition',
        "references": [
        'Dalí Persistence of Memory homages',
        'Magritte 3D interpretations',
        'Beeple surreal dailies',
        ],
    },
    "3d_western_cartoon": {
        "summary": '3D西方卡通：Disney/TV animation 的立体版，形体夸张、表情表演优先，shader 偏 flat color 分区而非写实 PBR。',
        "category": '三维西方卡通',
        "artist_refs": 'Disney TV 3D、Nickelodeon、Cloudy with a Chance of Meatballs',
        "era_texture": '2000s–2010s 电视动画3D',
        "line_control": 'thick brow line 模型化，silhouette 卡通',
        "lighting_color": '简化 cel shading 分层',
        "palette_strategy": '固有色+阴影色偏紫或蓝',
        "atmosphere": '搞笑、家庭、快节奏',
        "materials": 'matte toon，无复杂 SSS',
        "quality": '广播级干净，口型清晰',
        "taboos": '写实恐怖, 日系萌系, 低帧',
        "characters_zh": '手脚弹性大，鼻子可夸张。服装色块分明，像2D设定挤出3D。',
        "characters_en": 'western 3D cartoon character, TV animation style, exaggerated proportions, toon shading, expressive slapstick face, bouncy limbs',
        "scenes_zh": '郊区、学校、科幻实验室卡通化。道具 oversized 制造笑料。',
        "scenes_en": 'cartoon suburban house, wacky science lab, stylized school hallway, exaggerated prop scale, bright TV animation set',
        "colors": '电视红, 电视蓝, 草绿, 肤色 peach, 阴影紫',
        "image_prompt": '3D western cartoon style, TV animation aesthetic, toon shaded character, exaggerated proportions, bright saturated colors, slapstick expressive design, clean matte surfaces, family animation quality, 4k',
        "video_prompt": 'slapstick cartoon bounce, exaggerated take expression, toon shaded character hop, wacky prop animation, TV cartoon timing',
        "references": [
        'Cloudy with a Chance of Meatballs (2009)',
        'Hotel Transylvania TV look',
        'The Loud House 3D specials',
        ],
    },
    "3d_western_cartoon_draw": {
        "summary": '3D西方卡通+手绘混合：模型渲染后叠加笔触、描边或二维纹理，像《蜘蛛侠：平行宇宙》的3D分支但更轻量。',
        "category": '三维卡通手绘混合',
        "artist_refs": 'Spider-Verse technical art、Arcane 部分管线、Guilty Gear stylized',
        "era_texture": '2018–2024 手绘3D融合浪潮',
        "line_control": 'screen-space 或 texture 描边，帧间变化可控',
        "lighting_color": '绘画式色块光影',
        "palette_strategy": '漫画网点或水彩纹理叠层',
        "atmosphere": '漫画动势、艺术实验、年轻向',
        "materials": '3D base + hand-painted normal/roughness',
        "quality": '静帧像插画，动画保持风格',
        "taboos": '纯PBR写实, 风格帧间不一致, 无笔触',
        "characters_zh": '英雄pose带速度线纹理，脸部 halftone 阴影。',
        "characters_en": 'hand drawn 3D cartoon hero, comic ink outlines on 3D model, halftone shading, dynamic action pose, stylized brush textures',
        "scenes_zh": '城市屋顶、漫画分格感背景、色块爆炸特效。',
        "scenes_en": 'comic panel styled city rooftop, hand painted texture environment, halftone sky, dynamic action background',
        "colors": '漫画红, 墨黑线, 天蓝, 黄爆炸, 紫阴影',
        "image_prompt": '3D western cartoon with hand drawn textures, comic ink outlines, halftone shading on 3D model, dynamic hero pose, painterly brush overlays, Spider-Verse inspired aesthetic, vibrant colors, 4k',
        "video_prompt": 'comic line boil on 3D character, halftone flicker effect, dynamic action smear frames, hand drawn texture shift, stylized hybrid animation motion',
        "references": [
        'Spider-Man: Into the Spider-Verse (2018)',
        'Arcane (2021)',
        'TMNT: Mutant Mayhem (2023)',
        ],
    },
    "absurdist_high_key_white": {
        "summary": (
            "荒诞高调白色调电影风格：以当代时尚概念摄影与超现实装置（Tim Walker、"
            "Maurizio Cattelan、Juergen Teller 高调商业片）为基准，呈现无缝白墙过曝、"
            "物体比例错乱与 deadpan 模特并存的「absurdist high key + surreal scale」视觉语法。"
            "人物以时尚 deadpan 或与超大道具互动为核心；场景强调无缝白墙棚、悬浮日常物放大、"
            "地面几乎无影。整体为 live-action high key studio photography，偏纯白主导+单点饱和色 LUT，"
            "绝不做黑暗恐怖 low-key、复杂叙事文字或脏背景主导。"
            "适合荒诞幽默广告、时尚艺术片、超现实概念 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 荒诞高调白（Absurdist High Key White Cinematic Live-Action）",
        "artist_refs": (
            "摄影：Tim Walker、Juergen Teller、Maurizio Cattelan 装置摄影；"
            "美学：seamless white overexposure、surreal scale mismatch、"
            "fashion deadpan、minimal shadow high key multi-light；"
            "参照：Vogue 概念大片、当代艺术摄影装置。"
        ),
        "era_texture": (
            "当代时尚与概念摄影 digital clean；"
            "白墙过曝但物体边缘 crisp readable；"
            "材质真实但情境荒谬（oversized prop、floating arrangement）；"
            "digital 须 emulate 时尚杂志印刷级，无 gritty documentary grain。"
        ),
        "line_control": (
            "构图物体与人物清晰边缘 against 白；"
            "中心或不对称均可，强调 scale 对比；"
            "少景深混乱，主体 isolates on white；"
            "movement 慢：slow push absurd set、subtle object float。"
        ),
        "lighting_color": (
            "主光：多灯高调，阴影极淡几乎无地面影；"
            "辅光：fill 充足保持白底干净；"
            "单点饱和色 accent（珊瑚、电蓝、亮黄）；"
            "禁忌：low-key noir、dirty background、sick green horror。"
        ),
        "palette_strategy": (
            "主调：纯白、亮黄点缀、珊瑚、电蓝小面积、肤白；"
            "白主导 90%+ frame，accent 色块精准；"
            "肤色 pale fashion 无 tan glamour；"
            "叙事可用单点色块 shift 非整体 darken。"
        ),
        "atmosphere": (
            "荒诞、冷幽默、时尚疏离、Instagram 艺术摄影感；"
            "静止 deadpan 与过度表演并存；"
            "干净、超现实、商业摄影棚+装置艺术；"
            "非温馨治愈或恐怖血腥。"
        ),
        "materials": (
            "真实材质（陶瓷、塑料、织物）但比例荒谬；"
            "oversized everyday object、seamless vinyl floor；"
            "忌泥血、rust industrial、neon cyber alley。"
        ),
        "quality": (
            "时尚杂志印刷级：crisp edge、白底无脏点；"
            "fabric texture 在白底上 readable；"
            "4K clean，thumbnail 可辨 scale absurdity 与 deadpan face。"
        ),
        "taboos": (
            "黑暗恐怖 low-key、复杂叙事文字 overlay、脏背景、"
            "horror gore、documentary grit、cyber neon night。"
        ),
        "characters_zh": (
            "模特式静止或与超大道具互动；"
            "表情 deadpan 或过度表演；"
            "时尚妆面 clean，发型造型感强；"
            "姿态可僵硬或 surreal interaction。"
        ),
        "characters_en": (
            "absurdist fashion figure deadpan expression, oversized prop interaction, "
            "high key white seamless studio, surreal scale mismatch, "
            "minimal shadow fashion portrait, contemporary art photography presence"
        ),
        "scenes_zh": (
            "无缝白墙摄影棚、悬浮日常物放大、"
            "地面几乎无影时尚布景、单色道具装置、"
            "纯白 infinity backdrop 概念空间。"
        ),
        "scenes_en": (
            "high key white seamless studio overexposed, oversized everyday objects surreal scale, "
            "floating absurd arrangement minimal shadow, fashion set infinity white backdrop, "
            "contemporary art installation photography"
        ),
        "colors": "纯白, 亮黄点缀, 珊瑚, 电蓝小面积, 肤白, 淡粉",
        "image_prompt": (
            "absurdist high key white photography, seamless overexposed white background, "
            "surreal scale objects fashion deadpan model, minimal shadows clean studio lighting, "
            "contemporary art aesthetic crisp detail, Tim Walker inspired absurd composition, 4k"
        ),
        "video_prompt": (
            "slow push on absurd white set, subtle object float surreal, "
            "high key lighting steady no shadow drift, deadpan fashion motion minimal, "
            "surreal scale prop interaction slow reveal"
        ),
        "references": [
            "Tim Walker fashion spreads",
            "Maurizio Cattelan installations",
            "Juergen Teller campaigns",
        ],
    },
    "american_boom_era": {
        "summary": (
            "上海美术电影制片厂（上美影）经典二维国风动画美学高峰：融合传统工笔重彩、水墨山水（Shanshui）、"
            "年画/木刻民间美术与京剧脸谱（Lianpu）程式，代表作气质涵盖《大闹天宫》《哪吒闹海》《天书奇谭》"
            "《九色鹿》等 1960s–1980s 手绘赛璐璐。线条如书法般粗细顿挫，色块平涂为主、局部柔和晕染，"
            "人物造型略带泥塑/年画偶感，比例可适度夸张（天书奇谭式丑角与正角对照），动物角色拟人而保留物种特征。"
            "背景采用散点透视的层峦祥云、古松飞檐与绢本纸纹质感，整体神话童话、民间寓言、东方奇幻诗意并存，"
            "绝无 3D CG 体积光、日系大眼赛璐璐或欧美超英比例。适合神话题材、古典传奇、少儿寓言及民族符号感 AIGC 短剧/漫剧。"
        ),
        "category": "二维国风经典动画 / 上海美术电影制片厂（Shangmei / Shanghai Animation Film Studio）",
        "artist_refs": (
            "上海美术电影制片厂；导演/主创：万籁鸣、唐澄、严定宪、王树忱、胡进庆、特伟、钱家骏；"
            "美学参照：《大闹天宫》《哪吒闹海》《天书奇谭》《九色鹿》《葫芦兄弟》；"
            "传统来源：工笔画勾线、年画配色、京剧脸谱与水袖身段、木刻年画与民间泥塑。"
        ),
        "era_texture": (
            "1960s–1980s 中国手绘赛璐璐 + 工笔重彩 + 绢本/宣纸媒介感。"
            "全画面带轻微纸纹/绢纹颗粒与暖黄陈旧色调（仿 aged Xuan paper or silk scroll），"
            "色块边缘可见水粉/ gouache 平涂与少量水彩洇染，缩放仍保持干净 2D 平面，无现代数码 HDR 与 3D 渲染。"
        ),
        "line_control": (
            "书法式勾线：外轮廓粗黑、内线工笔，线条粗细随运笔变化（thick-to-thin calligraphic stroke），"
            "衣纹/云纹/水纹为连续曲线与折线并用；天书奇谭系可几何尖角与流动长曲线融合。"
            "Silhouette 清晰，边缘 decisive，少厚涂糊边；拟人动物（狐、猴、龙）同样以 bold ink outline 统摄。"
        ),
        "lighting_color": (
            "弱化单一强光源与西方明暗法；以色彩明暗分层、相邻色块对比暗示体积。"
            "大面积平涂 + 极柔和 atmospheric gradient（非写实 shadow），夜景靛青/群青底 + 局部暖黄灯火；"
            "肤色暖黄偏粉，戏曲妆面可在眼周/眉心加朱红或白粉（Lianpu 程式）。"
        ),
        "palette_strategy": (
            "矿物重彩体系：朱砂朱红、石青/群青、石绿/孔雀绿、藤黄、赭石、金箔勾边；"
            "高饱和但和谐，类似年画与工笔重彩；天空常青蓝渐变留白，水面青绿加白浪；"
            "正角可用暖金/明黄，反派或丑角可用紫、青、冷灰对照（天书奇谭式色彩象征）。"
            "点缀：桃粉、橙黄、 ivory 白，忌荧光霓虹与纯黑死灰大面积。"
        ),
        "atmosphere": (
            "神话感、童话感、民间寓言的温厚与奇崛并存；英雄主义与戏谑 caricature 可同屏（天书奇谭）。"
            "游观式、卷轴式浏览感，战斗场面仍保持平面装饰性与色块对比，非写实血腥；"
            "文化融合创作时须保留上美 DNA（线、色、云、山、脸谱），仅替换角色题材不替换美学。"
        ),
        "materials": (
            "人物：泥塑/年画偶质感、绢本平涂皮肤、戏曲油彩妆面；"
            "服饰：绸缎宽袖、水袖（long white sleeves）、云肩、步摇、冠簪、飘带随动；"
            "建筑：木构殿宇、琉璃瓦、飞檐斗拱（dougong）、红灯笼、旌旗；"
            "环境：皴法山石（Cun stroke）、古松针叶簇、莲花、锦鲤、瀑布；"
            "装饰：祥云纹（Xiangyun / mianmian yun 连绵云）、回纹、卷草、龙纹；"
            "文化元素：竖排书法匾牌、朱文方印（cinnabar seal chop）可作构图道具。"
        ),
        "quality": (
            "赛璐璐平涂干净、线稿锐利、缩放仍清晰；2D vector-like precision 与手绘温度并存；"
            "适合 16:9 横版角色卡与 9:16 竖版海报；4k 细节但不引入 3D 体积光或厚涂写实。"
        ),
        "taboos": (
            "3D CG 渲染、PBR 材质、写实厚涂、HDR 过曝、镜头光晕；"
            "日式赛璐璐大眼萌、欧美超英肌肉比例、霓虹赛博、低饱和莫兰迪灰调主导；"
            "photorealistic、anime cel shading gradients、复杂西方透视阴影、"
            "multipanel comic grid（角色卡须单图时）、watermark、脏污噪点背景。"
        ),
        "characters_zh": (
            "【面部·戏曲影响】凤眼/杏仁眼、瞳孔偏小；剑眉/柳叶眉；鼻线一笔；唇朱红或淡粉。"
            "天书奇谭式可夸张：脸 elongated 或正圆、鼻 chin 推到极端以定性格；"
            "丑角/小丑（Chou）可在眼鼻围白粉；正角（Sheng/Dan）清俊，反派（Jing）脸谱化色块但不过度恐怖。"
            "【体型】仙神修长（头身约 1:6–1:7），武将肩宽腰窄，孩童头略大；"
            "天书奇谭：Fox Mother 佝偻尖 silhouette，Dan Sheng 少年黄袍，Fox Girl 修长 tapering lines。"
            "【发型】高髻、双环髻、飞天髻、披发；发为 solid graphic shape，墨黑锐点，少量 stylized highlight。"
            "【服饰】汉服、铠甲、僧袍（patchwork kasaya）、宫装；宽袖水袖、长摆、腰带；"
            "龙纹、云纹、八卦、莲花、 yin-yang 纹样；飘带/步摇随武舞姿态流动。"
            "【姿态】京剧武舞/武术 stance：张力夸张、肢体延展；披风与飘带呈 ribbon arcs。"
            "【动物拟人】狐、猴、龙等保留物种特征（尾、耳、爪）+ 人形体态与同样线色体系；"
            "可并排展示人形与兽形（天书奇谭 Fox Mother / Fox Girl）。"
            "【气质范例】孙悟空——机敏桀骜；哪吒——英气少年；仙女——轻盈疏离；"
            "袁公——白袍红须正色；小皇帝——黄袍龙纹；阿拐——紫袍 clown 白脸。"
        ),
        "characters_en": (
            "Shanghai Animation Film Studio classic Chinese animation character, Tian Shu Qi Tan aesthetic, "
            "Uproar in Heaven style, calligraphic ink outlines with thick-to-thin brush variation, "
            "flat gouache and mineral pigment fills, Peking opera Lianpu inspired face with red eyeshadow, "
            "phoenix eyes, stylized martial arts wushu pose, flowing hanfu with water sleeves, "
            "exaggerated theatrical proportions, clay figurine and folk woodblock print influence, "
            "elongated or caricature silhouette, mythological Chinese design, bold black contours, "
            "no 3D render, no modern anime eyes"
        ),
        "scenes_zh": (
            "【典型环境】天宫凌霄殿、东海龙宫、花果山、江南水乡、云雾仙山、古寺竹林、荷花池、皇城宫殿。"
            "【山水 Shanshui】层峦叠嶂、近实远虚、青绿山水与水墨晕染结合；"
            "山体用 vertical Cun 皴法纹理，远景淡墨留白。"
            "【祥云 Xiangyun】如意云头、连绵卷云（mianmian yun）、丝带状云纹框景，可绕人物盘旋。"
            "【建筑】多层 pagoda 飞檐翘角、 dougong 斗拱、朱墙绿瓦；栏杆、石阶作前景框景。"
            "【植被】虬劲古松、针叶簇状墨点、垂柳、莲花。"
            "【构图】横卷轴或竖幅山水式；散点透视；主体置黄金分割；"
            "可加竖排书法匾牌、朱印；战斗仍平面装饰、色块对比。"
        ),
        "scenes_en": (
            "misty Chinese Shanshui landscape, layered blue-green mountains with ink wash mist, "
            "stylized Xiangyun auspicious clouds, ancient pagoda with upturned eaves and dougong brackets, "
            "gnarled pine trees on mountain ridges, celestial Chinese palace hall, lotus pond, "
            "decorative cloud ribbon patterns, scattered perspective traditional Chinese composition, "
            "vertical calligraphy plaque and cinnabar seal chop, mythological East Asian setting, "
            "aged xuan paper texture background, flat illustrative depth"
        ),
        "colors": (
            "主色：朱红/朱砂、石青/群青、石绿/孔雀绿、藤黄、赭石、金箔、靛蓝；"
            "辅助：象牙白、淡墨灰、桃粉、橙黄点缀、暖黄肤色；"
            "天书奇谭对照：正色暖金/明黄 vs 反派紫/青/冷灰；"
            "天空青蓝渐变留白，水面青绿加白浪；忌荧光、霓虹、纯黑死灰大面积"
        ),
        "image_prompt": (
            "Shanghai Animation Film Studio classic Chinese animation style, Tian Shu Qi Tan and Uproar in Heaven aesthetic, "
            "1960s-1980s hand-painted cel animation, calligraphic ink outlines with thick-to-thin brush strokes, "
            "flat gouache mineral pigment color blocks with subtle paper grain texture, "
            "Peking opera Lianpu inspired facial makeup with red eyeshadow, phoenix eyes, "
            "exaggerated theatrical character proportions, flowing hanfu water sleeves and silk ribbons, "
            "mythological wushu pose, blue-green Shanshui mountains, stylized Xiangyun swirling clouds, "
            "ancient pagoda with upturned eaves, gnarled pine trees, vermillion cinnabar red and azurite blue green palette, "
            "gold outline accents, aged xuan paper warm tint, vertical calligraphy and red seal chop optional, "
            "2D flat illustrative lighting, no 3D render, no photorealistic, no modern anime cel shading, "
            "highly detailed 2D illustration, cinematic composition, 4k"
        ),
        "video_prompt": (
            "Shanghai Animation Film Studio style 2D animation motion, Tian Shu Qi Tan aesthetic, "
            "flowing ribbon silk and water sleeve drift, gentle Xiangyun cloud parallax, "
            "Shanshui mountain mist scroll, flat illustrative lighting, mythological Chinese setting, "
            "smooth cel animation timing, decorative vermillion and azure palette, "
            "calligraphic line art consistency, no CGI, no fast shaky cam, ethereal heroic atmosphere"
        ),
        "references": [
            "大闹天宫 / Uproar in Heaven (1961/1964)",
            "哪吒闹海 / Nezha Conquers the Dragon King (1979)",
            "天书奇谭 / The Legend of Sealed Book (1983)",
            "九色鹿 / Nine-Colored Deer (1981)",
            "葫芦兄弟 / Calabash Brothers (1986)",
            "黑猫警长 / Black Cat Detective (1984)",
            "小蝌蚪找妈妈 (1960)",
            "牧笛 (1963)",
        ],
    },
    "american_comic_sketch": {
        "summary": '美式漫画草稿风：铅笔/墨水起稿感，交叉排线与动态透视。强调动作线与未完成能量，适合超级英雄分镜、概念迭代与粗稿storyboard。',
        "category": '二维美漫草稿',
        "artist_refs": 'Jack Kirby、Jim Lee 草稿、Marvel storyboard 团队',
        "era_texture": '1990s–2000s 美漫期刊制作流程',
        "line_control": '粗细墨水线，speed line，透视夸张',
        "lighting_color": '黑白为主，局部数码平色可选',
        "palette_strategy": '线稿黑白+单一强调色',
        "atmosphere": '力量、速度、未完成创作能量',
        "materials": '纸纹、墨水渗化、白高光留空',
        "quality": '打印线稿清晰，缩放仍见笔触',
        "taboos": '完整彩色渲染, 日系细线, 3D, 过度干净矢量',
        "characters_zh": '肌肉解剖夸张，披风与动态线交织。面部刀削，表情咆哮或 gritted teeth。',
        "characters_en": 'American comic sketch hero, ink crosshatching, dynamic foreshortening, muscular figure, cape motion lines, rough pencil underdrawing',
        "scenes_zh": '城市楼顶、爆炸背景线稿、分格透视速度感。',
        "scenes_en": 'comic book rooftop sketch, explosion background lines, forced perspective city, storyboard action layout',
        "colors": '墨黑, 纸白, 数码红点缀, 冷灰阴影',
        "image_prompt": 'American comic book sketch, ink crosshatching, dynamic action pose, muscular superhero, rough pencil lines, storyboard energy, black and white with red accent, Marvel style foreshortening, high contrast ink, 4k',
        "video_prompt": 'ink lines draw-on effect, comic speed lines pulse, camera punch-in on sketched hero, rough storyboard motion, dynamic comic energy',
        "references": [
        'Jack Kirby original art',
        'Jim Lee X-Men sketches',
        'Marvel house style boards',
        ],
    },
    "american_dark_illustration": {
        "summary": '美式黑暗插画：低键光、哥特纹理与叙事性阴影。借鉴封面艺术与独立漫画，心理恐怖与 noir 气质并存，适合悬疑、犯罪与 dark fantasy 封面。',
        "category": '二维黑暗插画',
        "artist_refs": 'Mike Mignola、Bernie Wrightson、Dave McKean',
        "era_texture": '1980s–2010s 黑暗漫画与封面黄金期',
        "line_control": 'heavy black shapes，silhouette 叙事',
        "lighting_color": '单源硬光，深黑占大面积',
        "palette_strategy": '黑+深红/深绿+肤色冷调',
        "atmosphere": '压迫、神秘、哥特',
        "materials": '刮刻纹理、水彩渍、旧纸',
        "quality": '印刷级暗部层次，不糊黑',
        "taboos": '高饱和卡通, 日系萌, 明亮日光, 3D',
        "characters_zh": '眼窝深影，轮廓如剪纸。长风衣、宽檐帽、伤痕与纹身暗示过往。',
        "characters_en": 'dark illustration figure, heavy shadow face, gothic silhouette, trench coat, noir mystery character, scratchy ink texture',
        "scenes_zh": '雨巷、废弃教堂、烛台与雾，前景栏杆框景。',
        "scenes_en": 'noir rainy alley, abandoned cathedral candles, fog streetlamp, gothic architecture shadows',
        "colors": '炭黑, 深红, 冷灰, 病绿, 蜡黄肤',
        "image_prompt": 'American dark illustration, heavy black shadows, gothic noir atmosphere, scratchy ink texture, single hard light source, mysterious figure in trench coat, deep crimson accents, horror comic cover quality, 4k',
        "video_prompt": 'slow candle flicker in dark corridor, fog drift across noir street, shadow swallow figure silhouette, gothic illustration atmosphere motion',
        "references": [
        'Hellboy comics (1994)',
        'Swamp Thing Bernie Wrightson',
        'Sandman covers Dave McKean',
        ],
    },
    "american_game_concept_art_2d": {
        "summary": '2D美式游戏概念艺术：关卡、角色与道具的探索性设计稿。线稿+快速色块，标注材质与比例，服务于 AAA 与 indie 前期视觉开发。',
        "category": '二维游戏概念艺术',
        "artist_refs": 'Naughty Dog visual dev、Blizzard concept、Sparth',
        "era_texture": '2010s 游戏预生产标准',
        "line_control": '干净结构线+松散笔触',
        "lighting_color": '快速明暗分区，主光方向标注',
        "palette_strategy": '3–5色探索，阵营色试稿',
        "atmosphere": '探索、工业流程、世界观搭建',
        "materials": 'annotated metal/leather/cloth',
        "quality": '可读 silhouette，适合内部评审',
        "taboos": '最终marketing polish, 错误比例无标注, 纯文字',
        "characters_zh": '多套装备变体并列，武器可拆展示。体态符合游戏camera视角。',
        "characters_en": 'game concept art character sheet, exploration sketches, armor variants, annotated proportions, action adventure hero design',
        "scenes_zh": '关卡鸟瞰、室内剖面、生物栖息地生态稿。',
        "scenes_en": 'game level concept vista, interior layout sketch, creature habitat design, annotated environment exploration',
        "colors": '土褐探索, 氧化蓝, 试稿橙, 结构灰',
        "image_prompt": '2D American game concept art, exploration sketches with color blocks, annotated armor design, epic environment vista, production art quality, loose brush with clear silhouette, adventure game aesthetic, 4k',
        "video_prompt": 'concept art layer build-up reveal, camera pan across level vista sketch, color block fade-in, game previsualization motion',
        "references": [
        'The Last of Us concept art',
        'Diablo IV environment concepts',
        'ArtStation Sparth works',
        ],
    },
    "american_retro_film_tv": {
        "summary": (
            "美式复古影视风格：以 1970s–1990s 北美电视 sitcom 与家庭录像带美学（Norman Lear sitcoms、"
            "MTV 90s、Kodachrome 家庭幻灯）为基准，呈现钨丝暖光、4:3 构图感、"
            "VHS 颗粒与木饰面客厅并存的「suburban nostalgia + analog TV」视觉语法。"
            "人物以大鬓角、复古发型、粗框眼镜与家居休闲服为核心；"
            "场景强调客厅、厨房、木质楼梯、墙上全家福。"
            "整体为 live-action analog TV/film emulation，偏暖棕+牛油果绿 LUT，"
            "绝不做现代 LED 冷白、4K 过度锐或赛博霓虹主导。"
            "适合美式怀旧家庭剧、复古广告、80/90 年代回忆 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 美式复古电视影视（American Retro Film TV Live-Action）",
        "artist_refs": (
            "导演/节目：Norman Lear sitcoms、《All in the Family》；"
            "美学：MTV 90s color、Kodachrome family slides；"
            "参照：《Stranger Things》80s TV homage、家庭录像带 VHS；"
            "摄影：演播室平光+钨丝暖、4:3 safe framing feel。"
        ),
        "era_texture": (
            "1970s–1990s 北美电视与家庭录像；"
            "VHS/16mm grain 可控，轻微色散；"
            "聚酯纤维、木饰面、CRT 反光 texture；"
            "digital 须 emulate analog warmth 非 clean modern HDR。"
        ),
        "line_control": (
            "构图自然 sitcom 感，无风格化描边；"
            "4:3 feel 或宽银幕但保留 TV set blocking；"
            "客厅 master shot + two-shot dialogue；"
            "movement：gentle push-in sitcom camera、CRT flicker subtle。"
        ),
        "lighting_color": (
            "主光：钨丝暖光+演播室平光；"
            "室内：table lamp warm + overhead soft；"
            "CRT 屏 glow 作环境 accent；"
            "禁忌：modern LED cold white、cyber neon、flat office fluorescent。"
        ),
        "palette_strategy": (
            "主调：钨丝暖、牛油果绿、橙棕、米黄、VHS 噪点灰；"
            "warm brown + wood paneling 锚点；"
            "肤色 warm nostalgic 非 glamour peach；"
            "flashback 可加 Kodachrome saturation boost。"
        ),
        "atmosphere": (
            "怀旧、家庭、喜剧或轻 drama；"
            "suburban comfort 与 CRT 嗡鸣视觉 companion；"
            "shag carpet、wood panel 是核心符号；"
            "非 epic blockbuster 或 horror dread。"
        ),
        "materials": (
            "聚酯纤维沙发、木饰面墙、shag carpet、"
            "CRT television、Formica 厨房台面、全家福相框；"
            "忌 glass skyscraper、neon sign、synthetic sportswear logo。"
        ),
        "quality": (
            "VHS/16mm grain 可控还原级；"
            "fabric pattern 与 wood grain readable；"
            "4K with film grain，thumbnail 可辨 70s living room mood。"
        ),
        "taboos": (
            "现代 LED 冷白、4K 过度锐、赛博霓虹、"
            "宽银幕变形 epic only、horror gore、anime。"
        ),
        "characters_zh": (
            "大鬓角、复古发型、粗框眼镜；"
            "休闲家居服、高领毛衣、宽领衬衫；"
            "客厅 sitcom 互动姿态；"
            "表情喜剧或轻 drama 自然。"
        ),
        "characters_en": (
            "retro American TV character 1970s hairstyle, turtleneck wide collar, "
            "living room sitcom pose warm nostalgic appearance, "
            "suburban family room presence, VHS color grade portrait"
        ),
        "scenes_zh": (
            "复古美式客厅、木饰面墙厨房、"
            "shag carpet 楼梯、CRT 电视 glow、"
            "郊区 suburban kitchen set。"
        ),
        "scenes_en": (
            "retro American living room wood panel walls, shag carpet suburban interior, "
            "CRT television glow warm tungsten, nostalgic kitchen Formica set, "
            "family photo wall 1970s suburban home"
        ),
        "colors": "钨丝暖, 牛油果绿, 橙棕, 米黄, VHS噪点灰, 木棕, CRT蓝灰",
        "image_prompt": (
            "American retro TV aesthetic 1970s living room, warm tungsten lighting, "
            "VHS grain texture wood panel walls, sitcom composition nostalgic suburban interior, "
            "soft analog colors 4:3 feel, Kodachrome warmth, 4k with film grain"
        ),
        "video_prompt": (
            "gentle CRT flicker subtle, sitcom camera push-in warm, "
            "warm tungsten light steady living room, VHS tracking subtle shake nostalgic, "
            "family room motion suburban comfort"
        ),
        "references": [
            "All in the Family (1971)",
            "Stranger Things 80s TV homage",
            "Kodachrome family slides",
        ],
    },
    "american_retro_hollywood": {
        "summary": (
            "美式复古好莱坞风格：以 1930s–1960s 好莱坞黄金年代（Technicolor 音乐剧、黑色电影、"
            "明星制度与影棚体系）摄影美学为基准，呈现高饱和原色、蝴蝶光/轮廓光 glamour 肖像、"
            "对称构图与人工完美布景并存的「studio dream factory」视觉语法。"
            "人物以卷发明星、粗眉红唇、礼服手套与经典站姿为核心；场景强调假景山、"
            "百老汇式舞台、片场 lot 与 velvet 幕布。整体为 live-action 电影级写实摄影，"
            "偏 Technicolor emulation + soft peach skin glow LUT，绝不做 handheld gritty indie、"
            "desaturated 北欧或现代街头潮牌主导。"
            "适合复古好莱坞、音乐剧风、明星传记、美式怀旧广告向 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 美式复古好莱坞黄金年代（American Retro Hollywood Golden Age Live-Action）",
        "artist_refs": (
            "摄影与美术参照：George Hurrell 明星肖像、MGM musicals、《Singin' in the Rain》"
            "《Rear Window》《Gentlemen Prefer Blondes》组；"
            "导演：Vincente Minnelli、Gene Kelly、Douglas Sirk、Billy Wilder；"
            "美学：butterfly key、rim glamour、three-point studio hard light、"
            "painted cyclorama backdrop、symmetrical star portrait framing。"
        ),
        "era_texture": (
            "1930s–1960s Technicolor 与 studio system 质感，35mm 胶片颗粒 fine、"
            "highlight soft rolloff、肤色 peach glow 无现代 HDR 硬边；"
            "室内影棚光比可控，外景 lot 仍带 artificial perfection；"
            "可选 subtle gate weave 与 dye transfer saturation（非 digital oversharpen）；"
            "digital capture 须 emulate Technicolor：rich primaries、cream highlight、velvet shadow。"
        ),
        "line_control": (
            "构图以经典三分法、对称与中心明星肖像为主；"
            "musical 场景用 wide master + low angle hero；dialogue 用 medium two-shot 舞台感；"
            "景深中等，背景假景保持 readable painted texture；"
            "少用手持 chaos，movement 靠 choreographed blocking 与 spotlight follow。"
        ),
        "lighting_color": (
            "主光：butterfly / paramount light 于面部，颧骨高光与眼下阴影可控；"
            "轮廓光：hard rim 分离发丝与礼服缎面；"
            "musical：spotlight pool + colored gel wash；"
            "禁忌：flat LED office、naturalistic overcast only、neon cyber、gritty sodium only。"
        ),
        "palette_strategy": (
            "主调：Technicolor 红、钴蓝、金黄、桃肤、深影褐；"
            "礼服与布景可用互补色 clash（红裙+蓝幕）；"
            "肤色统一 warm peach，唇高饱和红；"
            "叙事：悲剧场景可降饱和但保留 star lighting 轮廓，禁完全 desaturated indie grey。"
        ),
        "atmosphere": (
            "glamour、dream factory、artificial perfection 与 backstage longing 并存；"
            "缎面 shimmer、珍珠项链、舞台尘土光束、curtain reveal；"
            "明星微笑与 off-camera spotlight 是核心情绪符号；"
            "浪漫夸张但非 horror uncanny（除非黑色电影子类型单独标注）。"
        ),
        "materials": (
            "缎面礼服、亮片、人造珍珠、漆皮高跟鞋、假景帆布山、"
            "丝绒幕布、chrome microphone、studio cyclorama；"
            "毛发卷烫光泽、粉底 matte powder 质感；"
            "忌 modern athleisure fabric、dirty grit、rust industrial。"
        ),
        "quality": (
            "院线复古胶片还原级：4K clean 但保留 film grain 与 dye saturation；"
            "fabric fold 与 jewelry specular readable；"
            "thumbnail 可辨 star silhouette 与 Technicolor 色块。"
        ),
        "taboos": (
            "handheld gritty indie、desaturated nordic、modern streetwear dominant、"
            "cyber neon、horror gore、documentary shaky、flat smartphone HDR。"
        ),
        "characters_zh": (
            "好莱坞黄金年代明星：卷发波浪、细眉、红唇、珍珠项链与手套；"
            "礼服鱼尾/蓬裙、燕尾服、舞台妆面哑光；"
            "站姿经典 portrait pose，眼神 off-camera spotlight；"
            "群舞配角 uniform costume color block。"
        ),
        "characters_en": (
            "Hollywood golden age movie star, Technicolor glamour portrait, "
            "vintage curled hairstyle, red lipstick, pearl necklace and gloves, "
            "elegant gown or tuxedo, butterfly studio lighting, classic star pose, "
            "painted backdrop soundstage, 1950s cinema presence"
        ),
        "scenes_zh": (
            "MGM 式影棚阶梯、假山假水 cyclorama、spotlight 舞台、"
            "片场 lot 外景、红色丝绒幕布、化妆镜灯泡墙、"
            "musical 群舞几何构图场景。"
        ),
        "scenes_en": (
            "Hollywood soundstage musical set, painted backdrop mountains and sky, "
            "spotlight stage pool, vintage cinema studio lot exterior, "
            "red velvet curtain reveal, dressing room mirror bulbs, "
            "Technicolor choreographed ensemble wide shot"
        ),
        "colors": "Technicolor红, 钴蓝, 金黄, 肤peach, 深影褐, 丝绒酒红, 舞台琥珀",
        "image_prompt": (
            "American retro Hollywood golden age Technicolor cinematography, "
            "glamour studio portrait butterfly lighting, saturated primary colors red blue gold, "
            "vintage movie star in elegant gown, painted soundstage cyclorama backdrop, "
            "pearl necklace red lipstick curled hair, classic symmetrical cinema composition, "
            "fine 35mm film grain dye transfer saturation, 4k"
        ),
        "video_prompt": (
            "spotlight sweep across musical stage, Technicolor satin dress shimmer slow turn, "
            "velvet curtain pull reveal, classic Hollywood studio camera dolly, "
            "glamour portrait light shift, choreographed ensemble step in sync"
        ),
        "references": [
            "Singin' in the Rain (1952)",
            "Rear Window (1954)",
            "Gentlemen Prefer Blondes (1953)",
            "George Hurrell portrait archive",
        ],
    },
    "american_retro_weird": {
        "summary": (
            "美式复古怪异影视风格：以 David Lynch 郊区暗涌美学（《双峰》《蓝丝绒》）"
            "与 Rod Serling《 Twilight Zone》为基准，呈现白天正常表面下隐藏 uncanny、"
            "复古美国小镇+超自然符号并存的「mundane framing + wrong content」视觉语法。"
            "人物以微笑僵硬店员、少年侦探、神秘日志与港式 diner 制服为核心；"
            "场景强调双峰式 diner、红色窗帘房间、锯木厂雾、孤独公路牌。"
            "整体为 live-action 35mm with subtle wrongness，偏森林绿+樱桃红 LUT，"
            "绝不做纯恐怖 gore、赛博或明亮商业广告风主导。"
            "适合美式怪诞悬疑、小镇超自然、Lynchian 氛围 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 美式复古怪诞（American Retro Weird Lynchian Live-Action）",
        "artist_refs": (
            "导演：David Lynch、《双峰》《蓝丝绒》；"
            "Rod Serling《The Twilight Zone》；"
            "美学：mundane daylight normalcy、uncanny suburban、"
            "red curtain room、diner chrome、Pacific Northwest fog；"
            "摄影：1990s small town VHS color grade。"
        ),
        "era_texture": (
            "1980s–1990s 美国小镇录像感 35mm；"
            "subtle wrongness 非 overt horror gore；"
            "松木、chrome diner、红色窗帘 fabric texture；"
            "digital 须 emulate VHS/35mm 非 clean commercial polish。"
        ),
        "line_control": (
            "构图 mundane framing 异常内容；"
            "diner wide static、highway lonely sign；"
            "red curtain room centered symmetric uncanny；"
            "movement：slow unsettling pan、fog creep 缓慢。"
        ),
        "lighting_color": (
            "主光：日光平+突然硬闪；"
            "室内：diner fluorescent + red curtain warm；"
            "雾林：diffuse grey-green overcast；"
            "禁忌：bright commercial ad、cyber neon、horror sick green dominant。"
        ),
        "palette_strategy": (
            "主调：樱桃红、森林绿、松木棕、雾灰、霓虹咖啡；"
            "log cabin 棕与 forest green 锚点；"
            "肤色 natural 但 smile uncanny；"
            "night 场景可加 neon coffee sign accent。"
        ),
        "atmosphere": (
            "uncanny、悬疑、黑色幽默、郊区暗涌；"
            "白天正常表面下隐藏威胁；"
            "red curtain、diner hum、fog forest 是核心符号；"
            "非 jump scare horror franchise 主导。"
        ),
        "materials": (
            "diner chrome、松木、红色窗帘、"
            "公路金属牌、锯木厂 timber、小镇 brick storefront；"
            "忌 glass futurism、palace silk、anime cel。"
        ),
        "quality": (
            "35mm subtle wrongness 院线级；"
            "fog diffusion 与 chrome reflection readable；"
            "4K with grain，thumbnail 可辨 Lynchian diner 与 red curtain。"
        ),
        "taboos": (
            "纯恐怖 gore focus、赛博 neon、明亮商业广告风、"
            "epic blockbuster、anime cartoon。"
        ),
        "characters_zh": (
            "微笑僵硬的店员、少年侦探、神秘日志；"
            "复古美国发型与校服/ diner uniform；"
            "表情 polite uncanny smile；"
            "姿态 mundane 但眼神空洞。"
        ),
        "characters_en": (
            "retro weird American town character uncanny polite smile, "
            "1990s small town fashion Lynchian mystery figure, "
            "diner uniform chrome counter, Twin Peaks inspired presence, "
            "suburban uncanny daylight portrait"
        ),
        "scenes_zh": (
            "双峰式 diner 霓虹、红色窗帘房间、"
            "太平洋西北雾林、孤独公路牌、"
            "锯木厂雾气小镇。"
        ),
        "scenes_en": (
            "Twin Peaks style diner neon interior, red curtain room symmetric uncanny, "
            "Pacific Northwest fog forest highway, lonely highway sign small town, "
            "sawmill mist Lynchian suburban atmosphere"
        ),
        "colors": "樱桃红, 森林绿, 松木棕, 雾灰, 霓虹咖啡,  diner铬银",
        "image_prompt": (
            "American retro weird aesthetic Lynchian small town diner, "
            "uncanny daylight normalcy red curtain interior, Pacific Northwest fog, "
            "1990s VHS color grade mysterious suburban atmosphere, cinematic 35mm, 4k"
        ),
        "video_prompt": (
            "slow unsettling diner pan chrome counter, red curtain sway subtle, "
            "fog creep over highway lonely, uncanny small town stillness hold, "
            "retro weird suspense motion Lynchian"
        ),
        "references": [
            "Twin Peaks (1990)",
            "Blue Velvet (1986)",
            "The Twilight Zone (1959)",
        ],
    },
    "ancient_romance_soft_glow": {
        "summary": (
            "古偶唯美柔光风格：以 2010s–2020s 国产古装偶像剧（《步步惊心》《花千骨》《陈情令》《三生三世十里桃花》）"
            "摄影美学为基准，呈现柔焦梦幻、暖金轮廓光、低对比肤色与 pastel 服色并存的「仙侠/宫廷言情」视觉语法。"
            "人物以精致古装妆容、流苏步摇、纱幔罗裙与含情脉脉/泪光微闪表情为核心；场景强调桃花林、月下楼阁、"
            "纱帐寝宫与落樱庭院。整体为 live-action 电影级写实摄影，偏 soft glow + golden rim 柔光 LUT，"
            "背景 heavy bokeh，绝不做硬核战争 dirt、历史纪录片写实或日系动漫大眼化。"
            "适合古偶爱情、仙侠言情、宫斗甜宠向 AIGC 短剧的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 国产古偶言情柔光（Ancient Chinese Romance Soft Glow Live-Action）",
        "artist_refs": (
            "摄影与美术参照：《步步惊心》《花千骨》《陈情令》《三生三世十里桃花》《与君歌》《长月烬明》组；"
            "横店/象山/天都影视城古装外景；"
            "摄影指导式美学：柔光箱 + 逆光金边 rim、低对比 fill、浅景深 portrait；"
            "妆造：汉服/仙侠服、眉心妆、花钿、流苏耳坠、步摇、纱幔头饰。"
        ),
        "era_texture": (
            "2010s–2020s 国产古偶黄金配方，4K 干净肤质 + 柔焦 dreamy diffusion（非糊片）；"
            "可带轻微 lens bloom / halation 于高光发梢与金属饰件；"
            "室内烛火/月光场景带 soft haze，外景桃花/落樱带 airborne petal particles；"
            "色彩经 warm pastel grade，肤质 porcelain smooth，避免 gritty 纪录片颗粒。"
        ),
        "line_control": (
            "构图以人物居中或三分法、浅景深 isolating subject 为主；"
            "情侣/师徒双人对视常用 over-shoulder 或 profile silhouette against moon/sky；"
            "群像站位 romantic hierarchy（主角前景 sharp、背景 soft bokeh）；"
            "少用手持 chaos，多用 slow push-in / gentle arc 营造情感流动；"
            "可偶用 frame within frame（窗棂/纱帘/月洞门）但不强调对称压迫（区别于宫斗冷峻）。"
        ),
        "lighting_color": (
            "主光：大型 soft source（柔光箱/反射板）正面或 45°，肤质均匀透亮；"
            "轮廓：逆光/侧逆光 warm gold rim（2700K–3500K）勾发梢、肩线与纱幔边缘；"
            "辅光：充足 fill 减少眼窝深影，保留 romantic softness；"
            "点缀：烛火、孔明灯、月光冷蓝与室内暖金对位；"
            "禁忌：hard noir 半脸阴影、flat fluorescent、赛博霓虹、过度 HDR。"
        ),
        "palette_strategy": (
            "主调：柔粉、暖金、浅青、玉白、桃红 pastel；"
            "服色：淡粉/浅蓝/月白/藕荷，反派或魔族可用紫/玄青作对照；"
            "肤色：偏暖 porcelain，腮红轻扫苹果肌，唇色 coral/豆沙；"
            "叙事用色：甜蜜场景提 saturation 与 golden hour；虐恋/离别降饱和加冷蓝月光。"
        ),
        "atmosphere": (
            "浪漫、梦幻、情感特写、仙侠诗意与 tender heartache 并存；"
            "花瓣飘落、纱幔轻动、发丝随风、水面月影涟漪（视觉可表现为 slow motion petal drift）；"
            "对话场景常用「近景泪光 + 远景虚化花海/楼阁」对照，强调 emotional isolation in beauty；"
            "战斗/法术场面仍保持 drama 级柔光美学，光效偏 particle glow 非硬核 VFX。"
        ),
        "materials": (
            "服饰：纱、罗、绸、轻甲仙侠装、广袖、飘带、腰封、玉佩、剑穗；"
            "头饰：步摇、流苏、花冠、发簪、白纱覆面；"
            "道具：团扇、油纸伞、古琴、酒壶、信笺、灵珠、法器（发光柔和）；"
            "环境：桃花、樱花、荷叶、竹林、瀑布、云海、琉璃瓦楼阁；"
            "质感：丝绸 sheen、金属饰件 soft specular、花瓣 translucency。"
        ),
        "quality": (
            "4K drama cinematography，肤质细腻、发丝与织物纹理清晰；"
            "适合 9:16 竖版角色卡与 16:9 场景宽镜；"
            "景深：浅景深 portrait（f/1.4–2.8 feel）/ 背景 heavy bokeh；"
            "live-action realistic romantic，非插画、非 3D CG 仙侠。"
        ),
        "taboos": (
            "现代服装配饰、运动鞋、眼镜、手机、西化宫廷；"
            "硬核战争 mud/blood grit、历史纪录片 dirt、纪实 handheld chaos；"
            "日系 anime 大眼、韩漫 glass skin 过度、网红美颜滤镜；"
            "赛博霓虹、noir 冷调主导、horror green cast；"
            "watermark、字幕条、多格漫画分镜（单图角色卡时）。"
        ),
        "characters_zh": (
            "【面部】柳叶眉、杏眼或桃花眼，眼线柔和，眉心妆/花钿可选；"
            "唇色 coral/豆沙，腮红轻透；表情：含情脉脉、侧目娇羞、泪光盈盈、"
            "微蹙浅笑——「虐甜」并存。"
            "【发型】高髻、半披发、飞仙髻；发丝根根分明，逆光时呈 golden halo。"
            "【服饰】仙侠白/淡粉/浅蓝广袖，或宫廷华服金线刺绣；"
            "飘带、披帛、腰封、玉佩、剑穗随动；"
            "手持团扇、油纸伞、法器、信笺。"
            "【体态】轻盈步态、回眸、倚栏、抚琴、御剑悬浮（法效 soft glow）；"
            "双人：对视、牵手、背对背、公主抱。"
            "【气质范例】若曦——隐忍深情；花千骨——纯真与劫；"
            "魏无羡——洒脱俊逸；白浅——冷艳仙气。"
        ),
        "characters_en": (
            "ancient Chinese romance soft glow live-action character, elegant hanfu or xianxia costume, "
            "delicate makeup with forehead ornament, golden backlight rim on hair edges, "
            "dreamy romantic expression with glistening eyes, flowing silk ribbons and sheer sleeves, "
            "soft focus porcelain skin, pastel wardrobe styling, cherry blossom petal atmosphere, "
            "shallow depth of field portrait, warm pastel cinematic color grade, "
            "Chinese costume drama aesthetic, no anime style, no gritty war dirt, highly detailed 4k"
        ),
        "scenes_zh": (
            "【典型环境】桃花林、落樱庭院、月下楼阁、纱帐寝宫、竹林小径、"
            "云海仙山、瀑布旁、荷花池、宫墙外花径、孔明灯夜空。"
            "【构图】人物前景 sharp + 背景 heavy bokeh；"
            "或 couple silhouette against full moon / sunset golden hour。"
            "【光影】逆光金边、柔光箱正面、烛火 warm accent、月光 cool fill；"
            "花瓣/纱幔/发丝在 rim light 下 translucent。"
            "【季节】春樱、夏荷、秋夕、冬雪（雪场景仍保持 soft glow 非 harsh cold）；"
            "避免 overcast flat documentary 感。"
        ),
        "scenes_en": (
            "cherry blossom ancient garden soft glow, moonlit Chinese pavilion romantic scene, "
            "silk curtain bedroom dreamy bokeh, falling petals slow motion atmosphere, "
            "xianxia mountain cloud sea golden hour, lotus pond misty morning, "
            "warm pastel cinematic color grade, shallow depth of field, "
            "Chinese costume romance drama cinematography, live-action ethereal palace courtyard, 4k"
        ),
        "colors": (
            "主色：柔粉、暖金、浅青、玉白、桃红、藕荷；"
            "点缀：珊瑚唇、金饰、淡紫（魔族/反派）、月白月光；"
            "肤色：暖 porcelain，腮红轻透；"
            "叙事：甜蜜场景 golden hour 提暖，虐恋场景降饱和加冷蓝月光"
        ),
        "image_prompt": (
            "ancient Chinese romance soft glow live-action cinematography, dreamy bokeh and golden backlight rim, "
            "elegant hanfu or xianxia lovers in cherry blossom garden, delicate makeup and flowing silk ribbons, "
            "soft focus porcelain skin, pastel warm color grading, moonlit pavilion romantic atmosphere, "
            "falling petals and sheer curtain diffusion, shallow depth of field portrait, "
            "Chinese costume drama aesthetic, Empresses and xianxia romance visual style, "
            "no gritty war, no anime, no harsh noir lighting, highly detailed 4k vertical 9:16"
        ),
        "video_prompt": (
            "slow romantic push-in through cherry blossom petals, silk ribbon and hair flutter in golden rim light, "
            "soft glow lens flare gentle drift, moonlit pavilion couple silhouette, "
            "dreamy ancient romance atmosphere motion, pastel warm grade consistent, "
            "no shaky action cam, tender emotional pacing"
        ),
        "references": [
            "步步惊心 (2011)",
            "花千骨 (2015)",
            "陈情令 (2019)",
            "三生三世十里桃花 (2017)",
        ],
    },
    "anime_3render2": {
        "summary": '三渲二动漫风格：3D模型+二维赛璐璐渲染，Arcane/原神过场式平面色块与手绘感边缘。角色旋转仍保持 anime 读形。',
        "category": '三渲二/赛璐璐3D',
        "artist_refs": 'Arcane team、miHoYo cinematics、Guilty Gear Xrd',
        "era_texture": '2018–2024 三渲二工业化',
        "line_control": 'cel edge 或 texture 描边',
        "lighting_color": '分层 cel shadow，非PBR',
        "palette_strategy": 'anime固有色+环境互补',
        "atmosphere": '热血、精致、番剧品质',
        "materials": 'flat shader zones，hair clump anime',
        "quality": '番剧cut 级，无3D塑料感',
        "taboos": '纯写实PBR, 美漫, 低帧interlace',
        "characters_zh": '大眼 anime 比例，发色分区清晰。战斗pose带特效线。',
        "characters_en": 'anime 3D cel shaded character, large expressive anime eyes, stylized hair clumps, dynamic battle pose, toon shader lighting',
        "scenes_zh": '幻想都市、学院、异空间，背景 painterly。',
        "scenes_en": 'anime fantasy cityscape, cel shaded environment, painterly sky gradient, JRPG inspired landscape',
        "colors": '番剧蓝, 发色饱和, 肤色 peach, 阴影紫',
        "image_prompt": 'anime 3D cel shaded render, toon shader character, large expressive eyes, painterly background, Arcane inspired aesthetic, vibrant anime colors, dynamic pose, no photorealistic skin, cinematic anime composition, 4k',
        "video_prompt": 'cel shaded character action swipe, anime VFX streak lines, camera arc around 3D anime hero, toon lighting consistent, battle motion blur stylized',
        "references": [
        'Arcane (2021)',
        '原神过场动画',
        'Guilty Gear Strive (2021)',
        ],
    },
    "anime_concept_art_2d": {
        "summary": '2D日系动画概念设定：设定集式 turnaround、表情差分与场景气氛稿。线稿干净，色块探索世界观统一性。',
        "category": '二维日系概念设定',
        "artist_refs": '新海诚美术集、吉卜力设定、Aniplex visual design',
        "era_texture": '当代TV/feature preproduction',
        "line_control": '细线结构+水彩/数码铺色',
        "lighting_color": '气氛光速写，时间带标注',
        "palette_strategy": '主色脚本3色+中性灰',
        "atmosphere": '诗意、青春、世界观',
        "materials": '标注材质：棉、毛、金属',
        "quality": '设定集印刷级',
        "taboos": '3D截图, 欧美厚涂, 完成动画帧',
        "characters_zh": '校服/和服/奇幻服多方案，发型色板。表情 sheet 6–8种。',
        "characters_en": 'anime concept art character sheet, expression variants, school uniform design, clean lineart, color exploration thumbnails',
        "scenes_zh": '车站、屋顶、异世界门，带时间天气标注。',
        "scenes_en": 'anime concept environment, train station mood sketch, rooftop sunset study, fantasy gate design exploration',
        "colors": '探索蓝, 夕橙, 中性灰, 草绿试稿',
        "image_prompt": '2D anime concept art, clean character turnaround, environment mood painting, soft atmospheric lighting study, production design sheet, Japanese animation aesthetic, delicate linework, color script exploration, 4k',
        "video_prompt": 'concept sheet layer reveal, time-of-day color shift on environment study, gentle pan across anime design boards, preproduction art motion',
        "references": [
        'Your Name art book',
        'Ghibli Layout Collection',
        'Fate series material books',
        ],
    },
    "bw_2d_comic_animation": {
        "summary": '黑白二维漫画动画：高对比墨线与网点 halftone，像活页漫画动起来。适合 noir、独立漫画与实验动画。',
        "category": '二维黑白漫画动画',
        "artist_refs": 'Sin City、Persepolis、黑白日本独立动画',
        "era_texture": '2000s 独立漫画动画',
        "line_control": '纯黑fill与留白对抗',
        "lighting_color": '无灰度渐变或 limited halftone',
        "palette_strategy": '严格黑白，偶单红色',
        "atmosphere": 'noir、 stark、 dramatic',
        "materials": '网点纸、刮刀白',
        "quality": '线条动画稳定，无灰雾',
        "taboos": '全彩, 3D, 柔边喷枪',
        "characters_zh": '剪影式面部，风衣与礼帽。动作带漫画音效字空间。',
        "characters_en": 'black white comic animated character, high contrast ink silhouette, noir detective coat, halftone shadow dots, stark graphic pose',
        "scenes_zh": '雨夜街灯、监狱栏影、极简室内。',
        "scenes_en": 'noir black white city rain, prison bar shadows, minimalist comic panel background, high contrast urban night',
        "colors": '纯黑, 纯白, 灰网点, 单红点缀',
        "image_prompt": 'black and white 2D comic animation style, high contrast ink, halftone dot shadows, noir urban scene, stark graphic silhouettes, Sin City inspired aesthetic, bold black fills, comic panel composition, 4k',
        "video_prompt": 'comic panel transition wipe, halftone flicker animation, noir rain streaks, high contrast ink motion, black white comic timing',
        "references": [
        'Sin City (2005)',
        'Persepolis (2007)',
        'Tekkonkinkreet (2006)',
        ],
    },
    "bw_ink_wash": {
        "summary": '水墨黑白美学：宣纸渗化、留白写意、焦浓重淡清五墨。人物山水一体，东方哲学气质，非彩色国画数字化。',
        "category": '水墨/黑白写意',
        "artist_refs": '齐白石、李可染、徐冰、水墨动画传统',
        "era_texture": '传统水墨当代数字诠释',
        "line_control": '一笔见骨，无重复描线',
        "lighting_color": '无光源，靠墨阶',
        "palette_strategy": '纯墨+纸白，极少量淡彩可省',
        "atmosphere": '空灵、禅意、诗性',
        "materials": '生宣渗化、飞白、枯笔',
        "quality": '墨阶丰富不脏',
        "taboos": '彩色动漫, 3D体积, 西方油画笔触',
        "characters_zh": '简笔人物数笔传神，衣纹一笔而下。与梅竹石同框。',
        "characters_en": 'ink wash figure, minimal brushstrokes, flowing robe suggested lines, xieyi Chinese painting style, empty space composition',
        "scenes_zh": '远山淡墨、瀑布留白、孤舟江面。',
        "scenes_en": 'ink wash mountains mist, empty river with lone boat, bamboo grove monochrome, traditional scroll landscape',
        "colors": '焦墨, 浓墨, 淡墨, 清墨, 纸白',
        "image_prompt": 'black and white Chinese ink wash painting, xieyi expressive brushwork, rice paper texture bleed, misty mountains minimal strokes, poetic empty space, traditional scroll composition, no color, artistic monochrome, 4k',
        "video_prompt": 'ink brush stroke reveal animation, mist drifting across wash mountains, gentle scroll unroll motion, monochrome ink flow, meditative pace',
        "references": [
        '小蝌蚪找妈妈 (1960)',
        '山水情 (1988)',
        '齐白石虾群',
        ],
    },
    "children_crayon_handdrawn": {
        "summary": '儿童蜡笔手绘风：蜡笔颗粒、色彩出界、比例天真。像幼儿画作但构图完整，适合教育、亲子与温暖叙事。',
        "category": '儿童手绘/蜡笔',
        "artist_refs": "儿童绘本蜡笔风、Blue's Clues 早期手工感",
        "era_texture": '幼儿园/家庭手工',
        "line_control": '粗蜡笔线，不闭合也可',
        "lighting_color": '无光影，纯平面',
        "palette_strategy": '原色蜡笔直接叠涂',
        "atmosphere": '天真、温暖、安全',
        "materials": '蜡笔 grain、彩纸底',
        "quality": '边缘参差有手工感',
        "taboos": '写实, 恐怖, 精细数码, 3D',
        "characters_zh": '太阳脸微笑，手脚火柴棒。动物朋友圆润色块。',
        "characters_en": 'child crayon drawing character, wobbly thick lines, stick figure limbs, smiling sun face, naive cute proportions',
        "scenes_zh": '房子三角屋顶、太阳角、绿线草地。',
        "scenes_en": 'crayon drawn house and sun, wobbly green grass lines, hand drawn rainbow, kindergarten art paper background',
        "colors": '蜡笔红, 蜡笔蓝, 蜡笔黄, 蜡笔绿, 粗黑线',
        "image_prompt": 'children crayon hand drawn style, wobbly thick wax crayon lines, naive colorful shapes, paper texture grain, stick figure family, kindergarten art aesthetic, bright primary crayon colors, charming imperfect drawing, 4k',
        "video_prompt": 'crayon line draw-on animation, wobbly bounce motion, paper texture static, naive childlike energy, simple colorful scene movement',
        "references": [
        '儿童绘本蜡笔插画',
        'Harold and the Purple Crayon',
        '幼儿园墙绘',
        ],
    },
    "clay_animation": {
        "summary": '粘土定格动画：Fingerprint 与 Laika 式可塑粘土，可见指纹与微抖帧。温暖 tactile 质感，适合童话与幽默小品。',
        "category": '粘土定格动画',
        "artist_refs": 'Aardman、Laika Coraline、Claymation TV',
        "era_texture": '经典 stop-motion clay',
        "line_control": '圆滚形体，无硬边',
        "lighting_color": '小型 set 灯光，真实阴影',
        "palette_strategy": '粘土原色+手工上色',
        "atmosphere": '手工、幽默、 tactile',
        "materials": 'Plasticine、可见指纹、 armature',
        "quality": '帧间微动authentic',
        "taboos": '平滑3D, 2D, 无指纹perfect CG',
        "characters_zh": '圆眼、大鼻、可替换嘴型。身体略沉，重心明显。',
        "characters_en": 'clay animation character, plasticine texture, visible fingerprints, round expressive clay face, stop motion puppet body',
        "scenes_zh": '小型手工布景，假草与纸板箱。',
        "scenes_en": 'miniature clay animation set, handmade props, tabletop stop motion stage, tactile craft environment',
        "colors": '粘土肤, 原色红蓝, 手工绿, 暖台灯光',
        "image_prompt": 'clay animation stop motion style, plasticine characters with fingerprints, handmade miniature set, warm studio lighting, tactile clay texture, Aardman inspired design, visible frame-by-frame charm, 4k',
        "video_prompt": 'stop motion clay walk cycle, subtle frame jitter, mouth replacement timing, handmade set parallax, tactile clay motion',
        "references": [
        'Wallace and Gromit',
        'Chicken Run (2000)',
        'Coraline (2009)',
        ],
    },
    "cn_90s_realistic_film": {
        "summary": (
            "90年代中国写实电影风格：以 1990s 中国独立/现实主义电影（贾樟柯《小武》《站台》、"
            "王小帅《十七岁的单车》、赵刚摄影群体、以及县城题材纪录片美学）为基准，"
            "呈现灰绿褪色调、阴天自然光、长镜头气质与无美颜真实肤质并存的「county-town era + "
            "documentary humanism」视觉语法。"
            "人物以工人、青年小贩、下岗族与普通脸为核心；场景强调县城街道、录像厅、"
            "工厂大门、绿皮火车与灰色天空。整体为 live-action 16mm/35mm 电影摄影，"
            "偏 grey-green desaturated LUT，绝不做古偶柔光、HDR 锐化、赛博霓虹或都市精致广告感。"
            "适合年代怀旧、县城叙事、现实主义短剧 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 90年代中国写实电影（Chinese 90s Realistic Film Live-Action）",
        "artist_refs": (
            "导演/摄影参照：贾樟柯、王小帅、娄烨早期、赵刚；"
            "作品：《小武》《站台》《三峡好人》《十七岁的单车》《苏州河》；"
            "美学：overcast natural light、long take static or slow pan、"
            "wide shot small figure in urban decay、16mm/35mm grain、unretouched faces。"
        ),
        "era_texture": (
            "1990s 中国县城与国企转型期质感，16mm 或 35mm visible grain（非 clean digital）；"
            "阴天散射光主导，钨灯室内偏黄绿；"
            "建筑水泥灰、褪色招牌、自行车与 VCD 店霓虹作为时代符号；"
            "digital 须 emulate film：soft highlight、muted saturation、no beauty filter。"
        ),
        "line_control": (
            "构图 documentary framing：eye level、wide establishing + intimate close；"
            "长镜头留白，人物可偏离中心；"
            "少 dramatic dutch angle，emotion 靠 stillness 与环境音空间；"
            "街道纵深用 telephoto compression 或 flat frontal walk toward camera。"
        ),
        "lighting_color": (
            "主光：阴天顶光+环境 bounce，无 glamour key；"
            "室内：钨丝灯/日光灯混合偏绿，录像厅屏幕蓝光；"
            "夜景：sparse sodium 与廉价 neon，不高饱和；"
            "禁忌：golden hour hero only、studio butterfly、cyber teal-orange。"
        ),
        "palette_strategy": (
            "主调：灰绿、水泥灰、褪色红、阴天天空灰蓝、钨灯暖黄；"
            "肤色自然偏黄灰，无 porcelain smooth；"
            "偶尔 VCD 店/招牌小面积饱和色作时代锚点；"
            "全片避免 high-key pastel 与 commercial beauty grade。"
        ),
        "atmosphere": (
            "克制、时代乡愁、普通人尊严与失落并存；"
            "绿皮火车汽笛、工厂汽笛远去、录像厅烟雾、"
            "街头收音机与自行车铃声（视觉：empty street、waiting figure）；"
            "幽默苦涩，非 melodrama 大哭或 action spectacle。"
        ),
        "materials": (
            "水泥墙面、旧自行车、喇叭裤、工装夹克、塑料凉鞋、"
            "VCD 盗版海报、生锈铁门、煤烟空气；"
            "皮肤晒斑与粗糙纹理可见；忌 luxury leather、modern glass tower dominant。"
        ),
        "quality": (
            "独立电影放映级：grain 可见但非 noise disaster；"
            "4K scan from film 感，禁 oversharpen 与 skin smoothing；"
            "环境细节（电线、招牌字体）服务时代识别。"
        ),
        "taboos": (
            "古偶柔光美颜、HDR 过曝、4K 塑料锐化、赛博霓虹、"
            "好莱坞 glamour、日系清新高饱和、古装仙侠。"
        ),
        "characters_zh": (
            "90年代县城青年、工人、小贩：乱发、真实痘斑与晒痕；"
            "喇叭裤、工装、廉价夹克、布鞋；"
            "表情木讷或苦笑，肢体语言拘谨；"
            "群像：骑车少年、蹲门口老人、录像厅老板。"
        ),
        "characters_en": (
            "1990s Chinese realistic cinema character, small county town youth, "
            "plain worker cotton jacket, natural unretouched weathered face, "
            "documentary presence, cheap 90s fashion, tired eyes, "
            "standing on grey overcast street, Jia Zhangke aesthetic"
        ),
        "scenes_zh": (
            "县城主街、倒闭工厂大门、录像厅霓虹、绿皮火车站台、"
            "灰色天空下的河堤、破旧居委会院子、夜市廉价灯泡。"
        ),
        "scenes_en": (
            "1990s Chinese county town street overcast, dilapidated factory gate, "
            "video parlor neon sign, green train station platform, "
            "grey sky urban China, documentary wide empty road, "
            "river embankment with distant smokestack"
        ),
        "colors": "灰绿, 水泥灰, 褪色红, 阴天天空灰蓝, 钨灯暖黄, 录像厅蓝紫",
        "image_prompt": (
            "1990s Chinese realistic cinema, grey green desaturated color grade, "
            "overcast natural light small county town, unretouched authentic faces, "
            "documentary framing factory and bicycle era details, "
            "16mm 35mm film grain, Jia Zhangke Wang Xiaoshu aesthetic, "
            "muted nostalgic China 1990s atmosphere, 4k"
        ),
        "video_prompt": (
            "slow long take street walk toward camera, overcast light steady hold, "
            "distant train horn mood, grey green county town atmosphere, "
            "factory gate wind flutter banner, documentary camera drift"
        ),
        "references": [
            "小武 (1997)",
            "站台 (2000)",
            "三峡好人 (2006)",
            "十七岁的单车 (2001)",
        ],
    },
    "cn_90s_rural_film": {
        "summary": (
            "90年代中国农村电影风格：以 1980s–1990s 中国乡土电影高峰（张艺谋《红高粱》《秋菊打官司》、"
            "陈凯歌《黄土地》、谢晋农村题材、顾长卫摄影）为基准，"
            "呈现黄土高原、晒场、红盖头与粗粝阳光并存的「land ethics + epic rural color」视觉语法。"
            "人物以农民、新娘、村支书为主，晒黑皮肤与粗手；场景强调黄土坡、晒谷场、"
            "窑洞庭院、婚轿队伍。整体为 live-action 35mm rural epic cinema，"
            "偏黄土+大红+靛蓝高饱和 LUT，绝不做都市霓虹、古偶美颜或日系清新。"
            "适合乡土叙事、农村年代、土地伦理 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 90年代中国农村电影（Chinese 90s Rural Film Live-Action）",
        "artist_refs": (
            "导演：张艺谋早期、陈凯歌、谢晋、吴天明；"
            "摄影：顾长卫、侯咏、吕乐；"
            "作品：《红高粱》《黄土地》《秋菊打官司》《活着》《大红灯笼高高挂》早期段落；"
            "美学：wide landscape human small、harsh sun dust、harsh primary color blocking、"
            "epic rural procession composition。"
        ),
        "era_texture": (
            "1980s–1990s 西北/华北农村 35mm film grain visible；"
            "hard sunlight with airborne dust motes；"
            "粗布、土墙、高粱穗 texture readable；"
            "digital 须 emulate film saturation 与 skin weathering，no beauty filter。"
        ),
        "line_control": (
            "构图 wide landscape 人物渺小，horizon low 强调土地；"
            "婚嫁队伍 diagonal 穿越晒场；"
            "窑洞门口 frame within frame；"
            "少 shaky handheld，多用 locked wide 与 slow pan over yellow earth。"
        ),
        "lighting_color": (
            "主光：硬阳顶光或侧阳，尘土散射柔化但 shadow 仍硬；"
            "室内窑洞：窗洞光束 dust visible；"
            "禁忌：flat LED office、cyber neon、soft romcom fill only。"
        ),
        "palette_strategy": (
            "主调：黄土、大红、靛蓝、尘金黄、天空灰蓝；"
            "张艺谋式 primary color blocking 于婚嫁/晒场场景；"
            "肤色晒黑偏红，唇自然无 glamour；"
            "悲剧场景可压饱和但保留红/黄土地锚点。"
        ),
        "atmosphere": (
            "厚重、命运、土地伦理、集体与个体张力；"
            "风声高粱、婚鼓、尘土、晒场翻粮（视觉：grain wave、red veil flutter）；"
            "epic stillness 与突发冲突并存；"
            "非都市消费主义叙事。"
        ),
        "materials": (
            "粗布棉袄、土墙、高粱、晒场木耙、"
            "红盖头、花轿、驴车、陶罐、麦秸；"
            "忌 glass skyscraper、sportswear logo、synthetic neon。"
        ),
        "quality": (
            "乡土史诗电影级：dust in air、fabric weave、far horizon clarity；"
            "4K film scan 感，thumbnail 可辨黄土与红嫁衣。"
        ),
        "taboos": (
            "都市霓虹、古偶柔光美颜、日系清新、3D cartoon、"
            "cyberpunk、modern mall interior dominant。"
        ),
        "characters_zh": (
            "农民、新娘、村支书：晒黑皮肤、粗手、棉袄粗布；"
            "新娘红盖头/花轿服饰；"
            "村支书中山装或旧式干部装；"
            "群像：晒场劳作、婚嫁吹鼓。"
        ),
        "characters_en": (
            "1990s Chinese rural film character, peasant cotton clothing, "
            "sun weathered skin rough hands, red bridal veil costume, "
            "earthy village presence, Zhang Yimou early rural epic aesthetic, "
            "Loess plateau dignity portrait"
        ),
        "scenes_zh": (
            "黄土高原沟壑、晒谷场翻粮、窑洞院落、"
            "高粱地逆风、婚轿队伍尘土路、黄河岸边史诗远景。"
        ),
        "scenes_en": (
            "Loess plateau yellow earth hills, grain drying field harvest, "
            "cave dwelling courtyard, sorghum field wind, "
            "traditional rural wedding procession dust road, "
            "epic wide yellow landscape small human figure"
        ),
        "colors": "黄土, 大红, 靛蓝, 尘金黄, 天空灰蓝, 麦秆褐, 肤色晒红",
        "image_prompt": (
            "1990s Chinese rural cinema, Loess plateau landscape harsh sunlight dust in air, "
            "red bridal costume primary color blocking, earthy village architecture cave dwelling, "
            "Zhang Yimou Chen Kaige early aesthetic, rich saturated yellow red blue, "
            "35mm film grain epic rural composition, unretouched weathered faces, 4k"
        ),
        "video_prompt": (
            "wind across sorghum field waves, dust motes in harsh sun slow pan, "
            "rural wedding procession walk dust rise, grain shovel rhythm on drying field, "
            "yellow earth hills timelapse cloud"
        ),
        "references": [
            "红高粱 (1987)",
            "黄土地 (1984)",
            "秋菊打官司 (1992)",
            "活着 (1994)",
        ],
    },
    "cn_suspense_cold_tone": {
        "summary": (
            "国产悬疑冷调风格：以 2010s–2020s 国产罪案悬疑剧/电影（《隐秘的角落》《沉默的真相》《白夜追凶》"
            "《平原上的摩西》《无证之罪》）及刁亦男、辛爽式摄影美学为基准，呈现青蓝灰冷调、雨夜霓虹反射、"
            "对称/框中框构图与孤独人物并存的「urban mystery + psychological distance」视觉语法。"
            "人物以普通中年脸、雨衣、烟与疲惫眼神为核心；场景强调雨夜立交、废弃游乐园、海边堤岸、"
            "窄巷湿沥青与廉价 motel。整体为 live-action 电影级写实摄影，偏 teal-cyan-grey 冷调 LUT，"
            "局部危险橙/病态绿霓虹作点缀，绝不做古偶粉光、明亮 comedy 或纯 vintage warm only。"
            "适合国产悬疑、罪案、社会派推理向 AIGC 短剧的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 国产悬疑冷调（Chinese Suspense Cold Tone Live-Action）",
        "artist_refs": (
            "摄影与美术参照：《隐秘的角落》《沉默的真相》《白夜追凶》《平原上的摩西》《无证之罪》组；"
            "电影参照：刁亦男《白日焰火》《南方车站的聚会》、忻钰坤《心迷宫》、"
            "文晏《嘉年华》、张大磊《漫长的季节》摄影语言；"
            "美学：对称构图、框中框、anamorphic 宽银幕、长焦压缩、雨夜 practical neon。"
        ),
        "era_texture": (
            "2010s–2020s 国产悬疑剧电影化高峰，4K digital cinema clean dark（非粗颗粒战争片）；"
            "可选 subtle film grain 增强 mystery mood；"
            "雨夜场景带 wet surface specular、车窗/玻璃 rain streak；"
            "南方小城/沿海/工业废墟带 humid haze 与 muted saturation；"
            "色彩经 teal-cyan shadow + desaturated midtone 调色，保留 realistic skin 无 glamour filter。"
        ),
        "line_control": (
            "构图以对称轴、框中框（门框/窗框/后视镜/监控画面）与纵深消失点为主；"
            "人物常用 center frame 或 extreme wide 显渺小；"
            "长焦 compression 压缩空间制造 claustrophobia；"
            "少用手持 comedy shake，多用 slow dolly / locked-off / crane 俯视；"
            "监控/行车记录仪/手机竖屏可嵌套为 narrative device（须保持 cold grade 一致）。"
        ),
        "lighting_color": (
            "主光：冷键光（5600K–6500K 偏青）侧光或顶光，面部保留 shadow 层级；"
            "辅光：极弱 fill 或干脆 no fill 强化 isolation；"
            "点缀：霓虹橙/绿/红 practical（sign、路灯、便利店）在 wet ground 反射；"
            "雨夜：streetlight pools、car headlight streak、lightning flash optional；"
            "禁忌：warm golden hour romcom、flat beauty dish、过度 HDR 亮部。"
        ),
        "palette_strategy": (
            "主调：青蓝（teal/cyan）、冷灰、雨夜黑、湿 asphalt 反光；"
            "点缀：危险橙（neon sign）、病态绿（fluorescent）、暗红（警示/血暗示但非 gore）；"
            "肤色：偏冷 neutral，眼下 shadow 可见，唇色 natural desaturated；"
            "叙事用色：真相逼近时略提 contrast；回忆/温暖假象可短暂 warm insert 后回到 cold。"
        ),
        "atmosphere": (
            "压抑、谜题、urban loneliness、hidden threat 与 mundane evil 并存；"
            "雨声、远处车流、霓虹 buzz、空荡游乐场 rust（视觉：wet empty spaces）；"
            "对话场景常用「近景疲惫脸 + 远景冷色 urban void」对照；"
            "儿童/家庭场景亦带 unsettling undertone（非 bright sitcom）。"
        ),
        "materials": (
            "环境：湿沥青、玻璃反光、廉价 motel 床单、废弃游乐设施 rust、"
            "沿海堤岸 moss、窄巷 brick、便利店 fluorescent、老小区 green paint；"
            "道具：雨衣、折叠伞、烟、手机、老式相机、钓鱼线、药瓶、"
            "儿童玩具（contrasting innocence）、警灯 red-blue flash；"
            "车辆：出租车、面包车、老式 sedan 雨夜 wet body。"
        ),
        "quality": (
            "4K drama/thriller cinematography，暗部 detail 保留（非 crushed black mush）；"
            "适合 9:16 竖版角色卡与 2.39:1 宽银幕场景；"
            "anamorphic lens flare optional、slight barrel distortion acceptable；"
            "live-action realistic，非插画、非 anime、非 bright romcom。"
        ),
        "taboos": (
            "古偶粉光、仙侠 glow、明亮 comedy sitcom lighting；"
            "纯 vintage warm only（如 80s 港片饱和红）无 cold counterbalance；"
            "日系 anime、韩漫 glass skin、网红美颜；"
            "赛博朋k 过度 neon chaos（除非叙事需要且仍 cold dominant）；"
            "gore splatter horror、supernatural VFX 主导；"
            "watermark、字幕条、多格漫画分镜（单图角色卡时）。"
        ),
        "characters_zh": (
            "【面部】普通中年脸、真实皱纹与眼袋、无 glamour makeup；"
            "表情：疲惫、警惕、假笑、空洞 stare、压抑 rage——"
            "「日常下的异常」。"
            "【妆发】自然黑发/灰发、简单短发或凌乱，无精致造型；"
            "可选：胡茬、汗湿额发、雨湿贴发。"
            "【服饰】雨衣、深色夹克、POLO/格子衬衫、工厂工装、"
            "警察/保安制服（desaturated）；"
            "手持：烟、手机、手电筒、鱼竿、塑料袋。"
            "【体态】slumped shoulders、背对镜头、"
            "frame within window/car mirror、独处多于群像。"
            "【气质范例】张东升——压抑微笑；朱朝阳——少年阴郁；"
            "严良——街头警觉；江阳——执着疲惫。"
        ),
        "characters_en": (
            "Chinese suspense cold tone live-action character, tired middle aged ordinary face, "
            "raincoat under cold streetlight, exhausted suspicious expression, "
            "teal cyan grey cinematic color grade, wet hair and natural skin texture no glamour, "
            "isolated urban figure at night, anamorphic thriller framing, "
            "mystery drama cinematography, neon orange accent reflection on wet ground, "
            "no anime, no bright romcom lighting, highly detailed 4k"
        ),
        "scenes_zh": (
            "【典型环境】雨夜立交、废弃游乐园（旋转木马/摩天轮 rust）、"
            "海边堤岸 fog、窄巷 wet brick、廉价 motel 走廊、"
            "老小区楼梯间、工厂区 night、山顶气象站、"
            "便利店 fluorescent、出租车 interior rain streak。"
            "【构图】对称 corridor、frame in car window/mirror、"
            "extreme wide lone figure、surveillance angle optional。"
            "【光影】冷键光 + neon practical reflection、"
            "雨夜 ground pool light、lightning single flash。"
            "【气候】南方 humid rain、沿海 fog、秋冬 cold drizzle；"
            "避免 bright sunny picnic  unless unsettling contrast。"
        ),
        "scenes_en": (
            "rainy overpass night Chinese city, abandoned amusement park rust cold mood, "
            "coastal embankment fog teal grey grade, narrow alley wet asphalt neon reflection, "
            "cheap motel corridor fluorescent hum, symmetrical thriller composition, "
            "anamorphic cinematic framing, mystery drama atmosphere, "
            "desaturated cold urban loneliness, live-action suspense cinematography, 4k"
        ),
        "colors": (
            "主色：青蓝、冷灰、雨夜黑、湿面反光银；"
            "点缀：霓虹橙、病态绿、暗红、警灯蓝红；"
            "肤色：冷 neutral desaturated；"
            "叙事：回忆 warm insert 短暂；真相逼近略提 contrast"
        ),
        "image_prompt": (
            "Chinese suspense cold tone live-action cinematography, teal cyan grey color grade, "
            "rainy night urban wet asphalt neon reflections, lonely tired figure under streetlight, "
            "symmetrical anamorphic thriller framing, abandoned amusement park or coastal fog mood, "
            "mystery drama atmosphere, desaturated cold palette with danger orange neon accent, "
            "realistic skin no glamour filter, Hidden Corner / Chinese crime drama aesthetic, "
            "no bright romcom, no anime, highly detailed 4k vertical 9:16"
        ),
        "video_prompt": (
            "rain streaks on lens and car window, slow push toward lonely figure under cold streetlight, "
            "neon reflection ripple on wet road, symmetrical corridor dolly, "
            "teal grey grade consistent suspense atmosphere, "
            "subtle thunder flash optional, no shaky comedy cam, restrained thriller pacing"
        ),
        "references": [
            "隐秘的角落 (2020)",
            "沉默的真相 (2020)",
            "白日焰火 (2014)",
            "南方车站的聚会 (2019)",
        ],
    },
    "cn_urban_realistic": {
        "summary": (
            "国产都市写实风格：以 2010s–2020s 中国一线城市现实主义剧集/电影（《我在他乡挺好的》"
            "《爱情神话》《我不是药神》《文牧野都市片》、娄烨《春娇与志明》都市段落）"
            "摄影美学为基准，呈现地铁通勤、玻璃幕墙、便利店荧光灯与真实 interpersonal drama "
            "并存的「tier-one city life flow + unfiltered authenticity」视觉语法。"
            "人物以白领、外卖员、合租青年为主，妆发生活化；场景强调早高峰地铁、"
            "开放式办公室、深夜便利店、合租屋窗景。整体为 live-action 4K digital cinema documentary drama，"
            "偏 neutral urban LUT 无 glamour filter，绝不做古偶、欧美街道或过度商业广告精致感。"
            "适合都市情感、现实主义、职场与生活流 AIGC 短剧的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 国产都市写实（Chinese Urban Realistic Live-Action Drama）",
        "artist_refs": (
            "作品参照：《我在他乡挺好的》《爱情神话》《我不是药神》《逆行人生》；"
            "导演：文牧野、娄烨都市段落、李雪琴剧综电影化摄影；"
            "美学：handheld or gentle stabilizer、mixed LED window light、"
            "fluorescent convenience store、authentic Beijing Shanghai Shenzhen skyline。"
        ),
        "era_texture": (
            "2020s 中国一线与新一线 digital 4K clean，但禁 beauty filter 与过度磨皮；"
            "地铁、共享单车、外卖箱、手机屏光为时代质感；"
            "夜景窗灯与路灯混合，湿度南方城市 optional haze；"
            "色彩 neutral realistic，偶现品牌广告色块作都市背景 noise。"
        ),
        "line_control": (
            "构图生活流：over-shoulder dialogue、mirror reflection、crowd in frame；"
            "地铁用 frame within frame（车门、扶手）；"
            "办公室 wide showing cubicle geometry；"
            "少 epic wide hero，强调 medium close 情绪与环境的并置。"
        ),
        "lighting_color": (
            "主光：窗光+办公室 LED panel 混合；"
            "地铁：顶光冷白+手机 face glow；"
            "便利店：fluorescent green-cyan overhead；"
            "夜景：city bokeh amber + screen blue on face；"
            "禁忌：single golden hour only、palace candle、cyber neon alley。"
        ),
        "palette_strategy": (
            "主调：都市灰、窗光白、地铁银、夜窗蓝、便利店黄绿荧光；"
            "肤色真实偏倦容，允许黑眼圈与油光；"
            "服装 muted 大地色+通勤黑灰；"
            "情绪高潮可用 warm interior tungsten 对比冷窗外景。"
        ),
        "atmosphere": (
            "真实、疲惫、微小希望与都市孤独；"
            "早高峰拥挤、加班关灯、便利店饭团、"
            "合租屋泡面临食（视觉：steam、rain on window）；"
            "幽默与辛酸并存，非 fantasy escape。"
        ),
        "materials": (
            "玻璃幕墙、不锈钢地铁、塑料外卖箱、共享单车、"
            "开放式工位隔板、泡面纸杯、雨伞湿痕；"
            "忌 medieval costume、suburban American porch、luxury hotel only。"
        ),
        "quality": (
            "流媒体电影级 4K documentary drama：sharp environment readable；"
            "skin texture preserved；thumbnail 可辨都市语境（地铁/写字楼）。"
        ),
        "taboos": (
            "古偶仙侠、过度 LUT 网红滤镜、欧美街道招牌、"
            "glamour beauty commercial、赛博朋克、古装宫廷。"
        ),
        "characters_zh": (
            "都市白领、外卖骑手、合租青年：卫衣风衣、通勤妆、"
            "疲惫眼神、地铁耳机、工牌与外卖头盔；"
            "老人摊贩、便利店店员作群像；"
            "肢体语言真实拘谨或崩溃瞬间。"
        ),
        "characters_en": (
            "contemporary Chinese urban realism character, office worker casual fashion, "
            "metro commute exhaustion, delivery rider uniform helmet, "
            "shared apartment youth hoodie, authentic modern city life face no glamour filter, "
            "fluorescent convenience store lighting portrait"
        ),
        "scenes_zh": (
            "北京上海地铁早高峰、开放式办公室夜景、深夜便利店、"
            "高层合租窗景、雨后斑马线、外卖电动车巷口、商场地下通道。"
        ),
        "scenes_en": (
            "Beijing Shanghai metro rush hour crowd, open plan office night lights, "
            "convenience store fluorescent interior, high rise apartment window city lights, "
            "rainy crosswalk commute, delivery scooter alley corner, "
            "authentic contemporary China urban documentary scene"
        ),
        "colors": "都市灰, 窗光白, 地铁银, 夜窗蓝, 便利黄绿, 柏油路黑, 雨衣透明",
        "image_prompt": (
            "contemporary Chinese urban realism cinematography, metro commute scene, "
            "modern office and convenience store fluorescent, natural mixed lighting, "
            "authentic city life details shared bike delivery box, "
            "realistic skin no glamour filter documentary drama framing, "
            "tier-one city atmosphere Beijing Shanghai, 4k"
        ),
        "video_prompt": (
            "metro crowd slow motion push, office lights turning off sequence, "
            "convenience store door chime entrance, rain on taxi window bokeh drift, "
            "urban life realistic camera follow walk"
        ),
        "references": [
            "我在他乡挺好的 (2021)",
            "爱情神话 (2021)",
            "我不是药神 (2018)",
            "逆行人生 (2024)",
        ],
    },
    "cn_warm_blue_glow": {
        "summary": (
            "中式暖调蓝辉风格：以 2010s 国产青春都市情感片（《后来的我们》《你的婚礼》《匆匆那年》"
            "《前任》系列摄影）为基准，呈现雨夜窗光冷蓝与室内钨丝暖光互补、"
            "浅景深人物居中与 bokeh 街灯并存的「urban melancholy + healing blue」视觉语法。"
            "人物以青年男女卫衣风衣为主，望窗、雨中对视与侧脸蓝辉轮廓；"
            "场景强调雨夜出租车窗、天台串灯、小酒馆蓝琥珀混合夜景。"
            "整体为 live-action digital emotional cinema，偏 soft blue-orange gentle grade LUT，"
            "绝不做 hard noir、古装宫廷或 horror green dominant。"
            "适合国产青春、都市情感、治愈感伤 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 国产暖蓝情感都市片（Chinese Warm Blue Glow Emotional Cinema Live-Action）",
        "artist_refs": (
            "导演：刘若英、韩琰、张一白青春都市线；"
            "摄影：国产青春片灯光组（窗光蓝+钨暖对比）；"
            "作品：《后来的我们》《你的婚礼》《匆匆那年》《前任3》；"
            "美学：rainy window bokeh、blue rim on cheek、tungsten interior warmth、"
            "shallow DOF centered portrait、string light gold accent。"
        ),
        "era_texture": (
            "2010s–2020s 国产 digital emotional cinema，clean sensor 但肤质柔和；"
            "雨夜玻璃水珠与街灯 bokeh readable；"
            "室内钨丝略暖偏黄，窗外环境光冷蓝；"
            "digital 须 emulate gentle grade 非 HDR 硬对比，no beauty filter plastic skin。"
        ),
        "line_control": (
            "构图人物居中或三分，浅景深 isolates subject from city bokeh；"
            "窗框/车门 frame within frame；"
            "天台串灯作前景 depth layer；"
            "movement 慢：slow push-in on tear、rain streak on glass。"
        ),
        "lighting_color": (
            "主光：窗外冷蓝环境光作 rim 或侧光，面部半暖半蓝；"
            "辅光：室内钨丝台灯/串灯 warm fill；"
            "雨夜：wet surface reflection 加倍蓝橙；"
            "禁忌：flat daylight office、hard noir single source only、horror green cast。"
        ),
        "palette_strategy": (
            "主调：窗光蓝、钨丝暖、雨夜灰、串灯金、肤柔粉；"
            "蓝橙互补但整体偏柔，shadow 保留 detail 非 crushed black；"
            "肤色柔和偏粉，唇自然或淡玫瑰；"
            "感伤场景可略降饱和但保留 blue window anchor。"
        ),
        "atmosphere": (
            "感伤、治愈、都市孤独、青春遗憾与重逢；"
            "雨声、出租车引擎、串灯微风、咖啡杯热气（视觉：steam、rain streak）；"
            "melancholic romantic 非甜宠高糖；"
            "孤独中的温度是核心情绪符号。"
        ),
        "materials": (
            "玻璃雨痕、串灯 bulb、咖啡杯陶瓷、"
            "卫衣棉质、风衣面料、出租车 leather seat；"
            "忌古装绸缎、工业 rust、neon cyber dominant。"
        ),
        "quality": (
            "国产情感片院线级：bokeh smooth、skin soft but pore subtle；"
            "rain on glass refraction readable；"
            "4K digital clean，thumbnail 可辨蓝暖对比与人物情绪。"
        ),
        "taboos": (
            "hard noir only、古装宫廷、horror green、"
            "cyber neon、desaturated nordic grey only、3D cartoon。"
        ),
        "characters_zh": (
            "青年男女：卫衣、风衣、牛仔裤；"
            "望窗或雨中对视，侧脸蓝辉轮廓；"
            "表情 melancholic romantic，微湿发或额前碎发；"
            "配饰：耳机、手机、简单项链。"
        ),
        "characters_en": (
            "Chinese youth emotional drama character, hoodie and coat rainy night, "
            "window blue glow on face warm tungsten interior contrast, "
            "melancholic romantic expression shallow DOF, "
            "urban night bokeh portrait, soft skin gentle blue orange grade"
        ),
        "scenes_zh": (
            "雨夜出租车窗 bokeh、天台串灯夜景、"
            "小酒馆蓝琥珀混合、便利店门口雨棚、"
            "都市高架桥下车流光轨。"
        ),
        "scenes_en": (
            "rainy taxi window city bokeh night, rooftop string lights urban skyline, "
            "cozy bar blue amber mixed lighting, convenience store rain shelter, "
            "overpass traffic light trails emotional nightscape"
        ),
        "colors": "窗光蓝, 钨丝暖, 雨夜灰, 串灯金, 肤柔粉, 街灯琥珀, 柏油路黑",
        "image_prompt": (
            "Chinese warm blue glow cinematography, rainy window city bokeh night, "
            "tungsten interior warm contrast blue rim light on face, "
            "youth romance melancholy shallow DOF, soft skin tones, "
            "blue orange gentle grade urban emotional scene, "
            "string lights gold accent, 4k digital emotional cinema"
        ),
        "video_prompt": (
            "rain on window timelapse streaks, string lights gentle sway breeze, "
            "slow turn toward camera blue rim catch eye, "
            "warm blue emotional atmosphere taxi interior glow, "
            "city bokeh drift slow push-in"
        ),
        "references": [
            "后来的我们 (2018)",
            "你的婚礼 (2021)",
            "匆匆那年 (2014)",
        ],
    },
    "cyberpunk_digital_illustration": {
        "summary": '赛博朋克数字插画：霓虹雨夜、义体与全息广告，Syd Mead 式未来城市平面化呈现。高对比紫青与粉，适合封面与概念海报。',
        "category": '赛博朋克数字插画',
        "artist_refs": 'Syd Mead、Moebius cyber、Kilian Eng',
        "era_texture": '1980s–2020s cyberpunk visual evolution',
        "line_control": '硬边几何+细线机械',
        "lighting_color": '霓虹rim+湿面反射',
        "palette_strategy": '紫青+电粉+深黑',
        "atmosphere": ' dystopia、 cool、 high tech low life',
        "materials": 'chrome、 hologram、 rain streak',
        "quality": 'poster print sharp neon',
        "taboos": ' medieval,  pastoral,  flat corporate',
        "characters_zh": '义体改造人，发光眼罩，长风衣与机械臂。',
        "characters_en": 'cyberpunk digital illustration character, neon rim light, cybernetic implants, long tech coat, rain soaked futuristic streetwalker',
        "scenes_zh": '多层高架、中文霓虹招牌、飞行车轨。',
        "scenes_en": 'cyberpunk megacity alley, holographic billboards, rain reflective asphalt, flying vehicle lanes, neon kanji signs',
        "colors": '电紫, 青蓝, 霓虹粉, 深黑, 铬银',
        "image_prompt": 'cyberpunk digital illustration, neon purple and cyan, rain soaked futuristic city alley, holographic advertisements, cybernetic character portrait, chrome reflections, Syd Mead inspired design, high contrast poster art, detailed megacity, 4k',
        "video_prompt": 'neon sign flicker rain, hologram glitch loop, camera drift through cyber alley, rain streaks on lens, dystopian city atmosphere motion',
        "references": [
        'Blade Runner (1982)',
        'Ghost in the Shell (1995)',
        'Cyberpunk 2077 key art',
        ],
    },
    "dali_surreal": {
        "summary": '达利式超现实：软钟、长腿象、沙漠与梦境并置。写实渲染+不可能物理，哲学与潜意识视觉隐喻。',
        "category": '超现实主义/达利',
        "artist_refs": 'Salvador Dalí、René Magritte cross、现代3D homages',
        "era_texture": '20世纪超现实绘画数字再诠释',
        "line_control": '写实物体轮廓，梦境组合',
        "lighting_color": '沙漠长影或平光梦境',
        "palette_strategy": '金褐沙漠+蓝天+本白',
        "atmosphere": '梦境、荒诞、静止张力',
        "materials": ' melting metal、 elephant stilts、 ants',
        "quality": 'gallery print precision',
        "taboos": ' cartoon,  cyberpunk,  busy clutter',
        "characters_zh": '西装男、浮空人物、面具，表情 detached。',
        "characters_en": 'Dalí surreal figure, melting clock motif, stiff dream pose, desert horizon, metaphysical portrait, long shadow',
        "scenes_zh": '卡达克斯沙漠、软钟树、无限台阶。',
        "scenes_en": 'Dalí desert landscape, melting clocks on branch, infinite staircase sky, dream paradox seascape',
        "colors": '沙漠金, 天空蓝, 本白, 长影褐, 梦境紫',
        "image_prompt": 'Salvador Dalí surrealist scene, melting clocks in desert, long shadow golden hour, dreamlike impossible objects, metaphysical composition, crisp surreal details, elephant on stilts horizon, philosophical atmosphere, museum quality, 4k',
        "video_prompt": 'slow melting clock morph, desert heat shimmer, dream figure levitation subtle, surreal object drift, metaphysical camera glide',
        "references": [
        'Persistence of Memory (1931)',
        'Elephants Dalí',
        'Un Chien Andalou (1929)',
        ],
    },
    "dark_concept_art": {
        "summary": '黑暗概念艺术：末世、恐怖与 sci-fi horror 的探索稿。 loose brush + 强 silhouette，用于游戏与影视前期视觉开发。',
        "category": '黑暗概念艺术',
        "artist_refs": 'Brom、Wayne Barlowe、Bloodborne concept',
        "era_texture": '当代 dark fantasy preproduction',
        "line_control": 'massing first，detail second',
        "lighting_color": 'rim only in black fog',
        "palette_strategy": 'near monochrome + blood red',
        "atmosphere": ' dread、 unknown、 epic horror',
        "materials": 'bone, rust, wet leather',
        "quality": 'thumbnail to hero readable',
        "taboos": ' cute,  bright pastel,  clean utopia',
        "characters_zh": '异形轮廓、重甲骑士、不可名状剪影。',
        "characters_en": 'dark concept art creature silhouette, biomechanical horror design, armored knight in fog, Brom inspired monster, ominous scale',
        "scenes_zh": '废城、血月、地下祭坛、巨构废墟。',
        "scenes_en": 'post apocalyptic ruins concept, blood moon wasteland, underground ritual chamber, colossal dead architecture',
        "colors": '炭黑, 铁锈, 血红, 冷蓝rim, 尘灰',
        "image_prompt": 'dark concept art, ominous creature silhouette in fog, post apocalyptic ruins, blood red accent lighting, Brom inspired horror fantasy, loose epic brushwork, cinematic scale, production design exploration, 4k',
        "video_prompt": 'fog reveal monster silhouette, ember drift in ruins, slow ominous camera push, dark concept atmosphere build, horror scale motion',
        "references": [
        'Bloodborne concept art',
        'Wayne Barlowe Inferno',
        'Brom dark fantasy',
        ],
    },
    "dark_fantasy_illustration": {
        "summary": '黑暗奇幻插画：哥特铠甲、龙与 necromancer，book cover 级精细插画。介于 D&D 与 metal album art。',
        "category": '黑暗奇幻插画',
        "artist_refs": 'Frank Frazetta legacy、Peter Mohrbacher、Diablo IV art',
        "era_texture": '当代 fantasy book cover',
        "line_control": 'painterly edge，dramatic pose',
        "lighting_color": 'underlighting+ storm sky',
        "palette_strategy": 'deep purple+ ember orange',
        "atmosphere": ' epic dark、 heroic grim',
        "materials": 'engraved armor, dragon scale, magic smoke',
        "quality": 'cover art print detail',
        "taboos": ' chibi,  modern street,  sci-fi chrome',
        "characters_zh": '披风骑士、女巫、亡灵法师，武器发光。',
        "characters_en": 'dark fantasy illustration warrior, gothic plate armor, glowing runic sword, cape in storm wind, demonic presence background',
        "scenes_zh": '雷暴城堡、骨龙盘旋、诅咒森林。',
        "scenes_en": 'stormy gothic castle, bone dragon circling, cursed forest dead trees, lava chasm fantasy battlefield',
        "colors": '深紫, 余烬橙, 铁黑, 毒绿魔法, 风暴灰',
        "image_prompt": 'dark fantasy illustration, gothic armored warrior, stormy castle background, glowing magical sword, dragon silhouette, painterly epic composition, rich purple and ember palette, book cover quality, detailed armor engraving, 4k',
        "video_prompt": 'lightning flash on castle, cape billow in storm, magic rune pulse on sword, dragon shadow pass overhead, epic dark fantasy motion',
        "references": [
        'Diablo IV key art',
        'Magic The Gathering dark sets',
        'Frank Frazetta Conan',
        ],
    },
    "dark_manga": {
        "summary": '黑暗系漫画：Berserk、Death Note 式高对比 ink 与心理 horror。阴影吞噬面部，线条凌厉。',
        "category": '黑暗漫画/日式',
        "artist_refs": 'Kentaro Miura、Takeshi Obata dark scenes、Junji Ito ink',
        "era_texture": '1990s–2000s seinen dark',
        "line_control": '刮刻感黑块与细线',
        "lighting_color": '极端明暗，无中间调',
        "palette_strategy": '黑白为主，偶深红',
        "atmosphere": '绝望、暴力、心理压迫',
        "materials": '刮刀白、墨水飞白',
        "quality": '印刷线条锐利',
        "taboos": ' moe bright,  shonen color,  soft pastel',
        "characters_zh": '疤痕战士、瘦高 antagonist、扭曲笑容。',
        "characters_en": 'dark manga character, heavy ink shadows, scarred berserker armor, sinister thin smile, psychological horror expression, scratchy linework',
        "scenes_zh": '.eclipse sky、 torture chamber hint、 rain battle mud。',
        "scenes_en": 'dark manga battlefield rain, eclipse crimson sky, oppressive black corridor, scratchy ink background chaos',
        "colors": '纯黑, 纸白, 深红, 灰刮痕',
        "image_prompt": 'dark manga illustration, heavy black ink shadows, scratchy seinen linework, scarred armored warrior, psychological horror atmosphere, high contrast monochrome with crimson accent, Berserk inspired intensity, 4k',
        "video_prompt": 'ink shadow creep across face, scratchy line boil effect, rain slash battle motion, crimson eclipse pulse, dark manga intensity',
        "references": [
        'Berserk manga',
        'Death Note (2003)',
        'Junji Ito Uzumaki',
        ],
    },
    "game_concept_art": {
        "summary": '通用游戏概念艺术：东西融合的探索视觉，关卡/角色/道具三位一体。工业流程导向，强调可读与迭代。',
        "category": '游戏概念艺术',
        "artist_refs": 'Riot、FromSoftware mood、ArtStation AAA',
        "era_texture": '当代 AAA/AA preproduction',
        "line_control": 'structure lines + value block',
        "lighting_color": 'quick key light studies',
        "palette_strategy": 'faction color coding',
        "atmosphere": 'worldbuilding、 exploration',
        "materials": 'labeled material callouts',
        "quality": 'review-ready clarity',
        "taboos": ' final marketing polish only,  inconsistent scale',
        "characters_zh": 'silhouette 探索3–5变体，装备层级清晰。',
        "characters_en": 'game concept art hero exploration, silhouette variants, annotated gear layers, adventure protagonist design studies',
        "scenes_zh": 'hub town、battle arena、world map node。',
        "scenes_en": 'game hub town concept, battle arena layout, overworld landmark vista, biome exploration thumbnails',
        "colors": '探索暖冷对比, 标注红, 中性灰底',
        "image_prompt": 'video game concept art, hero character exploration sketches, epic environment vista, annotated design process, production art quality, clear silhouette readable shapes, adventure fantasy worldbuilding, 4k',
        "video_prompt": 'concept art overlay fade between variants, camera pan environment vista, design annotation appear, game previs exploration motion',
        "references": [
        'Elden Ring environment art',
        'League of Legends champion concepts',
        'God of War visual development',
        ],
    },
    "greek_mythology_film": {
        "summary": (
            "希腊神话电影风格：以 2000s epic historical fantasy 高峰（《300》《特洛伊》《诸神之战》）"
            "为基准，呈现大理石柱、togas、爱琴海蓝与史诗云并存的 "
            "「gods among men + Mediterranean epic」视觉语法。"
            "人物以古希腊铠甲、月桂冠、肌肉英雄与爱琴阳光古铜肤为核心；"
            "场景强调帕特农、爱琴崖、奥林匹斯云、大理石庭院。"
            "整体为 live-action 35mm epic grade cinema，偏大理石白+海蓝+青铜 LUT，"
            "绝不做 cyber、东亚宫廷或 cartoon 主导。"
            "适合神话史诗、古希腊题材、英雄奇幻 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 希腊神话史诗电影（Greek Mythology Epic Film Live-Action）",
        "artist_refs": (
            "导演：Ridley Scott《特洛伊》、Zack Snyder《300》；"
            "美术：Frank Miller《300》adapt、Roger Dean myth visual；"
            "作品：《特洛伊》《300》《诸神之战》；"
            "美学：monumental composition、hard Mediterranean sun、"
            "marble column courtyard、dust in heroic battle air。"
        ),
        "era_texture": (
            "2000s epic historical fantasy 35mm grade；"
            "marble weathering、bronze armor patina readable；"
            "linen toga weave、Mediterranean heat haze；"
            "digital 须 emulate epic film dust 非 clean studio HDR。"
        ),
        "line_control": (
            "构图 monumental wide，英雄 low angle hero shot；"
            "column corridor depth perspective；"
            "battle formation diagonal across frame；"
            "movement：slow epic crane over columns、cape billow hoplite。"
        ),
        "lighting_color": (
            "主光：hard Mediterranean sun 顶光或侧光；"
            "室内：torch warm + marble bounce cool；"
            "神迹：divine cloud light shaft from above；"
            "禁忌：cyber neon、flat LED office、East Asian palace red only。"
        ),
        "palette_strategy": (
            "主调：大理石白、爱琴海蓝、青铜、沙金、史诗云白；"
            "armor bronze highlight vs marble cool shadow；"
            "肤色 sun bronzed muscular 非 pale glamour；"
            "battle 场景 dust gold accent。"
        ),
        "atmosphere": (
            "epic、fate、gods among men、heroic destiny；"
            "海风、尘土战场、神谕云（视觉：cloud wrap、heat haze）；"
            "mythic scale 非 documentary neutral；"
            "brotherhood in battle 与 divine intervention 并存。"
        ),
        "materials": (
            "marble column、bronze hoplite armor、linen toga、"
            "laurel wreath、sandstone cliff、olive tree；"
            "忌 glass skyscraper、synthetic sportswear、anime cel。"
        ),
        "quality": (
            "史诗院线 35mm grade 级：armor specular、marble grain readable；"
            "dust in air atmospheric；"
            "4K theatrical，thumbnail 可辨 hoplite silhouette 与 temple scale。"
        ),
        "taboos": (
            "cyber futuristic、East Asian palace dominant、cartoon anime、"
            "modern urban streetwear、horror sick green。"
        ),
        "characters_zh": (
            "古希腊铠甲 hoplite、月桂冠 laurel crown；"
            "肌肉英雄 Mediterranean sun bronzed skin；"
            "神祇白袍 gold accent 或战士血污 battle；"
            "姿态 heroic statue-like 或 battle charge。"
        ),
        "characters_en": (
            "Greek mythology film hero bronze hoplite armor laurel wreath, "
            "muscular epic warrior Mediterranean sun bronzed skin, "
            "Parthenon temple background heroic composition, "
            "historical fantasy epic cinema presence dust in air"
        ),
        "scenes_zh": (
            "帕特农大理石柱、爱琴海悬崖远景、"
            "奥林匹斯史诗云、大理石庭院、"
            "古希腊集市 bazaar dust。"
        ),
        "scenes_en": (
            "ancient Greek temple Parthenon marble columns, Aegean sea cliff vista epic, "
            "Mount Olympus divine clouds light shaft, marble column courtyard hoplite formation, "
            "Mediterranean heat haze heroic wide landscape"
        ),
        "colors": "大理石白, 爱琴海蓝, 青铜, 沙金, 史诗云白, 橄榄绿, 尘土褐",
        "image_prompt": (
            "Greek mythology epic film bronze hoplite warrior, marble temple Parthenon background, "
            "harsh Mediterranean sunlight Aegean sea vista, epic historical fantasy cinematography, "
            "dust in air heroic composition Ridley Scott 300 inspired, 4k"
        ),
        "video_prompt": (
            "slow epic crane over temple columns marble, Mediterranean heat haze drift, "
            "cape billow hoplite formation march, divine cloud light shaft descend, "
            "mythic battle atmosphere dust particles"
        ),
        "references": [
            "300 (2006)",
            "Troy (2004)",
            "Immortals (2011)",
        ],
    },
    "guoman_2d_illustration": {
        "summary": '国漫二维插画：国产网络漫画与动画宣传图美学，介于日系与本土之间的线条与配色。热血、修仙、都市异能并存。',
        "category": '国漫二维插画',
        "artist_refs": '《一人之下》《全职高手》宣传、《斗破苍穹》插画',
        "era_texture": '2015–2025 国漫崛起期',
        "line_control": '数码勾线+ selective 厚涂',
        "lighting_color": '戏剧主光+特效 glow',
        "palette_strategy": '高饱和+金属色法术',
        "atmosphere": '热血、升级、少年向',
        "materials": '数码笔触、粒子特效、服饰纹样',
        "quality": '宣传图级，平台封面',
        "taboos": '纯日系无本土元素, 3D, 低完成度',
        "characters_zh": '现代校服或古风劲装，发型杀马特到精致皆有。武器与法术同框。',
        "characters_en": 'Chinese donghua illustration character, dynamic martial arts pose, modern or xianxia outfit, energy aura effects, promotional key visual style',
        "scenes_zh": '都市天台对决、宗门大殿、游戏厅异能。',
        "scenes_en": 'Chinese webtoon rooftop battle, sect hall fantasy interior, urban supernatural showdown, energy blast background',
        "colors": '法术金, 热血红, 深靛, 电蓝, 肤自然',
        "image_prompt": 'Chinese donghua 2D illustration, dynamic martial arts hero, vibrant energy effects, promotional anime key visual, detailed costume patterns, dramatic lighting glow, native Chinese webcomic aesthetic, high saturation, 4k',
        "video_prompt": 'energy aura charge up, hair and cloth whip in power surge, camera orbit martial arts pose, spell particle burst, donghua action motion',
        "references": [
        '一人之下',
        '全职高手',
        '斗破苍穹',
        '魔道祖师',
        ],
    },
    "hk_90s_film": {
        "summary": (
            "90年代港片风格：以 1989–1999 香港电影黄金期（王家卫《重庆森林》《堕落天使》、"
            "刘伟强《无间道》、杜琪峰黑帮片、关锦鹏文艺片）为基准，呈现霓虹旺角、"
            "手持 gritty 与廉价旅馆绿并存的「urban night romance + danger」视觉语法。"
            "人物以风衣墨镜、双枪或烟、港式发型为核心；"
            "场景强调旺角霓虹、重庆大厦走廊、码头雨夜、茶餐厅荧光灯。"
            "整体为 live-action 35mm anamorphic grain cinema，偏红绿霓虹+烟灰 LUT，"
            "可选王家卫 step-print，绝不做古装中国、北欧 clean 或 moe anime。"
            "适合港式警匪、都市浪漫、黑帮叙事 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 90年代香港电影（Hong Kong 90s Film Live-Action）",
        "artist_refs": (
            "导演：王家卫、杜琪峰、刘伟强、关锦鹏、吴宇森早期；"
            "作品：《重庆森林》《堕落天使》《无间道》《古惑仔》；"
            "摄影：霓虹 soaked street、handheld gritty、step-print optional；"
            "美学：wide anamorphic framing、cigarette smoke rim、tungsten motel green。"
        ),
        "era_texture": (
            "1989–1999 香港黄金期 35mm grain；"
            "step print stutter optional Wong Kar-wai mood；"
            "tile motel、neon tube、rain mac texture；"
            "digital 须 emulate film grain 非 clean smartphone night。"
        ),
        "line_control": (
            "构图宽银幕 anamorphic 或手持 gritty follow；"
            "neon alley depth with figure silhouette；"
            "Chungking Mansions corridor claustrophobic；"
            "movement：step printed slow walk、handheld alley chase。"
        ),
        "lighting_color": (
            "主光：霓虹红绿+钨丝旅馆绿；"
            "雨夜：wet surface reflection multiply neon；"
            "香烟 smoke rim light on face；"
            "禁忌：flat daylight nordic、palace candle only、anime flat cel。"
        ),
        "palette_strategy": (
            "主调：霓虹红、霓虹绿、烟灰、雨夜黑、钨黄；"
            "high contrast urban night；"
            "肤色 warm under neon mix 非 glamour peach；"
            "romantic scene 可降饱和加 single neon accent。"
        ),
        "atmosphere": (
            "浪漫、危险、都市速度、孤独与江湖义气；"
            "霓虹嗡鸣、雨声、茶餐厅碟碰撞（视觉：smoke drift、neon flicker）；"
            "Wong Kar-wai melancholy 与 gangster tension 可并存；"
            "非 epic blockbuster daylight only。"
        ),
        "materials": (
            "tile motel wall、neon tube sign、rain mac fabric、"
            "cha chaan teng fluorescent、dock wet concrete、"
            "trench coat leather、双枪 metal glint；"
            "忌 ancient palace silk、clean nordic wood、cartoon。"
        ),
        "quality": (
            "港片黄金期 35mm grain 还原级；"
            "neon reflection on wet pavement readable；"
            "4K with grain，thumbnail 可辨 Mong Kok neon 与 trench coat silhouette。"
        ),
        "taboos": (
            "ancient China palace dominant、clean Nordic minimal、"
            "moe anime、epic desert golden hour only、horror sick green。"
        ),
        "characters_zh": (
            "风衣、墨镜、双枪或烟；"
            "港式发型 90s layered 或 slick back；"
            "gangster 或 romantic loner 表情；"
            "香烟 smoke 与 neon rim 轮廓。"
        ),
        "characters_en": (
            "1990s Hong Kong film character trench coat sunglasses, "
            "neon alley portrait cigarette smoke rim light, "
            "gangster or romantic loner Wong Kar-wai mood, "
            "gritty urban night anamorphic HK aesthetic"
        ),
        "scenes_zh": (
            "旺角霓虹街、重庆大厦走廊、"
            "码头雨夜、茶餐厅荧光灯、"
            "天台孤独俯瞰都市。"
        ),
        "scenes_en": (
            "1990s Hong Kong neon Mong Kok street rain, Chungking Mansions corridor claustrophobic, "
            "rainy dock night wet concrete, cha chaan teng fluorescent interior, "
            "rooftop lonely city overlook HK night"
        ),
        "colors": "霓虹红, 霓虹绿, 烟灰, 雨夜黑, 钨黄, 瓷砖白, 海水灰",
        "image_prompt": (
            "1990s Hong Kong cinema neon soaked Mong Kok street rain cigarette smoke, "
            "wide anamorphic framing Wong Kar-wai mood gritty urban night, "
            "trench coat figure nostalgic HK aesthetic film grain, 4k"
        ),
        "video_prompt": (
            "step printed slow motion walk neon street, neon flicker Hong Kong alley, "
            "cigarette smoke drift rim light, handheld alley follow gritty, "
            "nostalgic HK night motion rain streaks"
        ),
        "references": [
            "重庆森林 (1994)",
            "无间道 (2002)",
            "古惑仔 (1996)",
            "堕落天使 (1995)",
        ],
    },
    "hollywood_bw_classic": {
        "summary": '好莱坞经典黑白：Casablanca、Citizen Kane 式 high key/low key 黑白摄影。Silver screen glamour 与 hard shadow noir。',
        "category": '经典好莱坞黑白',
        "artist_refs": 'Gregg Toland、Film noir DP、Hurrell B&W',
        "era_texture": '1930s–1950s studio black white',
        "line_control": 'deep focus or noir single source',
        "lighting_color": 'Rembrandt or venetian blind stripes',
        "palette_strategy": 'full grey scale mastery',
        "atmosphere": 'romance、 mystery、 timeless',
        "materials": 'satin shine in grey, smoke',
        "quality": 'rich grey separation',
        "taboos": ' color,  modern digital sharp HDR',
        "characters_zh": '礼帽、晚礼服、香烟，经典明星脸。',
        "characters_en": 'classic Hollywood black white star, fedora and evening gown, venetian blind shadow stripes, silver screen glamour portrait',
        "scenes_zh": '机场雾、酒吧钢琴、旋转门、雨街。',
        "scenes_en": 'classic airport fog farewell, piano bar smoke, revolving door hotel, noir rainy street lamp classic cinema',
        "colors": '纯黑白灰, 深黑, 高光银, 中间调丰富',
        "image_prompt": 'classic Hollywood black and white cinematography, venetian blind shadow stripes, silver screen glamour portrait, deep focus composition, film noir atmosphere, rich grey tones, timeless 1940s cinema aesthetic, 4k',
        "video_prompt": 'venetian blind shadow sweep, slow push classic portrait, cigarette smoke curl grey tones, noir piano bar atmosphere, timeless black white motion',
        "references": [
        'Casablanca (1942)',
        'Citizen Kane (1941)',
        'The Maltese Falcon (1941)',
        ],
    },
    "horror_film": {
        "summary": (
            "恐怖电影风格：以 contemporary horror franchise 高峰（James Wan《招魂》、"
            "Ari Aster《遗传厄运》、Roger Deakins horror 段落）为基准，呈现低键单光源、"
            "jump scare 留白与孤立主体并存的「dread + isolation + uncanny」视觉语法。"
            "人物以受害者半脸阴影、背景模糊 antagonist、背对镜头为核心；"
            "场景强调废弃医院、地下室灯泡闪烁、森林夜雾、镜中异常。"
            "整体为 live-action clean digital dark detail cinema，偏 desaturate + sick green/cold blue LUT，"
            "blood minimal until needed，绝不做 comedy bright、romance soft glow 或 cartoon。"
            "适合恐怖惊悚、超自然恐惧 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 恐怖电影（Horror Film Cinematography Live-Action）",
        "artist_refs": (
            "导演：James Wan、Ari Aster、Mike Flanagan；"
            "摄影：Roger Deakins horror、modern horror DP craft；"
            "作品：《招魂》《遗传厄运》《它跟随》《关灯后》；"
            "美学：low key single source、negative space threat、"
            "face half black、flicker bulb、isolated corridor。"
        ),
        "era_texture": (
            "contemporary horror franchise digital dark detail；"
            "peeling paint、fog particle、flicker bulb strobe readable；"
            "shadow crush 但保留 eye highlight；"
            "digital 须 preserve dark shadow detail 非 muddy black。"
        ),
        "line_control": (
            "构图 negative space threat，主体 isolated small in frame；"
            "corridor vanishing point dolly dread build；"
            "mirror frame uncanny reflection offset；"
            "movement：slow corridor dolly、shadow figure edge of frame。"
        ),
        "lighting_color": (
            "主光：single source low key，面部半黑；"
            "accent：sick green fluorescent 或 cold blue moon；"
            "flicker bulb strobe irregular；"
            "禁忌：romance soft glow fill、bright comedy even light、neon cyber pop。"
        ),
        "palette_strategy": (
            "主调：死黑、病绿、冷蓝、血红点缀、灰墙；"
            "desaturate base + sick/cold accent；"
            "肤色 pale terrified 非 glamour；"
            "blood red 仅叙事需要时点缀。"
        ),
        "atmosphere": (
            "dread、isolation、uncanny、anticipation of reveal；"
            "呼吸雾、脚步回声、灯泡闪烁（视觉：flicker strobe、fog breath）；"
            "jump scare 留白 negative space 是核心；"
            "非 gore splatter dominant（除非子类型标注）。"
        ),
        "materials": (
            "剥落墙漆、闪烁灯泡、雾、"
            "生锈铁门、潮湿地下室、破碎镜子；"
            "忌 pastel romance fabric、neon cyber、cartoon cel。"
        ),
        "quality": (
            "现代恐怖院线级：dark detail readable、skin pore in shadow；"
            "flicker 与 fog particle sharp；"
            "4K clean dark，thumbnail 可辨 corridor dread 与 half-face shadow。"
        ),
        "taboos": (
            "comedy bright even light、romance soft glow、cartoon anime、"
            "epic golden hour warm only、pastel kawaii。"
        ),
        "characters_zh": (
            "受害者 terrified 半脸阴影；"
            "阴影中 antagonist 背景 blur 或 silhouette；"
            "背对镜头 isolated posture；"
            "睡衣或日常服 disheveled。"
        ),
        "characters_en": (
            "horror film victim half face in shadow terrified expression, "
            "ominous figure background blur silhouette, isolated dark corridor presence, "
            "modern horror movie aesthetic sick green grade, low key single light"
        ),
        "scenes_zh": (
            "废弃医院走廊、地下室单灯泡闪烁、"
            "森林夜雾、镜中异常反射、"
            "空荡儿童房 night。"
        ),
        "scenes_en": (
            "abandoned hospital corridor vanishing point dread, basement single bulb flicker, "
            "fog forest night isolated figure, mirror uncanny reflection offset horror, "
            "empty child bedroom night negative space threat"
        ),
        "colors": "死黑, 病绿, 冷蓝, 血红点缀, 灰墙, 霉绿, 月光青",
        "image_prompt": (
            "horror film cinematography low key single light source, "
            "isolated figure dark corridor sick green color grade, "
            "ominous negative space flickering bulb, terrifying atmosphere, "
            "modern horror movie aesthetic James Wan inspired, 4k dark detail"
        ),
        "video_prompt": (
            "slow corridor dolly dread build, flicker bulb strobe irregular, "
            "shadow figure pass edge of frame, breath fog in cold air, "
            "horror suspense motion without comedy beat"
        ),
        "references": [
            "The Conjuring (2013)",
            "Hereditary (2018)",
            "It Follows (2014)",
        ],
    },
    "hq_2d_shonen_anime": {
        "summary": '高质量二维少年动漫：TV与剧场版之间，精线、渐变阴影与特效作画。热血战斗、体育、冒险的标准美学。',
        "category": '二维少年动漫高精',
        "artist_refs": 'ufotable、MAPPA、sakuga 社区',
        "era_texture": '2015–2025 TV anime peak production',
        "line_control": '细线+ selective 粗线强调',
        "lighting_color": '多层赛璐璐+ glow 特效',
        "palette_strategy": '角色固有色+背景景深降饱和',
        "atmosphere": '热血、友情、胜利',
        "materials": 'anime hair highlight bands, impact frames',
        "quality": 'sakuga moment freeze worthy',
        "taboos": ' static low fps,  western comic,  chibi only',
        "characters_zh": '少年主角、 rival、 mentor，战损与汗。',
        "characters_en": 'high quality shonen anime character, dynamic battle pose, detailed cel shading, wind swept spiky hair, intense determined eyes, aura effects',
        "scenes_zh": '竞技场、学校屋顶、异世界战场。',
        "scenes_en": 'shonen anime stadium battle, school rooftop sunset duel, otherworld crater battlefield, speed line impact background',
        "colors": '热血橙, 深靛, 肤色 peach, 特效白, 阴影蓝紫',
        "image_prompt": 'high quality 2D shonen anime, detailed cel shading, dynamic action pose, wind swept hair, intense eyes, sakuga level effects, vibrant colors with depth background, ufotable inspired lighting, anime key visual, 4k',
        "video_prompt": 'impact frame flash, speed lines burst, hair cloth violent motion, aura charge explosion, shonen battle sakuga timing',
        "references": [
        '鬼灭之刃',
        '咒术回战',
        'My Hero Academia',
        'Haikyu!!',
        ],
    },
    "hq_animation_render": {
        "summary": '高质量动画渲染：2D/3D不限，强调 final composite 级完成度。适合 trailer still 与 premium MV 帧。',
        "category": '高精动画渲染',
        "artist_refs": 'Disney feature、Arcane finals、日本剧场版',
        "era_texture": 'contemporary premium animation output',
        "line_control": 'style-consistent edge treatment',
        "lighting_color": 'cinematic 3-point adapted',
        "palette_strategy": 'color script locked per sequence',
        "atmosphere": 'premium、 emotional peak',
        "materials": 'full pipeline materials resolved',
        "quality": 'theatrical still frame',
        "taboos": ' rough concept,  inconsistent style frames',
        "characters_zh": '剧场版级细腻表情， tears and sweat rendered。',
        "characters_en": 'high quality animation render character, theatrical detail eyes, emotional tear highlight, premium cloth hair simulation, cinematic hero pose',
        "scenes_zh": ' climax environment fully lit， particles volumetric。',
        "scenes_en": 'premium animated film environment, volumetric god rays, fully composited background, theatrical climax scene atmosphere',
        "colors": '序列锁定色, 高光纯, 阴影通透',
        "image_prompt": 'high quality animation render, theatrical lighting and composition, premium character detail, volumetric atmosphere, fully composited environment, emotional cinematic peak moment, feature animation quality, 4k',
        "video_prompt": 'theatrical camera crane emotional peak, volumetric light sweep, premium hair cloth simulation, climax animation motion blur stylized',
        "references": [
        'Your Name climax scenes',
        'Spider-Verse finals',
        'Frozen 2 Elsa sequences',
        ],
    },
    "industrial_film": {
        "summary": (
            "工业电影风格：以 20–21 世纪工业文明纪实（Joris Ivens 工业纪录片、"
            "王兵《铁西区》、东北工业摄影、《摩登时代》）为基准，呈现工厂烟囱、"
            "钢铁工人与 monumental geometry 并存的「labor dignity + heavy history」视觉语法。"
            "人物以工人头盔、工装、煤灰脸与集体列队为核心；"
            "场景强调高炉、流水线火花、铁路调车场、废弃工厂锈教堂。"
            "整体为 live-action documentary sharp grain cinema，偏锈橙+钢灰+煤黑 LUT，"
            "绝不做 fantasy、pastel romance 或 clean tech white only 主导。"
            "适合工业纪实、劳动史诗、后工业废墟 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 工业纪实电影（Industrial Film Documentary Live-Action）",
        "artist_refs": (
            "导演/摄影：Joris Ivens、王兵《铁西区》；"
            "参照：《摩登时代》、东北工业摄影纪实；"
            "美学：monumental factory geometry、blast furnace glow、"
            "documentary labor portrait、overcast or furnace orange light。"
        ),
        "era_texture": (
            "20–21 世纪工业文明记录 documentary sharp grain；"
            "steel rust、steam、slag、brick texture readable；"
            "coal dust on skin、oil smear on metal；"
            "digital 须 emulate documentary grain 非 clean commercial polish。"
        ),
        "line_control": (
            "构图 monumental geometry：crane over factory yard；"
            "assembly line diagonal depth；"
            "worker portrait against blast furnace glow；"
            "movement：slow pan rust cathedral、steam vent blast。"
        ),
        "lighting_color": (
            "主光：overcast industrial yard 或 furnace orange glow；"
            "室内：hard factory lamp + window dust beam；"
            "night：furnace red vs steel blue shadow；"
            "禁忌：pastel romance soft glow、clean tech white only、fantasy magic light。"
        ),
        "palette_strategy": (
            "主调：铁锈橙、钢灰、煤黑、蒸白、炉红；"
            "rust orange + steel grey anchor；"
            "肤色劳作红晕煤灰 非 glamour；"
            "废弃工厂可加 cool blue rust contrast。"
        ),
        "atmosphere": (
            "heavy、labor、history、industrial sublime；"
            "蒸汽喷发、火花飞溅、火车调车（视觉：steam blast、spark shower）；"
            "documentary dignity 非 action blockbuster；"
            "后工业废墟 melancholy 可并存。"
        ),
        "materials": (
            "steel beam、steam pipe、coal pile、"
            "hard hat、boiler suit canvas、rust metal、"
            "brick chimney、railway track；"
            "忌 silk palace、glass futurism office、pastel fabric。"
        ),
        "quality": (
            "工业纪实院线级：metal specular、steam diffusion readable；"
            "rust texture macro detail；"
            "4K documentary grain，thumbnail 可辨 furnace glow 与 worker silhouette。"
        ),
        "taboos": (
            "fantasy magic、pastel romance、clean tech white only dominant、"
            "palace costume、anime cartoon、cyber neon。"
        ),
        "characters_zh": (
            "工人头盔、工装、煤灰脸；"
            "集体列队或单人劳作 portrait；"
            "姿态有力面向机器或镜头；"
            "汗渍油污真实 非明星 glamour。"
        ),
        "characters_en": (
            "industrial film worker hard hat boiler suit, coal dust face documentary labor portrait, "
            "factory floor blast furnace glow silhouette, monumental steel mill presence, "
            "labor dignity cinematography rust steam atmosphere"
        ),
        "scenes_zh": (
            "高炉炉火橙光、流水线火花飞溅、"
            "铁路调车场、废弃工厂锈教堂、"
            "烟囱烟雾天际线。"
        ),
        "scenes_en": (
            "steel mill blast furnace orange glow worker silhouette, assembly line sparks shower, "
            "railway shunting yard overcast industrial, abandoned factory rust cathedral slow pan, "
            "factory chimney smoke skyline monumental geometry"
        ),
        "colors": "铁锈橙, 钢灰, 煤黑, 蒸白, 炉红, 砖褐, 阴天灰",
        "image_prompt": (
            "industrial film aesthetic steel mill blast furnace glow, worker hard hat silhouette, "
            "rust steam atmosphere monumental factory geometry, documentary grain labor dignity, "
            "Joris Ivens Wang Bing inspired cinematography, 4k"
        ),
        "video_prompt": (
            "steam vent blast rhythmic pulse, sparks shower assembly line, "
            "slow pan rust cathedral abandoned factory, furnace glow flicker orange, "
            "industrial documentary motion heavy atmosphere"
        ),
        "references": [
            "铁西区 (2003)",
            "Modern Times (1936)",
            "工业摄影纪实",
        ],
    },
    "jp_bw_film_photo": {
        "summary": (
            "日本黑白胶片摄影风格：以 1950s–1970s 日本映画黄金（小津安二郎《东京物语》、"
            "沟口健二《雨月物语》、木下惠介家庭剧）与森山大道 street B&W 摄影为基准，"
            "呈现 tatami 地平线低角构图、障子柔光与和室静默人脸并存的 "
            "「mono no aware + formal ritual」视觉语法。"
            "人物以和服、战后西装、鞠躬礼仪与 family portrait 平静表情为核心；"
            "场景强调和室低角、庭石枯山水、乡间小站月台、神社石阶。"
            "整体为 live-action 35mm B&W film photography，偏 full grey scale 与纸白高光 LUT，"
            "绝不做 color pop、动作少年番或霓虹都市主导。"
            "适合日式家庭伦理、战后叙事、静寂美学 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 日本黑白胶片（Japanese Black White Film Photography Live-Action）",
        "artist_refs": (
            "导演：小津安二郎、沟口健二、木下惠介；"
            "摄影：厚木太郎、宫川一夫；街头：森山大道、东松照明；"
            "作品：《东京物语》《晚春》《雨月物语》《楢山节考》；"
            "美学：low tatami camera height、horizon line at mat edge、"
            "static family tableau、shoji diffused window light、B&W tonal separation。"
        ),
        "era_texture": (
            "1950s–1970s 日本映画 35mm B&W fine grain；"
            "纸白 highlight 不刺眼，shadow 丰富中间调；"
            "木 grain、棉布 kimono weave readable；"
            "digital monochrome 须 emulate film tonal curve 非 flat smartphone grey。"
        ),
        "line_control": (
            "构图低机位 tatami 地平线，人物跪坐或端坐；"
            "family group symmetric or triangular tableau；"
            "庭院用 fixed wide，人物小置于 frame 一角；"
            "movement 极少：static hold、gentle bow、障子光影 shift。"
        ),
        "lighting_color": (
            "主光：障子窗柔光 diffuse，面部无硬 shadow；"
            "室外：overcast soft 或侧光庭石；"
            "full grey scale，纸白、墨黑、木灰中间调丰富；"
            "禁忌：color pop、neon rim、HDR hard contrast、action flash。"
        ),
        "palette_strategy": (
            "主调：墨黑、纸白、木灰、中间调丰富；"
            "和服纹样以灰阶纹理呈现非彩色；"
            "肤色柔和无 glamour contrast；"
            "户外场景保留 sky grey 与 stone texture separation。"
        ),
        "atmosphere": (
            "静寂、物哀、family ritual、战后克制与世代隔阂；"
            "障子光影、庭石雨痕、火车到站铃（视觉：static platform、bow motion）；"
            "quiet pace 非 melodrama 夸张；"
            "formal distance 与温情并存。"
        ),
        "materials": (
            "障子纸、木 grain tatami、棉布和服、"
            "石阶青苔、铁轨、陶罐、茶碗；"
            "忌 neon sign、plastic modern、sportswear logo。"
        ),
        "quality": (
            "经典日本映画 B&W 还原级：fine grain、tonal separation readable；"
            "fabric weave 与 wood grain 在灰阶中可辨；"
            "4K scan 感，thumbnail 可辨 tatami line 与 family composition。"
        ),
        "taboos": (
            "color pop dominant、action shonen、neon city night、"
            "horror gore、modern cyber、3D cartoon。"
        ),
        "characters_zh": (
            "和服正装、战后西装、鞠躬礼仪姿态；"
            "family portrait 平静表情，少夸张表情；"
            "老幼三代同框 tableau；"
            "街头 B&W 可森山大道式 dynamic blur（子类型标注）。"
        ),
        "characters_en": (
            "Japanese black white film character, kimono or postwar suit formal, "
            "bowing ritual posture calm expression, Ozu family portrait tableau, "
            "low tatami angle composition, shoji soft window light, "
            "mono no aware monochrome cinema presence"
        ),
        "scenes_zh": (
            "和室低角 tatami 线、枯山水庭石、"
            "乡间铁路小站月台、神社石阶、"
            "战后街道 modest shopfront monochrome。"
        ),
        "scenes_en": (
            "Japanese tatami room low Ozu angle horizon line, zen garden rocks moss, "
            "rural train station platform quiet, shrine stone steps monochrome, "
            "postwar street modest storefront B&W film grain"
        ),
        "colors": "墨黑, 纸白, 木灰, 中间调丰富, 石青灰, 苔绿灰阶",
        "image_prompt": (
            "Japanese black white film photography, Ozu low tatami angle horizon, "
            "shoji window soft diffused light, family in traditional room tableau, "
            "zen garden monochrome fine grain, quiet mono no aware atmosphere, "
            "classic Japanese cinema tonal separation, 35mm B&W, 4k"
        ),
        "video_prompt": (
            "static tatami line composition hold, gentle formal bow motion slow, "
            "shoji shadow shift afternoon, rural train arrive platform quiet, "
            "contemplative Japanese B&W film pace minimal movement"
        ),
        "references": [
            "東京物語 (1953)",
            "雨月物語 (1953)",
            "森山大道 photography",
        ],
    },
    "jp_flat_illustration": {
        "summary": '日式扁平插画：无透视或等距，有限色板与几何形。适合App、杂志与 lifestyle branding。',
        "category": '日式扁平插画',
        "artist_refs": 'Noritake、Japanese editorial illustrators、Mid-century J-design',
        "era_texture": '当代日本 editorial flat',
        "line_control": 'uniform thin line optional',
        "lighting_color": '无阴影或单阴影块',
        "palette_strategy": '3–4色 strict',
        "atmosphere": 'calm、 witty、 design forward',
        "materials": 'flat fill only',
        "quality": 'vector clean scalable',
        "taboos": ' gradient heavy,  3D,  photoreal',
        "characters_zh": '简笔人，圆头，日常场景。',
        "characters_en": 'Japanese flat illustration character, minimal geometric body, limited color palette, editorial cute figure, simple daily life pose',
        "scenes_zh": '咖啡馆、电车、办公室小景。',
        "scenes_en": 'flat Tokyo cafe interior, geometric train commuter scene, isometric office desk, minimal urban Japan illustration',
        "colors": '米白, 靛蓝, 珊瑚, 黑线, 灰绿',
        "image_prompt": 'Japanese flat illustration, minimal geometric shapes, limited color palette, editorial lifestyle scene, clean vector aesthetic, witty calm composition, modern Tokyo daily life, scalable design quality, 4k',
        "video_prompt": 'flat shape slide transition, minimal character walk cycle, color block scene swap, gentle editorial motion graphics, calm Japanese flat animation',
        "references": [
        'Noritake illustrations',
        'POPEYE magazine art',
        'Mid-century Japanese graphic design',
        ],
    },
    "jp_life_natural": {
        "summary": (
            "日式生活自然风格：以 2000s–2020s 日本人文主义电影（是枝裕和《步履不停》《小偷家族》"
            "《完美日子》、河濑直美纪录片、荻上直子日常美学）为基准，"
            "呈现窗光、植物、木器与 quiet domestic moments 并存的「everyday sacred + "
            "gentle desaturation」视觉语法。"
            "人物以家庭成员、老人、孩子为主，自然妆发；场景强调厨房晨光、缘侧、"
            "便利店雨夜入口、神社旁小路。整体为 live-action soft digital cinema，"
            "偏 desaturated gentle warm LUT，绝不做 action spectacle、霓虹赛博或 epic VFX。"
            "适合家庭伦理、治愈日常、日本生活流 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 日式生活自然主义（Japanese Life Naturalist Cinema Live-Action）",
        "artist_refs": (
            "导演：是枝裕和、河濑直美、荻上直子、三宅喜重；"
            "作品：《步履不停》《小偷家族》《完美日子》《蒲公英》《萌之朱雀》；"
            "美学：eye level static、slow pan、natural window light、"
            "overcast soft fill、domestic framing、stillness as emotion。"
        ),
        "era_texture": (
            "2000s–2020s Japanese humanist digital cinema，soft highlight rolloff；"
            "轻微 desaturation，木器与植物绿为色彩锚点；"
            "厨房 steam、米饭水汽、雨声场景（视觉：condensation、wet stone）；"
            "no glamour skin smoothing，保留毛孔与岁月纹。"
        ),
        "line_control": (
            "构图 eye level 尊重人物，static hold 或 imperceptible slow pan；"
            "frame 内留白给环境声空间（empty chair、distant corridor）；"
            "人物可背对镜头从事家务；"
            "少 dramatic low angle hero，emotion 靠 micro gesture（洗手、摆碗）。"
        ),
        "lighting_color": (
            "主光：北向窗光+ overcast sky bounce，soft shadow；"
            "室内：钨灯暖点缀但不过饱和；"
            "雨景：diffused grey with specular on asphalt；"
            "禁忌：hard noir、neon sign dominant、studio butterfly glamour。"
        ),
        "palette_strategy": (
            "主调：木温、灰绿植物、米白、雨灰、柔阳金；"
            "肤色自然偏暖黄，老人斑与皱纹保留；"
            "食物与陶器作 small color accent；"
            "全片避免 high-sat candy 或 cyber palette。"
        ),
        "atmosphere": (
            "quiet、tender、everyday sacred、家庭沉默中的爱；"
            "煮饭蒸汽、晾衣杆、便利店自动门、"
            "神社风铃、自行车经过（视觉：slow daily ritual）；"
            "低 drama 高真实温柔，非 melodrama 大吵。"
        ),
        "materials": (
            "木纹餐桌、亚麻、陶碗、电饭煲、盆栽、"
            "湿雨伞、便利店透明伞、榻榻米、磨砂玻璃；"
            "忌 chrome cyber、leather action hero、palace gold。"
        ),
        "quality": (
            "艺术院线人文片级：soft digital clean，texture of wood and fabric readable；"
            "thumbnail 传达「家的温度」与季节感。"
        ),
        "taboos": (
            "action explosion、neon cyberpunk、epic fantasy VFX、"
            "glamour beauty commercial、horror gore、anime big-eye stylization。"
        ),
        "characters_zh": (
            "日本家庭日常：老人、父母、孩子，家居服与便服；"
            "温柔疲惫微笑、做饭洗碗动作；"
            "便利店店员、邻居老人作群像；"
            "表情克制，情绪在眼神与停顿。"
        ),
        "characters_en": (
            "Japanese naturalist life cinema character, casual home clothing linen, "
            "gentle tired smile domestic presence, soft unretouched face, "
            "elder parent or child everyday moment, Hirokazu Kore-eda Naomi Kawase aesthetic, "
            "quiet humanist portrait"
        ),
        "scenes_zh": (
            "日式厨房晨光、缘侧望庭、便利店雨夜入口、"
            "神社石阶小路、浴室蒸汽、小餐桌便当、社区洗衣场。"
        ),
        "scenes_en": (
            "Japanese home kitchen morning window light, engawa porch garden view, "
            "convenience store rainy entrance automatic door, shrine side stone path, "
            "steam from rice cooker, small dining table domestic still life, "
            "quiet suburban neighborhood walk"
        ),
        "colors": "木温, 灰绿植物, 米白, 雨灰, 柔阳金, 陶土褐, 天空浅灰",
        "image_prompt": (
            "Japanese naturalist life cinema, soft window light kitchen domestic scene, "
            "quiet family everyday moment, gentle desaturated warm colors, "
            "plants and wood textures, Hirokazu Kore-eda Naomi Kawase aesthetic, "
            "tender humanist stillness, unretouched natural faces, 4k"
        ),
        "video_prompt": (
            "slow pan rice cooking steam rise, rain dripping engawa eaves, "
            "quiet walking shrine path, domestic silence hold, "
            "hands washing dishes gentle motion, naturalist life atmosphere"
        ),
        "references": [
            "步履不停 (2008)",
            "Shoplifters (2018)",
            "Perfect Days (2023)",
            "萌之朱雀 (1997)",
        ],
    },
    "jp_youth_film": {
        "summary": (
            "日式青春胶片风格：以 1990s–2010s 日本青春电影（岩井俊二《Love Letter》《关于莉莉周的一切》、"
            "《四月物语》《花与爱丽丝》、是枝裕和《距离》、松田龙平世代）摄影美学为基准，"
            "呈现强逆光 haze、天空蓝、制服海军蓝与 tender heartache 并存的「nostalgic adolescence + photochemical warmth」视觉语法。"
            "人物以高中制服、短发/自然长发、书包与侧脸望天为核心；场景强调屋顶、海堤、"
            "樱花隧道、 rural 月台与自行车 seaside wind。整体为 live-action 胶片感电影摄影，"
            "偏 soft flare + fine film grain LUT，绝不做 horror dark、epic war 或 corporate sleek。"
            "适合日系青春、纯爱、成长伤痛向 AIGC 短剧的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 日式青春胶片（Japanese Youth Film Grain Live-Action）",
        "artist_refs": (
            "导演/摄影参照：岩井俊二（Shunji Iwai）、是枝裕和早期、行定勋、"
            "《Love Letter》《All About Lily Chou-Chou》《Hana and Alice》《April Story》；"
            "美学：强 backlight haze、handheld soft 或 locked poetic、"
            "Kodak/Fuji film stock emulation、school uniform navy + sky blue contrast。"
        ),
        "era_texture": (
            "1990s–2010s Japanese youth cinema，35mm film grain visible but fine（非 heavy 16mm noise）；"
            "highlight soft rolloff + gentle lens flare acceptable；"
            " daylight exterior 高 key blue sky；interior classroom chalk dust haze；"
            "optional slight vignette 与 warm shadow toe（photochemical feel）；"
            "digital capture 须 emulate film：soft halation、muted highlight、subtle grain overlay。"
        ),
        "line_control": (
            "构图以留白 sky/sea 与 small figure 对照为主（人物占 frame 1/3 或 less）；"
            "profile silhouette against bright sky 或 cherry tunnel；"
            "handheld gentle sway 或 locked wide poetic；"
            "letter/ diary/ CD player 等 props 可作 foreground bokeh；"
            "少用手持 chaos，emotion 靠 stillness 与 wind movement。"
        ),
        "lighting_color": (
            "主光：强逆光/侧逆光（sun or window）制造 haze bloom 与 rim；"
            "辅光：soft bounce fill 保留肤色 warmth；"
            "室内：窗光条纹 + chalkboard grey-green；"
            "黄昏：golden hour warm + long shadow on embankment；"
            "禁忌：hard noir、flat fluorescent office、cyber neon。"
        ),
        "palette_strategy": (
            "主调：天空蓝、制服海军蓝、樱花粉、阳光白、海青；"
            "胶片：shadow 略 warm green/cyan，highlight soft cream；"
            "肤色：youthful natural，minimal makeup；"
            "叙事用色：回忆/信笺场景可 sepia insert；失落场景降 saturation 保留 blue sky anchor。"
        ),
        "atmosphere": (
            "nostalgic、fragile、first love、unspoken words 与 seasonal passing 并存；"
            "wind in hair/skirt、train depart、chalk dust、CD player headphones、"
            "letter folding（视觉：petals/seagull/cloud movement）；"
            "quiet melancholy 非 melodrama scream；"
            "夏天与青春 fleeting 感。"
        ),
        "materials": (
            "服饰：高中制服（海军蓝 blazer / sailor / 立领）、"
            "white shirt、striped tie、pleated skirt、loose socks、"
            "school bag leather/nylon、white sneakers；"
            "道具：自行车、letter envelope、CD player、earphones、"
            "chalk、library book、film camera、bus ticket；"
            "环境：tin roof、chain link fence、seaside concrete embankment、"
            "rural train platform、classroom window row、cherry trees tunnel。"
        ),
        "quality": (
            "film emulation cinematography，fine grain + soft highlight；"
            "适合 9:16 竖版角色卡与 16:9 widescreen sky/sea；"
            "lens flare 与 halation 可控（非 anamorphic sci-fi flare）；"
            "live-action realistic youth，非 anime、非 idol MV 过度磨皮。"
        ),
        "taboos": (
            "horror dark、gore、epic war、battlefield；"
            "corporate sleek skyscraper、luxury fashion editorial；"
            "K-pop glass skin、Chinese palace、cyberpunk neon；"
            "heavy HDR crunchy contrast、TikTok beauty filter；"
            "watermark、字幕条、多格漫画分镜（单图角色卡时）。"
        ),
        "characters_zh": (
            "【面部】少年/少女 natural face，minimal makeup，"
            "眼神 shy、 distant gaze、 tear held back；"
            "侧脸望天/望海为 signature pose。"
            "【发型】短发自然、或黑长直/微卷，wind-blown strands；"
            "男生：school regulation cut；女生：ribbon/barrette optional。"
            "【服饰】制服完整或 summer short sleeve variant；"
            "书包单肩/双手握把；"
            "手持：信、CD player、自行车 handlebar。"
            "【体态】bicycle ride、platform wait、"
            "rooftop fence lean、cherry path walk slow。"
            "【气质范例】藤井树——quiet longing；"
            "花——eccentric gentle；莲见——fragile observer。"
        ),
        "characters_en": (
            "Japanese youth film grain live-action character, high school uniform navy blazer, "
            "strong blue sky backlight haze and soft lens flare, gentle sidelong gaze nostalgic, "
            "bicycle or seaside embankment wind blown hair, fine 35mm film grain texture, "
            "Shunji Iwai Love Letter aesthetic, tender heartache adolescent mood, "
            "natural skin minimal makeup, cherry blossom or train platform atmosphere, "
            "no anime style, no corporate sleek, highly detailed 4k"
        ),
        "scenes_zh": (
            "【典型环境】学校屋顶 fence + sky、海堤 concrete wind、"
            "樱花隧道 path、 rural 月台、 classroom 窗光排、"
            "图书馆 aisle、自行车 seaside road、"
            "冬日空场 snow optional（仍 soft 非 harsh）。"
            "【构图】small figure + vast sky/sea；"
            "profile silhouette、 cherry tunnel depth、"
            "train leaving platform wide。"
            "【光影】强逆光 haze、golden hour embankment、"
            "classroom window slats、soft overcast still poetic。"
            "【季节】春樱、夏海、秋 wind、冬 quiet——"
            "seasonal nostalgia 为核心。"
        ),
        "scenes_en": (
            "Japanese school rooftop blue sky backlight haze, seaside embankment wind fine film grain, "
            "cherry blossom tunnel path nostalgic, rural train platform farewell wide shot, "
            "classroom window light row soft flare, Shunji Iwai youth film aesthetic, "
            "35mm photochemical warmth, tender heartache atmosphere, "
            "high school uniform silhouette, live-action Japanese coming of age cinematography, 4k"
        ),
        "colors": (
            "主色：天空蓝、制服海军蓝、樱花粉、阳光白、海青；"
            "胶片：shadow warm green/cyan toe、highlight cream soft；"
            "肤色：natural youthful；"
            "叙事：信笺/回忆 sepia insert；失落降饱和保 sky blue"
        ),
        "image_prompt": (
            "Japanese youth film grain live-action cinematography, high school uniform silhouette, "
            "strong blue sky backlight haze and soft lens flare, fine 35mm film grain texture, "
            "seaside embankment breeze or cherry blossom tunnel path, nostalgic tender heartache mood, "
            "Shunji Iwai Love Letter aesthetic, natural adolescent skin minimal makeup, "
            "photochemical warm shadows soft highlight rolloff, "
            "no anime, no horror dark, no corporate sleek, highly detailed 4k vertical 9:16"
        ),
        "video_prompt": (
            "bicycle ride along seaside wind hair and skirt flutter, cherry petals fall slow motion, "
            "train depart platform figure wave, strong backlight haze drift consistent, "
            "fine film grain subtle motion, youth film nostalgic pacing, "
            "classroom window light gentle pan, no shaky action cam"
        ),
        "references": [
            "Love Letter (1995)",
            "All About Lily Chou-Chou (2001)",
            "Hana and Alice (2004)",
            "April Story (1998)",
        ],
    },
    "kdrama_urban_soft": {
        "summary": (
            "韩剧都市柔光风格：以 2016–2024 韩国 tvN/SBS 都市浪漫剧（《鬼怪》《爱的迫降》《金秘书为何那样》"
            "《举重妖精金福珠》《请回答1988》柔光段落、《社内相亲》）摄影美学为基准，"
            "呈现清透亮肤、大型 soft source、奶油色肤色与 pastel 大衣并存的「aspirational romcom + melodrama gloss」视觉语法。"
            "人物以精致韩式妆容、设计师大衣围巾、微卷发型与 romantic lead 表情为核心；"
            "场景强调汉江桥夜景、咖啡店窗、樱花道与 luxury apartment city view。"
            "整体为 live-action 电影级写实摄影，偏 soft beauty lighting + creamy skin LUT，"
            "绝不做 gritty documentary、horror dark 或 ancient war。"
            "适合韩剧都市爱情、浪漫 comedy、melodrama 向 AIGC 短剧的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 韩剧都市柔光（K-Drama Urban Soft Light Live-Action）",
        "artist_refs": (
            "摄影与美术参照：《鬼怪》《爱的迫降》《金秘书为何那样》《举重妖精金福珠》"
            "《她的私生活》《社内相亲》组；"
            "tvN romance peak look、Seoul location（Han River, Garosu-gil, cafe district）；"
            "美学：large soft source + rim、浅景深 portrait、glass skin beauty、"
            "pastel wardrobe styling、night city bokeh golden。"
        ),
        "era_texture": (
            "2016–2024 K-drama peak look，4K clean digital + beauty commercial skin finish；"
            "轻微 soft diffusion/bloom on highlight（非 over-soft 糊片）；"
            "夜景 Seoul bokeh rich、汉江反射 warm-cool mix；"
            "snow/cherry season scenes 带 airborne particle 与 gentle flare；"
            "色彩经 creamy midtone + pastel wardrobe grade，避免 documentary flat desat。"
        ),
        "line_control": (
            "构图以 portrait center 或 rule-of-thirds couple framing 为主；"
            "浅景深 isolating subject，背景 city/cafe bokeh creamy；"
            "情侣：two-shot symmetry 或 walking side-by-side depth；"
            "慢 push-in / slow orbit 营造 romantic tension；"
            "少用手持 gritty，多用 stabilized glide / jib gentle。"
        ),
        "lighting_color": (
            "主光：大型 soft source（softbox/China ball）45° 或 butterfly front，"
            "glass skin even highlight；"
            "轮廓：rim light 分离发丝与大衣 edge；"
            "夜景：practical city light + warm key on face，background blue hour；"
            "室内：cafe window natural + warm interior pendant；"
            "禁忌：hard noir half shadow、flat fluorescent horror、over-HDR crunchy。"
        ),
        "palette_strategy": (
            "主调：奶油肤、粉杏、海军大衣蓝、夜城蓝、暖白 interior；"
            "服色：camel coat、blush pink、cream sweater、navy suit；"
            "肤色：flawless glass skin，lip coral/gloss，brow defined；"
            "叙事用色：conflict 场景略降 warmth； reunion/snow 提 golden sparkle。"
        ),
        "atmosphere": (
            "romantic、glossy、aspirational、comfort fantasy 与 sincere tear 并存；"
            "coffee steam、 cherry drift、snow fall gentle、"
            "Han River wind in scarf hair（视觉：soft particle + bokeh）；"
            "office/cafe 日常亦带 fairytale polish；"
            "melodrama cry 仍保持 beauty lighting（tear track glossy）。"
        ),
        "materials": (
            "服饰：设计师大衣、围巾、针织、西装、高跟鞋/切尔西靴；"
            "配饰：手表、手袋、耳环 subtle sparkle；"
            "环境：glass cafe facade、Han River bridge railing、"
            "cherry blossom street、luxury apartment floor-to-ceiling window、"
            "office glass partition、bookstore aisle；"
            "道具：coffee cup、umbrella pastel、phone、gift box ribbon。"
        ),
        "quality": (
            "4K beauty commercial level skin + fabric detail；"
            "适合 9:16 竖版角色卡与 16:9 city night wide；"
            "shallow DOF portrait standard，bokeh smooth circular；"
            "live-action realistic glamour，非 anime、非 gritty doc。"
        ),
        "taboos": (
            "gritty documentary、horror dark、 slasher blood；"
            "ancient war armor、historical sageuk dirt（除非 hybrid 叙事）；"
            "日系 anime filter、中国古偶 gold rim 主导；"
            "unflattering harsh top light、acne visible macro（除非角色设定）；"
            "watermark、字幕条、多格漫画分镜（单图角色卡时）。"
        ),
        "characters_zh": (
            "【面部】精致韩式妆容：clean brow、soft contour、"
            "gradient lip、coral/blush；"
            "表情：romantic gaze、 shy smile、 tearful glossy cry、"
            "CEO cold face softening——「韩剧标准视觉糖」。"
            "【发型】微卷 lob、空气刘海、或 slick businessman cut；"
            "发色 natural black/brown，highlight subtle。"
            "【服饰】驼色大衣+围巾、海军西装、"
            "粉色针织、运动休闲（金福珠式）；"
            "手持：coffee、phone、umbrella。"
            "【体态】Han River lean on rail、cafe window seat、"
            "snow walk two-shot、office elevator mirror。"
            "【气质范例】鬼怪——lonely immortal warm；"
            "金秘书——competent romantic；福珠——bubbly athletic sweet。"
        ),
        "characters_en": (
            "K-drama urban soft live-action character, flawless glass skin portrait, "
            "designer coat and scarf Seoul fashion styling, romantic lead expression, "
            "large soft beauty lighting with gentle rim, creamy pastel color grade, "
            "Han River night bokeh or cozy cafe window background, "
            "shallow depth of field, tvN Korean drama aesthetic, "
            "aspirational glossy romance, no gritty documentary, highly detailed 4k"
        ),
        "scenes_zh": (
            "【典型环境】汉江桥夜景、咖啡店靠窗、"
            "樱花道 walk、luxury apartment 全景窗、"
            "office 玻璃隔断、书店 aisle、"
            "初雪 street、机场 reunion hall。"
            "【构图】portrait center shallow DOF；"
            "couple two-shot city bokeh background；"
            "wide Han River skyline figure small romantic。"
            "【光影】soft beauty key + rim、"
            "blue hour city + warm face、"
            "cafe window natural backlight halo。"
            "【季节】春樱、夏汉江、秋落叶 pastel、冬初雪 sparkle——"
            "seasonal romance 视觉糖。"
        ),
        "scenes_en": (
            "Han River Seoul night bridge bokeh romantic, cozy cafe window seat soft lighting, "
            "cherry blossom street walk pastel wardrobe, luxury apartment city view night, "
            "K-drama urban soft cinematography, glass skin portrait creamy grade, "
            "large soft source beauty lighting, shallow depth of field, "
            "tvN Korean romance drama aesthetic, aspirational glossy atmosphere, 4k"
        ),
        "colors": (
            "主色：奶油肤、粉杏、海军大衣蓝、夜城蓝、暖白；"
            "点缀：coral lip、camel coat、 cherry pink、 snow sparkle；"
            "肤色：glass skin warm-neutral；"
            "叙事：冲突略降 warmth，重逢/初雪提 golden"
        ),
        "image_prompt": (
            "K-drama urban soft live-action cinematography, flawless glass skin portrait, "
            "designer coat scarf Seoul fashion styling, Han River night city bokeh romantic, "
            "cozy cafe window soft beauty lighting, creamy pastel color grade gentle rim light, "
            "shallow depth of field, tvN Korean romance drama aesthetic, "
            "Goblin Crash Landing style aspirational glossy mood, "
            "no gritty documentary, no anime, highly detailed 4k vertical 9:16"
        ),
        "video_prompt": (
            "slow romantic orbit couple Han River wind scarf flutter, "
            "cherry blossom drift soft, cafe window rain outside gentle, "
            "snow fall sparkle slow motion, glass skin beauty lighting consistent, "
            "K-drama emotional soft pacing, no shaky gritty cam"
        ),
        "references": [
            "Guardian: The Lonely and Great God (2016)",
            "Crash Landing on You (2019)",
            "Business Proposal (2022)",
            "Weightlifting Fairy Kim Bok-joo (2016)",
        ],
    },
    "kr_cold_minimal_film": {
        "summary": (
            "韩国冷淡风电影风格：以 2000s–2020s 韩国作者电影（洪尚秀 awkward conversation、"
            "李沧东《诗》《燃烧》、金基德早期）为基准，呈现 static long take、"
            "overcast flat light 与 mundane interior 并存的「alienation + quiet tension」视觉语法。"
            "人物以普通人脸、烧酒桌 awkward posture 与荧光灯下疲惫为核心；"
            "场景强调小餐馆、河边步道阴天、普通公寓、空教室。"
            "整体为 live-action digital auteur cinema，偏 desaturated grey-green minimal LUT，"
            "绝不做 romcom gloss、epic color 或 action VFX 主导。"
            "适合韩国作者片、阶级张力、日常疏离 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 韩国冷调极简作者电影（Korean Cold Minimal Auteur Film Live-Action）",
        "artist_refs": (
            "导演：洪尚秀、李沧东、金基德早期、张律；"
            "摄影：韩国作者片 digital flat honest 组；"
            "作品：《燃烧》《诗》《海边的一天》洪尚秀系列、《空房间》；"
            "美学：static long take、overcast flat lighting、mundane framing、"
            "awkward sitting distance、fluorescent exhaustion、minimal color blocking。"
        ),
        "era_texture": (
            "2000s–2020s Korean auteur digital，flat honest 无 glamour grade；"
            "overcast sky 或荧光灯 green-grey cast；"
            "混凝土、廉价酒店 wallpaper texture readable；"
            "digital 须 preserve flat realism 非 beauty filter 或 blockbuster teal-orange。"
        ),
        "line_control": (
            "构图 static wide 或 medium，人物偏 frame 边缘 awkward space；"
            "long take composition 少 cut，dialogue 用 two-shot across table；"
            "horizon level，少 dutch angle；"
            "movement 慢：walk along river、pour soju static camera。"
        ),
        "lighting_color": (
            "主光：overcast flat 或 fluorescent overhead，shadow minimal；"
            "室内：cheap hotel green-grey fluorescent；"
            "室外：阴天均匀光，无 magic hour；"
            "禁忌：romcom golden hour gloss、epic sunset、neon cyber、studio glamour。"
        ),
        "palette_strategy": (
            "主调：灰米、冷绿、荧白、混凝土、淡蓝；"
            "desaturated grey-green minimal，accent 极少；"
            "肤色自然偏疲态，无 peach glamour；"
            "情绪高潮仍可 flat 非 sudden saturated burst。"
        ),
        "atmosphere": (
            "alienation、quiet tension、class gap、awkward silence；"
            "烧酒瓶、香烟雾、河水阴天、空教室桌椅（视觉：static hold、distance）；"
            "melodrama restrained 非韩剧高光眼泪特写主导；"
            "existential mundane 是核心情绪符号。"
        ),
        "materials": (
            "烧酒瓶 green glass、混凝土墙、廉价酒店家具、"
            "塑料椅、河边步道地砖、普通公寓 wallpaper；"
            "忌 velvet palace、neon sign、luxury gloss。"
        ),
        "quality": (
            "作者电影 digital honest 级：flat but sharp，texture readable；"
            "fluorescent cast consistent；"
            "4K clean 无 oversharpen，thumbnail 可辨 awkward composition 与 grey palette。"
        ),
        "taboos": (
            "romcom gloss、epic color blockbuster、action VFX、"
            "palace costume drama、neon cyber、Technicolor saturation。"
        ),
        "characters_zh": (
            "普通人脸，无明星 glamour；"
            "awkward sitting posture 烧酒桌、河边长椅；"
            "荧光灯下疲惫、眼神回避；"
            "穿着 mundane 夹克、衬衫、普通外套。"
        ),
        "characters_en": (
            "Korean minimal auteur film character, plain everyday face no glamour, "
            "awkward sitting posture at small restaurant table, "
            "fluorescent lit exhaustion desaturated skin, "
            "Hong Sang-soo Lee Chang-dong framing restraint, mundane wardrobe jacket"
        ),
        "scenes_zh": (
            "小餐馆方桌、阴天河边步道、"
            "普通公寓室内、空教室安静、"
            "廉价酒店走廊荧光灯。"
        ),
        "scenes_en": (
            "Korean small restaurant table two-shot awkward distance, "
            "riverside walking path overcast flat sky, "
            "mundane apartment interior wallpaper, empty classroom quiet desks, "
            "cheap hotel corridor fluorescent green grey"
        ),
        "colors": "灰米, 冷绿, 荧白, 混凝土, 淡蓝, 烧酒瓶绿, 阴天灰",
        "image_prompt": (
            "Korean cold minimal auteur film, overcast flat lighting no glamour, "
            "mundane apartment or restaurant interior, quiet awkward figure at table, "
            "desaturated grey green palette, Hong Sang-soo Lee Chang-dong framing, "
            "fluorescent exhaustion aesthetic, restraint cinematography, 4k digital honest"
        ),
        "video_prompt": (
            "static long take silence hold, soju pour slow no cut, "
            "overcast riverside walk distant figures, fluorescent hum mood, "
            "minimal Korean auteur film motion restrained"
        ),
        "references": [
            "Burning (2018)",
            "Hong Sang-soo films",
            "Poetry (2010)",
        ],
    },
    "minimal_illustration": {
        "summary": '极简插画：少元素、多留白、单一隐喻。国际 editorial 与 mindfulness branding 常用。',
        "category": '极简插画',
        "artist_refs": 'Malika Favre、Noma Bar、Japanese minimal editors',
        "era_texture": 'contemporary global editorial',
        "line_control": 'few strokes maximum',
        "lighting_color": 'none or one shadow shape',
        "palette_strategy": '1–2 colors + negative space',
        "atmosphere": 'clever、 calm、 iconic',
        "materials": 'flat vector',
        "quality": 'icon readable at 64px',
        "taboos": ' clutter,  texture noise,  3D',
        "characters_zh": '符号化人形，一两笔。',
        "characters_en": 'minimal illustration figure, single line face, geometric body, negative space composition, editorial icon character',
        "scenes_zh": '一个对象+大片留白。',
        "scenes_en": 'minimal illustration scene, single object metaphor, vast white negative space, clever visual pun layout',
        "colors": '黑, 白, 单点红或蓝',
        "image_prompt": 'minimal illustration, bold negative space, single metaphor object, limited two color palette, editorial vector aesthetic, clever iconic composition, clean geometric shapes, magazine cover quality, 4k',
        "video_prompt": 'minimal shape morph reveal, negative space slide transition, single color pop accent, calm editorial motion, icon simplicity animation',
        "references": [
        'Malika Favre covers',
        'Noma Bar hidden images',
        'New Yorker minimal spots',
        ],
    },
    "moe_kawaii": {
        "summary": '萌系可爱：大眼睛、 blush、 pastel 与 chibi 可选。日系 gacha/VTuber/轻百 aesthetic。',
        "category": '萌系/可爱',
        "artist_refs": 'Kyoto Animation moe、Sanrio、gacha game art',
        "era_texture": '2000s–2020s moe culture',
        "line_control": '细线圆角',
        "lighting_color": 'soft flat+ cheek blush',
        "palette_strategy": 'pastel candy',
        "atmosphere": 'innocent、 healing、 sparkly',
        "materials": 'cel flat, star sparkle overlay',
        "quality": 'gacha SSR frame quality',
        "taboos": ' gritty realism,  horror,  muscular hero',
        "characters_zh": '猫耳、蝴蝶结、 school uniform or maid，★眼。',
        "characters_en": 'moe kawaii anime girl, huge sparkling eyes, pastel hair, blush cheeks, cute peace sign pose, frilly outfit ribbons',
        "scenes_zh": '卧室、甜品店、樱花、彩虹背景。',
        "scenes_en": 'kawaii bedroom pastel decor, dessert cafe pink, cherry blossom sparkles, rainbow soft background',
        "colors": '樱花粉, 薄荷, 薰衣草, 奶油白, 星黄',
        "image_prompt": 'moe kawaii anime style, huge sparkling eyes, pastel pink hair, soft blush cheeks, frilly cute outfit, star sparkle overlays, healing pastel background, gacha game illustration quality, 4k',
        "video_prompt": 'sparkle burst eye shine, ribbon bounce idle animation, pastel background shimmer, cute head tilt moe motion, healing kawaii energy',
        "references": [
        'K-On!',
        'Sanrio characters',
        'Princess Connect art',
        ],
    },
    "neon_cyber_film": {
        "summary": (
            "霓虹赛博电影风格：以 2010s–2020s neo-noir sci-fi 电影（《银翼杀手2049》"
            "Roger Deakins 摄影、《攻壳机动队》真人版、Denis Villeneuve 式 scale）"
            "为基准，呈现湿街反射、全息广告巨构、孤独人影与 orange-teal 分离并存的 "
            "「future noir megacity + volumetric neon」视觉语法。"
            "人物以长风衣、侧脸霓虹映、android 疑云为核心；场景强调空街、"
            "广告峡谷、飞行车远光、酸雨雾。整体为 live-action anamorphic IMAX cinema，"
            "偏 orange vs teal color separation LUT，绝不做 medieval、明亮 comedy 或 flat illustration。"
            "适合赛博朋克、未来 noir、科幻短片 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 霓虹赛博电影（Neon Cyber Film Live-Action Neo-Noir）",
        "artist_refs": (
            "摄影：Roger Deakins《银翼杀手2049》、Darius Khondji、"
            "美术：Syd Mead、Dennis Villeneuve 调度；"
            "作品：Blade Runner 2049、Ghost in the Shell (2017)、Altered Carbon；"
            "美学：anamorphic wide、volumetric fog、wet asphalt specular、"
            "massive practical neon + CGI hologram scale。"
        ),
        "era_texture": (
            "近未来 megacity digital IMAX clean dark，wet surface  everywhere；"
            "volumetric haze 与 acid rain mist；"
            "hologram flicker、LED billboard bloom controlled；"
            "grain optional subtle，highlight neon bloom 可接受。"
        ),
        "line_control": (
            "构图 anamorphic wide negative space，人物 small in canyon；"
            "symmetry 与 leading lines 来自街道透视；"
            "slow dolly 或 crane 揭示 scale；"
            "close-up 用 neon rim 勾轮廓，face half in shadow。"
        ),
        "lighting_color": (
            "主光：neon motivated color（橙/青/紫）+ volumetric fog scatter；"
            "湿地面 bounce 加倍霓虹；"
            "剪影 backlight 与 smoke；"
            "禁忌：flat daylight pastoral、warm only cottage interior、comedy high-key。"
        ),
        "palette_strategy": (
            "主调：霓虹橙、青蓝、湿黑、全息紫、雾灰；"
            "orange-teal separation 为 signature；"
            "肤色冷调或半 android 中性；"
            "远景建筑可加 sickly green 酸雨 accent。"
        ),
        "atmosphere": (
            "lonely、vast、future noir、high tech low life；"
            "雨声、远处飞行车、全息广告低语（视觉：reflection ripple）；"
            "孤独人影 walking into fog；"
            "庄严压迫感，非 cartoon cyber illustration。"
        ),
        "materials": (
            "湿沥青、铬金属、全息玻璃、雨水雨衣、"
            "长风衣 fabric、neon tube、蒸汽排气口；"
            "忌 wood cottage、medieval stone、bright pastel toy。"
        ),
        "quality": (
            "IMAX sci-fi theatrical：anamorphic flare controlled、"
            "neon bloom without clipping、4K wet reflection detail。"
        ),
        "taboos": (
            "medieval fantasy、bright comedy sitcom lighting、"
            "flat 2D illustration only、pastoral daylight、historical costume drama。"
        ),
        "characters_zh": (
            "赛博 noir 人物：长风衣、高领、侧脸霓虹轮廓；"
            "疑似改造人冷峻眼神、雨水中伫立；"
            "路人剪影、全息面具倒影；"
            "动作缓慢沉重非 superhero pose。"
        ),
        "characters_en": (
            "neon cyber film character, long coat rain silhouette, "
            "holographic advertisement reflection on face, lonely future noir figure, "
            "anamorphic neon rim lighting, wet street walking, "
            "Roger Deakins Blade Runner 2049 inspired, android undertone optional"
        ),
        "scenes_zh": (
            "巨型全息广告峡谷、空荡雨街、飞行车远光掠过、"
            "酸雨雾巷、霓虹中文/日文招牌、地下通道蒸汽、屋顶俯瞰 megacity。"
        ),
        "scenes_en": (
            "mega city neon billboard canyon anamorphic, empty rain soaked street reflection, "
            "distant flying vehicle lights pass overhead, acid fog cyber metropolis alley, "
            "holographic ad flicker wet asphalt, lonely figure long coat center frame, "
            "volumetric fog orange teal separation"
        ),
        "colors": "霓虹橙, 青蓝, 湿黑, 全息紫, 雾灰, 酸雨绿点缀, 铬银反射",
        "image_prompt": (
            "neon cyber film cinematography, anamorphic rain soaked street, "
            "massive holographic advertisements, lonely figure long coat silhouette, "
            "orange teal color separation, volumetric fog, wet asphalt reflections, "
            "Roger Deakins Blade Runner 2049 inspired future noir, IMAX scale megacity, 4k"
        ),
        "video_prompt": (
            "slow anamorphic walk rain reflections ripple, hologram advertisement flicker, "
            "volumetric fog drift through neon canyon, flying car lights pass overhead, "
            "lonely cyber city atmosphere camera creep"
        ),
        "references": [
            "Blade Runner 2049 (2017)",
            "Ghost in the Shell (2017)",
            "Altered Carbon (2018)",
            "Dune (2021) city visuals",
        ],
    },
    "orange_yellow_cinematic": {
        "summary": (
            "橙黄色电影风格：以 contemporary cinematic warm grade 高峰（《疯狂的麦克斯4》沙漠橙、"
            "《老无所惧》黄昏焦虑、《她》暖色室内、Roger Deakins 沙漠摄影、"
            "Fincher amber 室内）为基准，呈现 golden hour 或 sodium vapor 主导、"
            "orange-yellow dominate 与 heat haze 并存的「sun-drenched nostalgia + unease」视觉语法。"
            "人物以汗渍光泽、墨镜、热风吹乱头发为核心；"
            "场景强调沙漠公路、黄昏球场、琥珀酒吧、阳光焦灼郊区。"
            "整体为 live-action theatrical colorist grade cinema，偏 orange-yellow LUT shadows teal 极少，"
            "绝不做 cool nordic only、纯 monochrome 或 neon purple 主导。"
            "适合沙漠史诗、怀旧焦虑、暖色叙事 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 橙黄色调电影（Orange Yellow Cinematic Color Grade Live-Action）",
        "artist_refs": (
            "摄影：Roger Deakins（沙漠/黄昏）、Emmanuel Lubezki golden hour；"
            "导演：George Miller、Coen Brothers、Spike Jonze《她》；"
            "作品：《疯狂的麦克斯4》《老无所惧》《她》《囚徒》；"
            "美学：orange yellow dominate grade、golden hour heat haze、"
            "sodium vapor amber、sun drenched skin、theatrical colorist shadow warmth。"
        ),
        "era_texture": (
            "contemporary cinematic grading trend，theatrical colorist 级；"
            "heat haze shimmer、dust in warm air readable；"
            "sun bleach fabric、amber glass refraction；"
            "digital 须 emulate film warm rolloff 非 cold digital default。"
        ),
        "line_control": (
            "构图 wide landscape 沙漠公路 或 intimate warm interior close；"
            "golden hour backlit silhouette 或 front lit sweat detail；"
            "horizon low 强调 heat sky gradient；"
            "movement：slow drive highway、sun move across face timelapse feel。"
        ),
        "lighting_color": (
            "主光：golden hour sun 或 sodium vapor amber street；"
            "shadow 偏暖褐非冷蓝（teal 仅点缀）；"
            "heat haze 作 atmospheric diffusion；"
            "禁忌：cool nordic grey only、flat fluorescent、neon purple dominant。"
        ),
        "palette_strategy": (
            "主调：橙、金黄、琥珀、深褐影、淡青仅点缀；"
            "orange yellow dominate，shadow 保留 warm brown；"
            "肤色 amber warm，汗渍 specular；"
            "夜景 sodium amber 延续日戏 warm anchor。"
        ),
        "atmosphere": (
            "heat、nostalgia、unease optional、sun-drenched anxiety；"
            "热风、路尘、琥珀酒杯、球场黄昏（视觉：haze shimmer、dust float）；"
            "epic warmth 与 suburban dread 可并存；"
            "非纯温馨治愈，可有 tension under warm light。"
        ),
        "materials": (
            "dust、amber glass、sun bleach cotton、"
            "皮革墨镜、沥青公路、生锈金属 warm rust；"
            "忌 ice blue dominant、neon cyber、clean nordic wood only。"
        ),
        "quality": (
            "院线 colorist 级：warm grade consistent frame to frame；"
            "heat haze 与 sweat specular readable；"
            "4K theatrical，thumbnail 可辨 orange-yellow dominant 与 sun mood。"
        ),
        "taboos": (
            "cool nordic only、pure monochrome、neon purple dominant、"
            "flat office LED、desaturated indie grey only。"
        ),
        "characters_zh": (
            "汗渍光泽皮肤、墨镜、热风吹乱头发；"
            "沙漠 wanderer 或郊区焦虑青年；"
            "穿褪色 T 恤、工装、皮革夹克 warm tone；"
            "表情 contemplative 或 tense under sun。"
        ),
        "characters_en": (
            "orange yellow cinematic character, sweat glisten golden hour skin, "
            "sunglasses desert wanderer, warm amber skin tone portrait, "
            "windblown hair heat atmosphere, sun drenched anxious expression, "
            "theatrical warm color grade presence"
        ),
        "scenes_zh": (
            "沙漠公路热浪、黄昏棒球场、"
            "琥珀灯光酒吧、阳光焦灼郊区街道、"
            "麦田 golden hour 远景。"
        ),
        "scenes_en": (
            "desert highway heat haze shimmer orange sky, golden hour baseball field, "
            "amber lit bar interior warm shadows, sun drenched suburban anxiety street, "
            "wheat field magic hour vast warm landscape"
        ),
        "colors": "橙, 金黄, 琥珀, 深褐影, 淡青点缀, 锈红, 沥青黑暖调",
        "image_prompt": (
            "orange yellow cinematic color grade dominant, golden hour desert highway heat haze, "
            "sun drenched warm atmosphere amber skin tones, nostalgic yet tense mood, "
            "theatrical cinematography rich warm shadows, sodium vapor amber optional, "
            "Roger Deakins desert inspired warmth, 4k"
        ),
        "video_prompt": (
            "golden hour sun move across face slow, heat haze road shimmer drive, "
            "amber bar light flicker warm, warm dust particles float sun shaft, "
            "orange yellow grade consistent motion cinematic"
        ),
        "references": [
            "Mad Max Fury Road (2015)",
            "No Country for Old Men (2007)",
            "Her (2013) warm scenes",
        ],
    },
    "palace_intrigue_cold": {
        "summary": (
            "宫斗权谋冷峻风格：以国产宫廷剧高峰（《甄嬛传》《如懿传》《延禧攻略》）摄影美学为基准，"
            "呈现深宫红墙、对称纵深、侧光冷调与局部暖烛高光并存的「克制奢华 + 暗涌杀机」视觉语法。"
            "人物以旗头/钿子、护甲、团扇、跪拜礼仪与「笑里藏刀」微表情为核心；场景强调故宫式中轴对称、"
            "雪落庭院、烛火深殿与长廊透视。整体为 live-action 电影级写实摄影，偏 teal-grey 冷调 LUT，"
            "金绣与宫墙朱红作点缀，绝不做明亮甜宠、现代时装或日系动漫化。"
            "适合宫斗、权谋、古装悬疑、历史正剧向 AIGC 短剧的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 国产宫廷权谋剧（Palace Intrigue Live-Action Drama）",
        "artist_refs": (
            "摄影与美术参照：《甄嬛传》《如懿传》《延禧攻略》《芈月传》组；"
            "故宫/横店/明清宫苑实景组；"
            "摄影指导式美学：侧光肖像、对称纵深、冷暖对位（cold ambient + warm candle key）；"
            "妆造：清代宫廷旗装、钿子旗头、护甲、云肩、团扇、步摇。"
        ),
        "era_texture": (
            "2010s–2020s 国产宫廷剧数字摄影高峰，4K 干净肤质与织物细节，"
            "轻微 film grain 可选（非粗颗粒战争片）；"
            "室内烛火场景带 subtle smoke/haze，外景雪庭带冷空气透视；"
            "色彩经 teal-grey 或 cyan-shadow 调色，保留 drama clean 肤质，避免 MV 过度磨皮。"
        ),
        "line_control": (
            "构图以对称轴、框中框（门框/窗棂/廊柱）与纵深消失点为主；"
            "人物肖像常用三分法侧脸或半侧，眼神留「余光」空间暗示算计；"
            "群像站位层次分明（主子居中、嬷嬷/宫女分列），跪姿形成重复韵律；"
            "少用手持 chaos，多用 slow dolly / locked-off 压迫感。"
        ),
        "lighting_color": (
            "主光：侧光或侧逆光（window light / corridor slit light），面部半明半暗；"
            "辅光：极弱 fill 保留眼窝阴影；"
            "点缀：烛火、宫灯暖黄（2700K–3200K）在冷环境中作 small hot spot；"
            "雪景：高键冷白 + 低饱和天空，人物斗篷/毛领边缘 rim light；"
            "禁忌：flat beauty dish 网红光、彩虹霓虹、过度 HDR。"
        ),
        "palette_strategy": (
            "主调：冷青灰（teal-grey）、宫墙红（muted cinnabar）、炭黑/鸦青；"
            "点缀：金绣、明黄团龙、翡翠/玉绿、雪白；"
            "肤色：偏冷中性，唇色克制（豆沙/淡朱），眼妆细而利；"
            "叙事用色：位份越高金红越集中，禁足/失宠场景去饱和并压暗。"
        ),
        "atmosphere": (
            "克制、礼仪、尊卑与 hidden threat 并存；表面静穆，暗线紧张；"
            "雪、风、烛焰微颤、远处钟鼓或更漏声（视觉可表现为空庭飘雪、纱帘轻动）；"
            "对话场景常用「近景表情 + 远景深宫」对照，强调孤独与算计；"
            "战斗/惩罚场面仍保持 drama 级写实，非武侠玄幻光效。"
        ),
        "materials": (
            "服饰：云锦/织金缎、毛领、护甲、盘扣、朝珠、团扇、帕子；"
            "头饰：钿子、旗头、步摇、流苏、点翠（或仿点翠）；"
            "建筑：朱墙、黄琉璃瓦、汉白玉栏、雕梁彩绘、宫灯、铜缸、冰窖；"
            "道具：玉如意、圣旨卷轴、茶盏、香炉、炭盆、梅花/腊梅；"
            "环境：落雪、薄雾、红墙夹道、对称月洞门。"
        ),
        "quality": (
            "4K drama cinematography，肤质与织物纹理清晰；"
            "适合 9:16 竖版角色卡与 16:9 场景宽镜；"
            "景深可控（浅景深肖像 / 深景深对称走廊）；"
            "live-action realistic，非插画、非 3D CG 古装。"
        ),
        "taboos": (
            "现代服装配饰、运动鞋、眼镜、手机；"
            "明亮甜宠 romcom 粉光、日系大眼滤镜、网红美颜；"
            "赛博霓虹、武侠玄幻气浪、Anime cel shading；"
            "过度血腥恐怖、西方中世纪铠甲、日式和服混淆；"
            "watermark、字幕条、多格漫画分镜（单图角色卡时）。"
        ),
        "characters_zh": (
            "【面部】柳叶眼/丹凤眼，眼线细而长，眉形清晰；唇色豆沙或淡朱，腮红极弱；"
            "表情：浅笑不露齿、垂眸、侧目、指节微白握扇——「笑里藏刀」；"
            "哭戏也偏克制，泪痕一线而非嚎啕。"
            "【头饰】皇后/贵妃：钿子或旗头 + 点翠/金步摇；格格/答应：简化旗头；"
            "太监/嬷嬷：无钿子，帽翅/布巾区分。"
            "【服饰】冬：毛领斗篷、护甲；夏：纱质/单衣；位份以团龙、云纹、金线密度区分；"
            "手持团扇、帕子、念珠、指甲套（护甲）。"
            "【体态】行礼：万福、跪拜、叩首；站姿端正，步态小碎步；"
            "群像时主子居中高位，奴仆低眉顺目。"
            "【气质范例】甄嬛——隐忍聪慧；皇后——威仪压场；华妃——骄纵刃利；"
            "如懿——冷静刚烈；太监首领——弓身假笑。"
        ),
        "characters_en": (
            "Chinese palace intrigue drama character, Qing court costume with golden embroidery, "
            "elaborate court headdress and hair ornaments, cold side light half face shadow, "
            "subtle scheming expression with downcast eyes, folding fan or prayer beads in hand, "
            "kneeling or standing formal court posture, teal grey cinematic color grade, "
            "live-action realistic skin texture, imperial silk and fur collar detail, "
            "forbidden city drama aesthetic, no modern makeup filter, no anime style"
        ),
        "scenes_zh": (
            "【典型环境】紫禁城长走廊、养心殿/坤宁宫、御花园、冰窖、冷宫、慈宁宫、"
            "红墙夹道、汉白玉台基、对称月洞门、雪落庭院。"
            "【构图】中轴对称纵深，廊柱形成框景；人物置前景三分之一，远景层层殿宇；"
            "或 lone figure 在巨大空庭中显渺小。"
            "【光影】窗棂投影条纹、烛火暖点、雪地冷反射；"
            "夜戏：宫灯成排，地面微湿反光。"
            "【季节】冬雪、初春薄寒、秋夕落叶（低饱和）；"
            "避免夏阳高饱和度假感。"
        ),
        "scenes_en": (
            "forbidden city long corridor symmetrical perspective, imperial palace courtyard snow falling, "
            "throne hall candlelight depth haze, red palace wall white marble railing, "
            "moon gate framing cold winter garden, teal grey cinematic color grade, "
            "slow dolly depth layers, live-action Chinese palace drama atmosphere, "
            "court intrigue tension, dramatic side light window slats, 4k clean drama cinematography"
        ),
        "colors": (
            "主色：冷青灰、宫墙朱红（muted）、炭黑/鸦青、雪白；"
            "点缀：金绣、明黄团龙、翡翠绿、烛火暖黄；"
            "肤色：冷中性，唇豆沙；"
            "叙事：失宠/禁足场景整体降饱和压暗，册封/大典可略提金红密度"
        ),
        "image_prompt": (
            "Chinese palace intrigue cold tone live-action cinematography, forbidden city symmetrical corridor depth, "
            "Qing court imperial costume with golden embroidery and elaborate headdress, "
            "cold side light scheming portrait half face shadow, snow covered palace courtyard atmosphere, "
            "teal grey cinematic color grade with warm candle accent spots, "
            "red palace wall white marble details, folding fan court etiquette, "
            "Empresses in the Palace drama aesthetic, live-action realistic skin and silk texture, "
            "slow dramatic composition, shallow depth of field optional, "
            "no modern filter, no anime, no bright romcom lighting, highly detailed 4k vertical 9:16"
        ),
        "video_prompt": (
            "slow dolly down palace corridor symmetry, snow falling silent courtyard, "
            "candle flame tremble in throne hall haze, court character subtle eye shift scheming, "
            "teal grey grade consistent cold atmosphere, silk robe slight movement, "
            "live-action palace intrigue tension motion, no shaky action cam, dramatic restraint pacing"
        ),
        "references": [
            "甄嬛传 / Empresses in the Palace (2011)",
            "如懿传 / Ruyi's Royal Love in the Palace (2018)",
            "延禧攻略 / Story of Yanxi Palace (2018)",
            "芈月传 / Legend of Mi Yue (2015)",
            "故宫 / The Forbidden City documentary",
            "满城尽带黄金甲 (2006) 色彩参考（慎用过度饱和）",
        ],
    },
    "purple_tone_cinematic": {
        "summary": (
            "紫色色调电影风格：以 2010s stylized cinema 与 MV 高峰（Nicolas Winding Refn《亡命驾驶》"
            "夜景、《Euphoria》灯光、《银翼杀手》紫雾）为基准，呈现 twilight magic hour 偏紫、"
            "dreamlike romance 或 synth mood 并存的「purple dominate + melancholic luxury」视觉语法。"
            "人物以夜店装束、反光墨镜、ethereal calm 表情为核心；"
            "场景强调紫色黄昏公路、俱乐部浴室霓虹、屋顶 dusk 城市紫天。"
            "整体为 live-action high end commercial grade cinema，偏紫+品红+暮蓝 LUT，"
            "绝不做 documentary neutral 或 warm desert only 主导。"
            "适合音乐视频、奢华夜景、赛博浪漫 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 紫色色调电影（Purple Tone Cinematic Live-Action）",
        "artist_refs": (
            "导演：Nicolas Winding Refn《Drive》；"
            "灯光：《Euphoria》purple gel、《银翼杀手》purple haze；"
            "美学：twilight purple grade、neon purple gel、"
            "music video colorist flattering purple skin、highway night bokeh。"
        ),
        "era_texture": (
            "2010s stylized cinema and MV digital pristine；"
            "chrome reflection、velvet fabric、city bokeh smooth；"
            "neon haze particle purple tint；"
            "digital 须 emulate commercial grade 非 documentary flat。"
        ),
        "line_control": (
            "构图 centered portrait 或 highway night vanishing line；"
            "rooftop dusk silhouette against purple sky；"
            "club interior mirror neon symmetry；"
            "movement：slow highway drive bokeh、neon pulse club。"
        ),
        "lighting_color": (
            "主光：twilight ambient purple + neon purple gel accent；"
            "肤色 flattering purple cast on cheek；"
            "屏幕/霓虹作 rim purple magenta；"
            "禁忌：documentary neutral flat、warm desert orange only、daylight neutral。"
        ),
        "palette_strategy": (
            "主调：紫、品红、暮蓝、霓虹白、肤柔；"
            "purple dominate 60%+ frame；"
            "skin flattering purple 非 sick green；"
            "accent chrome silver 或 neon white highlight。"
        ),
        "atmosphere": (
            "dream、synth、melancholic luxury、nightlife solitude；"
            "引擎低鸣、霓虹脉冲、黄昏紫云（视觉：purple sky deepen、bokeh drift）；"
            "music video emotional peak 非 documentary；"
            "calm uncanny 与 luxury 并存。"
        ),
        "materials": (
            "chrome car surface、velvet club interior、"
            "reflective sunglasses、neon tube purple、"
            "wet asphalt reflection；"
            "忌 rustic organic wood only、ancient stone only。"
        ),
        "quality": (
            "高端商业/MV 院线级：bokeh smooth、purple grade consistent；"
            "chrome specular 与 neon edge readable；"
            "4K pristine，thumbnail 可辨 purple twilight 与 nightlife portrait。"
        ),
        "taboos": (
            "documentary neutral only、warm desert golden only、"
            "flat office daylight、pastel kawaii daytime。"
        ),
        "characters_zh": (
            "夜店装束、反光墨镜；"
            "ethereal calm 或 melancholic stare；"
            "luxury nightlife styling 皮革/丝绒；"
            "发型 slick 或 wet look purple rim。"
        ),
        "characters_en": (
            "purple tone cinematic character twilight neon portrait, reflective sunglasses, "
            "dreamlike calm expression luxury nightlife styling, "
            "music video aesthetic purple skin flattering grade, synth mood presence"
        ),
        "scenes_zh": (
            "紫色黄昏公路驾车、俱乐部浴室霓虹雾、"
            "屋顶 dusk 城市紫天、霓虹隧道、"
            "雨夜紫色反光街道。"
        ),
        "scenes_en": (
            "purple twilight highway driving city bokeh, neon club interior bathroom haze purple, "
            "rooftop dusk city purple sky silhouette, neon tunnel magenta glow, "
            "rainy street purple reflection dreamlike nightscape"
        ),
        "colors": "紫, 品红, 暮蓝, 霓虹白, 肤柔, 铬银, 深紫黑",
        "image_prompt": (
            "purple tone cinematic color grade twilight neon portrait, dreamlike urban night highway, "
            "synth mood atmosphere flattering purple skin tones, luxury melancholic composition, "
            "music video aesthetic Nicolas Winding Refn inspired, 4k commercial grade"
        ),
        "video_prompt": (
            "purple twilight sky deepen slow, neon club light pulse magenta, "
            "slow highway drive bokeh purple consistent, dreamlike purple grade drift, "
            "synth mood motion luxury night"
        ),
        "references": [
            "Drive (2011) night scenes",
            "Euphoria lighting",
            "Blade Runner purple haze",
        ],
    },
    "retro_cinematography": {
        "summary": (
            "复古电影摄影风格：以 1970s–1990s film stock emulation 通用美学（Kodak 胶片、"
            "Super 8 nostalgia、《不羁夜》《几近成名》look）为基准，呈现 35mm grain、"
            "soft halation 与 vintage lens flare 并存的「analog warmth + nostalgia」视觉语法。"
            "人物以 period hair wardrobe、candid documentary feel 为核心；"
            "场景强调 disco、郊区街道、霓虹 diner、汽车影院。"
            "整体为 live-action 35mm film emulation cinema，偏柯达暖+褪色青 lifted shadows LUT，"
            "绝不做 ultra sharp digital、anime 或 flat vector 主导。"
            "适合复古年代片、怀旧叙事、胶片感广告 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 复古电影摄影（Retro Cinematography Film Emulation Live-Action）",
        "artist_refs": (
            "摄影：Kodak film stocks Vision3 emulation、Super 8 nostalgia；"
            "作品：《不羁夜》《几近成名》；"
            "美学：35mm grain、soft halation、vintage lens flare、"
            "lifted black shadows、period accurate framing。"
        ),
        "era_texture": (
            "1970s–1990s film emulation 35mm grain visible；"
            "gate weave subtle、halation on highlight 非 oversharpen；"
            "fade blacks lifted shadows analog warmth；"
            "digital 须 emulate scan grain 非 digital noise pattern。"
        ),
        "line_control": (
            "构图 period accurate framing：disco wide、diner two-shot；"
            "suburban street vintage cars depth；"
            "drive-in screen glow backlight；"
            "movement：slow pan period scene、flare sun enter frame。"
        ),
        "lighting_color": (
            "主光：tungsten interior + daylight film balance；"
            "highlight soft halation rolloff；"
            "neon diner night accent；"
            "禁忌：ultra sharp digital HDR、flat LED ring light、anime cel flat。"
        ),
        "palette_strategy": (
            "主调：柯达暖、褪色青、颗粒灰、霓虹红；"
            "warm analog base + faded teal shadow；"
            "肤色 period natural 非 modern glamour；"
            "night 场景 neon red 作 accent 保留 grain。"
        ),
        "atmosphere": (
            "nostalgia、analog warmth、candid documentary feel；"
            "胶片颗粒、镜头光晕、年代服饰（视觉：grain overlay、flare streak）；"
            "personal memory 与 pop culture epoch 并存；"
            "非 epic blockbuster teal-orange only。"
        ),
        "materials": (
            "film grain overlay、vinyl disco floor、"
            "chrome diner counter、vintage car metal、"
            "wood panel suburban、drive-in screen canvas；"
            "忌 clean glass futurism、digital UI screen dominant。"
        ),
        "quality": (
            "胶片扫描还原级：grain consistent、halation natural；"
            "period wardrobe fabric readable through grain；"
            "4K with film grain，thumbnail 可辨 70s color fade 与 flare。"
        ),
        "taboos": (
            "ultra sharp digital clean、anime cartoon、flat vector、"
            "modern smartphone HDR、cyber neon only。"
        ),
        "characters_zh": (
            "period hair wardrobe 70s–90s；"
            "candid documentary feel 自然表情；"
            "disco 装束或郊区 casual；"
            "vintage lens flare 可勾发丝轮廓。"
        ),
        "characters_en": (
            "retro cinematography character 1970s wardrobe hair, film grain portrait, "
            "analog warmth candid expression, vintage lens flare halation, "
            "period setting nostalgic film stock aesthetic"
        ),
        "scenes_zh": (
            "70s disco 舞池颗粒、郊区复古街道、"
            "霓虹 diner 夜景、汽车影院屏幕光、"
            "胶片感室内钨丝灯。"
        ),
        "scenes_en": (
            "1970s disco dance floor film grain halation, suburban street vintage cars period, "
            "neon diner night tungsten glow, drive-in theater screen backlight glow, "
            "analog warmth interior lifted shadow shadows Kodak fade"
        ),
        "colors": "柯达暖, 褪色青, 颗粒灰, 霓虹红, 钨黄, 米褐, 胶片黑",
        "image_prompt": (
            "retro cinematography 35mm film grain vintage lens flare, 1970s color fade analog warmth halation, "
            "period wardrobe setting lifted black shadows, nostalgic film stock aesthetic cinematic composition, "
            "Kodak emulation Boogie Nights inspired, 4k with grain"
        ),
        "video_prompt": (
            "film gate weave subtle drift, vintage flare sun enter frame streak, "
            "grain consistent overlay motion, period scene slow pan nostalgic, "
            "analog warmth halation highlight roll"
        ),
        "references": [
            "Boogie Nights (1997)",
            "Almost Famous (2000)",
            "Kodak Vision3 emulation",
        ],
    },
    "retro_halftone_gothic": {
        "summary": '复古网点哥特：Victorian horror meets pulp comic halftone。Tim Burton 与 EC comics 混合平面。',
        "category": '复古网点哥特',
        "artist_refs": 'Tim Burton、EC Comics、Edward Gorey',
        "era_texture": 'Victorian gothic pulp print',
        "line_control": 'spindly ink+ halftone shadow',
        "lighting_color": 'flat with spot moon',
        "palette_strategy": 'black purple orange halftone',
        "atmosphere": 'macabre cute、 spooky fun',
        "materials": 'halftone dots, scratchy ink',
        "quality": 'print registration charm',
        "taboos": ' photoreal,  clean corporate,  bright kawaii',
        "characters_zh": '细肢、大眼眶、条纹袜、苍白。',
        "characters_en": 'retro halftone gothic character, spindly Tim Burton proportions, pale skin dark circles, striped stockings, EC comics horror cute',
        "scenes_zh": ' cemetery twist tree、 crooked house、 moon cloud。',
        "scenes_en": 'gothic cemetery twisted trees, crooked Victorian house, halftone moon clouds, pulp horror comic background',
        "colors": '黑, 紫, 橙网点, 灰绿, 骨白',
        "image_prompt": 'retro halftone gothic illustration, Tim Burton spindly character, EC comics dot shadows, Victorian cemetery twisted trees, macabre cute aesthetic, purple orange black palette, pulp horror print quality, 4k',
        "video_prompt": 'halftone dot shimmer animation, spindly character creep walk, moon cloud slide gothic, scratchy ink boil, macabre cute motion',
        "references": [
        'Edward Scissorhands (1990)',
        'EC Tales from the Crypt',
        'Edward Gorey illustrations',
        ],
    },
    "retro_narrative_film": {
        "summary": (
            "复古叙事电影风格：以 1930s–1960s classic Hollywood narrative cinema（黑色电影、"
            "screwball comedy、法庭剧与火车对话场景）摄影美学为基准，"
            "呈现 motivated light、master shot coverage 逻辑与 blocking 驱动的 "
            "「story-first theatrical naturalism」视觉语法。"
            "人物以 period dialogue pose、eyeline match 表情为核心；场景强调客厅对峙、"
            "火车包厢、法庭证词、剧院后台。整体为 live-action Technicolor 或 rich B&W cinema，"
            "偏 motivated window/lamp light，绝不做 handheld chaos only 或 MV 纯 stylization。"
            "适合复古剧情、经典好莱坞叙事、话剧感对白场景 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 复古叙事电影（Retro Narrative Film Classic Hollywood Live-Action）",
        "artist_refs": (
            "导演：Billy Wilder、Alfred Hitchcock、Sidney Lumet、Howard Hawks；"
            "作品：《十二怒汉》《 Rear Window》《 Some Like It Hot》《 Witness for the Prosecution》；"
            "美学：master shot + shot-reverse-shot rhythm、motivated practical lamp、"
            "period accurate set dressing、deep staging blocking。"
        ),
        "era_texture": (
            "1930s–1960s narrative cinema restoration print clarity；"
            "Technicolor 饱和或 rich monochrome silver gelatin contrast；"
            "studio set walls with texture paint，props period accurate；"
            "film grain fine，gate steady，no modern digital sharpening halos。"
        ),
        "line_control": (
            "构图 master shot coverage logic：two-shot dialogue、"
            "over-shoulder 对话、deep staging 多层景深；"
            "train compartment 用 frame lines 引导 eyeline；"
            "courtroom 对称与 witness 孤立 frame；"
            "movement 服务 blocking 非 flashy drone。"
        ),
        "lighting_color": (
            "主光：motivated window 或 table lamp 可见光源；"
            " noir 场景：hard key + venetian blind shadow；"
            " comedy：even fill 保表情；"
            "禁忌：unmotivated neon、flat LED ring light、music video color wash only。"
        ),
        "palette_strategy": (
            "Technicolor：rich primaries + cream highlight；"
            "B&W：silver grey midtone、deep velvet black；"
            "interior wallpaper pattern 作 texture color；"
            "情绪转折可用 shadow 加深但保持 period palette。"
        ),
        "atmosphere": (
            "story first、theatrical naturalism、dialogue tension；"
            "clock ticking、cigarette smoke、train whistle（视觉：steam window）；"
            "courtroom silence、curtain rustle；"
            "wit 与 suspense 并存，表演略舞台化但 grounded。"
        ),
        "materials": (
            "period wood furniture、wallpaper、train leather seat、"
            "court wood panel、brass lamp、typed paper props；"
            "忌 modern smartphone、glass skyscraper、sportswear。"
        ),
        "quality": (
            "经典电影修复级 clarity：fabric pattern 与 face wrinkle readable；"
            "shot-reverse-shot 缩略图仍可读 eyeline 关系。"
        ),
        "taboos": (
            "handheld chaos only、MV stylization without story、"
            "modern urban neon、cyber sci-fi、anime stylization。"
        ),
        "characters_zh": (
            "经典好莱坞叙事人物：period 西装礼服、戏剧化站姿；"
            "对话场景 eyeline 精准、手势克制；"
            "法官、律师、列车员、邻居作群像；"
            "表情服务于台词 subtext。"
        ),
        "characters_en": (
            "retro narrative film character, classic Hollywood dialogue pose, "
            "period accurate costume 1940s 1950s, motivated window lamp lighting portrait, "
            "story driven expression, train compartment conversation staging, "
            "theatrical naturalism cinema presence"
        ),
        "scenes_zh": (
            "客厅对峙、火车包厢对话、法庭证词、"
            "剧院后台、餐厅卡座、雨夜街灯门口、书房台灯阅读。"
        ),
        "scenes_en": (
            "classic living room confrontation dialogue scene, train compartment conversation two-shot, "
            "courtroom dramatic testimony wide, period interior set dressing narrative, "
            "motivated window lighting study, retro narrative film blocking composition"
        ),
        "colors": "Technicolor原色或rich黑白灰, 木暖褐, 墙纸花纹, 台灯琥珀, 墨绿阴影",
        "image_prompt": (
            "retro narrative film cinematography, classic Hollywood dialogue framing, "
            "period accurate interior set dressing, motivated window and lamp lighting, "
            "story driven composition technicolor or rich black white, "
            "theatrical naturalism timeless cinema aesthetic, train or courtroom scene, 4k"
        ),
        "video_prompt": (
            "classic shot reverse shot dialogue rhythm, motivated table lamp turn on, "
            "train window landscape pass behind speakers, narrative blocking shift step, "
            "period film pacing camera hold"
        ),
        "references": [
            "12 Angry Men (1957)",
            "Some Like It Hot (1959)",
            "Rear Window (1954)",
            "Witness for the Prosecution (1957)",
        ],
    },
    "retro_psychedelic_texture": {
        "summary": '复古迷幻纹理：60–70s psychedelic poster swirl、 liquid color 与 overlay patterns。Rock poster 与 experimental film。',
        "category": '复古迷幻',
        "artist_refs": 'Peter Max、Yellow Submarine、Fillmore posters',
        "era_texture": '1967–1972 psychedelic era',
        "line_control": 'flowing contour+ pattern fill',
        "lighting_color": 'flat graphic no real light',
        "palette_strategy": 'clashing saturated rainbow',
        "atmosphere": 'trippy、 groovy、 utopian',
        "materials": 'halftone swirl, oil overlay',
        "quality": 'screenprint texture',
        "taboos": ' minimal corporate,  realistic noir',
        "characters_zh": ' big hair、 round glasses、 peace sign。',
        "characters_en": 'retro psychedelic character, swirling rainbow pattern skin, round groovy glasses, peace sign pose, 1960s festival fashion',
        "scenes_zh": ' mushroom landscape、 liquid sky、 concert crowd swirl。',
        "scenes_en": 'psychedelic swirling landscape, liquid rainbow sky, concert crowd pattern overlay, mushroom fantasy valley',
        "colors": '彩虹饱和, 橙紫 clash, 酸绿, 热粉, 黄',
        "image_prompt": 'retro psychedelic texture art, swirling rainbow patterns, 1960s concert poster aesthetic, liquid color overlays, groovy character portrait, Peter Max inspired design, saturated clashing palette, screenprint texture, 4k',
        "video_prompt": 'psychedelic swirl pattern rotate, liquid color morph background, groovy zoom pulse, rainbow overlay shift, trippy 60s motion',
        "references": [
        'Yellow Submarine (1968)',
        'Fillmore concert posters',
        'Peter Max art',
        ],
    },
    "retro_sci_fi_atompunk": {
        "summary": (
            "复古科幻原子朋克（Retro Sci-Fi Atompunk）：以 1950s 原子时代「未来昨日」美学为核心，"
            "融合 Googie 建筑、流线型 chrome 鳍片、bubble helmet 宇航服、raygun 与真空管控制台。"
            "视觉气质在「红色恐怖时代的乐观未来主义」与「核时代 uncanny」之间摆动，"
            "参照 Fallout 系列、1950s World's Fair、Norman Bel Geddes 工业设计与《The Jetsons》动画。"
            "配色以青绿（turquoise）、奶油白、樱桃红与铬银为主，材质强调 bakelite、"
            "抛光金属、玻璃气泡罩与印刷插画颗粒。适合 retro-futurism 科幻短剧、"
            "原子朋克角色/场景与怀旧科幻广告风 AIGC。"
        ),
        "category": "复古科幻原子朋克 / 1950s Atompunk Retro-Futurism（live-action or vintage illustration）",
        "artist_refs": (
            "Fallout series environmental art；"
            "Norman Bel Geddes（Futurama 1939、流线型工业设计）；"
            "1950s Popular Mechanics / Mechanix Illustrated 封面；"
            "Googie architecture（洛杉矶 Diners、加油站、太空针）；"
            "The Jetsons (1962)、Flash Gordon serial、1950s pin-up sci-fi illustration。"
        ),
        "era_texture": (
            "1950s–1960s atomic age print aesthetic：轻微 offset 网点/杂志印刷 grain，"
            "chrome 高光硬边，plastic 与 bakelite 饱和色；"
            "可选 live-action 实拍质感（复古 studio flash）或 vintage pulp illustration 平面；"
            "忌 2020s minimal UI、Apple 风纯白、赛博朋克湿街。"
        ),
        "line_control": (
            "形态语言：streamlined curves、tail fins、火箭轮廓、星burst 徽章；"
            "建筑：折线屋顶、倾斜玻璃、neon 招牌几何字；"
            "人物：bubble helmet 正圆玻璃罩、肩甲式宇航服、A-line 裙与 pin-up 姿态；"
            "构图：hero product shot 居中、对称 launch pad、低角度仰拍火箭。"
        ),
        "lighting_color": (
            "硬光 studio flash 或 midday sun（高对比 chrome specular）；"
            "室内：vacuum tube 控制台绿/琥珀 glow + 天花板 bare bulb；"
            "夜外景：neon turquoise/red 招牌反射在 chrome 车身；"
            "可选 subtle nuclear glow green（谨慎，偏 stylized 非恐怖 gore）。"
        ),
        "palette_strategy": (
            "主色：turquoise / aqua、cream ivory、cherry red、cadmium orange；"
            "金属：chrome silver、brushed aluminum；"
            "点缀：原子符号黄、星burst 白、森林绿（1950s appliance green）；"
            "叙事：乌托邦广告用高饱和；废土/uncanny 版本可降饱和加 dust beige（仍保留 atompunk 读感）。"
        ),
        "atmosphere": (
            "optimistic retro-future → subtle uncanny：完美核家庭微笑背后一丝不安；"
            "火箭发射 smoke、播音员式宏大叙事、博览会 pavilion 人群；"
            "robot companion、raygun holster、jetpack test pad；"
            "适合 black comedy sci-fi 与 nostalgic adventure 并存。"
        ),
        "materials": (
            "chrome bumpers、tail fins、hubcaps；"
            "bakelite radio、vacuum tubes、analog gauge、toggle switches；"
            "bubble helmet glass、rubber hose、pressure suit ribbing；"
            "linoleum floor、formica counter、checkered diner tile；"
            "warning labels、atomic symbol decals、retro CRT screens。"
        ),
        "quality": (
            "4k retro illustration or live-action with period lens character；"
            "chrome 与玻璃高光可控，避免 modern CGI plastic look；"
            "适合 9:16 角色海报与 16:9 博览会/发射场宽景；"
            "print texture subtle，非 dirty grunge（除非刻意 Fallout wasteland variant）。"
        ),
        "taboos": (
            " sleek 2020s minimal sci-fi、iPhone、现代 HUD、全息蓝透明 UI；"
            "赛博朋克 rain neon（属 cyberpunk 非 atompunk）；"
            "hard military realistic 现代战争、medieval fantasy；"
            "anime chibi、photorealistic horror gore；"
            "watermark、stock photo 现代城市 skyline。"
        ),
        "characters_zh": (
            "【宇航/探险】bubble helmet 透明圆罩、白色/银灰 pressure suit、"
            "胸前 hose 与 gauge、raygun 皮 holster、皮手套；"
            "姿态：hero pose 指向前方或 salute。"
            "【pin-up / 1950s 家庭】A-line 裙、头巾、红唇、复古 curl 发型；"
            "男性：窄 tie、short brim hat、吸烟斗或报纸（exposition 感）。"
            "【robot companion】圆头 chrome robot、天线、单眼 cyclops 或双灯眼、"
            "关节外露 rivets，表情 friendly but uncanny。"
            "【反派/辐射风】可选 gas mask、caution tape（仍 stylized，非 gross horror）。"
            "【气质】微笑乐观、播音员自信、或 Fallout 式 retro sarcasm。"
        ),
        "characters_en": (
            "retro atompunk sci-fi character, 1950s bubble helmet astronaut suit with chrome details, "
            "raygun holster and leather gloves, pin-up sci-fi outfit optional, "
            "friendly chrome robot companion sidekick, vintage atomic age fashion, "
            "hard studio lighting chrome specular highlights, turquoise cream red color scheme, "
            "Norman Bel Geddes futurism silhouette, live-action or vintage pulp illustration style, "
            "no modern minimalist sci-fi, no cyberpunk rain neon"
        ),
        "scenes_zh": (
            "【建筑】Googie diner、火箭形加油站、expo pavilion、domed future home；"
            "【发射场】launch pad smoke、countdown board、围观 1950s crowd；"
            "【室内】future living room：vacuum tube console、圆角家具、starburst clock；"
            "【城市】atompunk skyline with finned towers、neon sign、flying car concept art 背景；"
            "【废土变体（可选）】rust chrome、 faded billboard、仍读 atompunk 非 pure post-apocalypse。"
        ),
        "scenes_en": (
            "Googie architecture retro diner exterior, 1950s rocket launch pad smoke plume, "
            "atomic age future living room vacuum tube console, atompunk city skyline chrome fins, "
            "world fair pavilion crowd vintage fashion, neon turquoise red signage reflections, "
            "Norman Bel Geddes streamlined design, retro sci-fi magazine illustration atmosphere, "
            "hard flash chrome highlights, optimistic then uncanny retro-future, 4k detailed"
        ),
        "colors": (
            "主色：青绿/turquoise、奶油 ivory、樱桃红、镉橙；"
            "金属：铬银、铝灰；"
            "点缀：原子黄、星burst 白、1950s appliance green；"
            "废土变体：dust beige、rust orange（仍保留 retro signage 色块）"
        ),
        "image_prompt": (
            "retro sci-fi atompunk aesthetic, 1950s atomic age futurism, Googie architecture chrome diner, "
            "bubble helmet astronaut with raygun, turquoise cream cherry red palette, "
            "vacuum tube console glowing gauges, streamlined tail fin rocket design, "
            "Norman Bel Geddes world fair futurism, vintage Popular Mechanics illustration texture, "
            "hard studio flash chrome specular, friendly robot companion, "
            "optimistic retro-future with subtle uncanny mood, "
            "no modern minimalist sci-fi, no cyberpunk neon rain, highly detailed 4k vertical 9:16"
        ),
        "video_prompt": (
            "retro rocket launch smoke plume slow motion, chrome fin car pull into Googie diner, "
            "vacuum tube console lights blink sequence, bubble helmet visor reflection pan, "
            "atompunk neon sign flicker, robot companion head turn friendly uncanny, "
            "1950s expo crowd subtle movement, turquoise red grade consistent retro-future motion"
        ),
        "references": [
            "Fallout series art direction",
            "1950s Popular Mechanics covers",
            "Norman Bel Geddes Futurama (1939 World's Fair)",
            "The Jetsons (1962)",
            "Flash Gordon (1936 serial)",
            "Tomorrowland / 1950s Disney futurism",
            "Mechanix Illustrated rocket car concepts",
        ],
    },
    "retro_war_film": {
        "summary": (
            "复古战争电影风格：以 1990s–2010s war epic cinema 高峰（Janusz Kamiński《拯救大兵瑞恩》、"
            "《1917》Deakins、《兄弟连》《全金属外壳》）为基准，呈现 desaturate bleach bypass、"
            "handheld chaos 与硝烟并存的「trauma + brotherhood + battlefield chaos」视觉语法。"
            "人物以泥血脸、头盔、狗牌、thousand yard stare 为核心；"
            "场景强调海滩登陆、战壕泥泞、燃烧城市废墟。"
            "整体为 live-action theatrical grain bleach bypass cinema，偏去饱和绿褐+爆炸橙 LUT，"
            "绝不做 clean fashion、明亮喜剧或 anime 主导。"
            "适合战争史诗、战场创伤、军事叙事 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 复古战争电影（Retro War Film Cinematography Live-Action）",
        "artist_refs": (
            "摄影：Janusz Kamiński《拯救大兵瑞恩》、Roger Deakins《1917》；"
            "导演：Steven Spielberg、Sam Mendes、Stanley Kubrick《全金属外壳》；"
            "作品：《拯救大兵瑞恩》《1917》《兄弟连》；"
            "美学：desaturate bleach bypass、handheld chaos framing、"
            "mud blood face、smoke obscured battlefield、explosion orange flash。"
        ),
        "era_texture": (
            "1990s–2010s war epic theatrical grain bleach bypass；"
            "mud、smoke、brass、wool uniform texture readable；"
            "handheld micro shake controlled；"
            "digital 须 emulate gritty grain 非 clean blockbuster polish only。"
        ),
        "line_control": (
            "构图 handheld chaos 为主，occasional steady hero walk；"
            "beach landing wide chaos multiple focal planes；"
            "trench claustrophobic tight；"
            "movement：explosion shock shake、slow walk through rubble。"
        ),
        "lighting_color": (
            "主光：overcast battle diffuse 或 explosion orange flash；"
            "smoke 作 atmospheric diffusion；"
            "night battle flares green/red sporadic；"
            "禁忌：bright comedy even fill、romance soft glow、clean fashion studio。"
        ),
        "palette_strategy": (
            "主调：去饱和绿、泥褐、烟灰、爆炸橙、血红；"
            "bleach bypass desaturate base；"
            "blood red accent 于伤口/爆炸；"
            "肤色 mud weathered 非 glamour。"
        ),
        "atmosphere": (
            "trauma、brotherhood、chaos、sacrifice；"
            "炮火、泥泞、硝烟（视觉：smoke wipe、mud splash）；"
            "thousand yard stare 是核心情绪符号；"
            "非 patriotic propaganda bright only。"
        ),
        "materials": (
            "mud、smoke、brass cartridge、wool uniform、"
            "steel helmet、dog tag metal、rubble concrete、"
            "burning timber ruin；"
            "忌 silk gown、glass office、neon sign。"
        ),
        "quality": (
            "战争史诗院线级：smoke particle、mud splash sharp；"
            "uniform wool weave through grime readable；"
            "4K gritty grain，thumbnail 可辨 soldier stare 与 smoke battlefield。"
        ),
        "taboos": (
            "clean fashion glamour、bright comedy sitcom、anime cartoon、"
            "cyber neon、palace costume drama。"
        ),
        "characters_zh": (
            "泥血脸、WWII/现代战头盔、狗牌；"
            "thousand yard stare 空洞凝视；"
            "羊毛军装泥泞破损；"
            "战友搀扶或独自穿越废墟。"
        ),
        "characters_en": (
            "retro war film soldier mud blood face WWII helmet, thousand yard stare, "
            "wool uniform smoke background Saving Private Ryan aesthetic, "
            "handheld chaos framing gritty grain battlefield trauma portrait"
        ),
        "scenes_zh": (
            "D-Day 海滩登陆混乱、战壕泥泞攻防、"
            "燃烧欧洲城市废墟、硝烟遮蔽战场、"
            "慢步穿越瓦砾街区。"
        ),
        "scenes_en": (
            "D-Day beach landing chaos handheld desaturated, muddy trench warfare smoke, "
            "burning European city rubble explosion orange flash, smoke obscured battlefield, "
            "slow walk through rubble thousand yard stare"
        ),
        "colors": "去饱和绿, 泥褐, 烟灰, 爆炸橙, 血红, 钢灰, 炭黑",
        "image_prompt": (
            "retro war film cinematography desaturated bleach bypass, muddy battlefield smoke, "
            "soldier thousand yard stare mud blood face, explosion orange flash handheld chaos framing, "
            "Saving Private Ryan 1917 aesthetic gritty grain, 4k theatrical"
        ),
        "video_prompt": (
            "explosion shock handheld shake smoke wipe, slow walk through rubble boots mud splash, "
            "smoke drift obscures frame battlefield, war trauma atmosphere motion gritty, "
            "flare burst orange desaturated grade lock"
        ),
        "references": [
            "Saving Private Ryan (1998)",
            "1917 (2019)",
            "Band of Brothers (2001)",
        ],
    },
    "retro_y2k_fantasy": {
        "summary": 'Y2K复古幻想：2000年代初 glitter、 chrome text、 bubble font 与 low-rise fashion 的 fantasy MV 美学。',
        "category": 'Y2K复古幻想',
        "artist_refs": 'early Britney MV、Paris Hilton era、PS2 game UI',
        "era_texture": '1999–2004 Y2K pop culture',
        "line_control": 'chrome bubble letter overlay',
        "lighting_color": 'ring flash+ gel color',
        "palette_strategy": 'silver pink baby blue',
        "atmosphere": 'playful、 glossy、 millennium optimism',
        "materials": 'glitter, plastic, flip phone',
        "quality": 'early HD glossy',
        "taboos": ' rustic organic,  dark horror,  ancient',
        "characters_zh": '低腰、 glitter makeup、 butterfly clip。',
        "characters_en": 'Y2K fantasy character, glitter makeup, butterfly hair clips, low rise futuristic outfit, chrome accessories, pop princess pose',
        "scenes_zh": ' infinity backdrop、 disco ball、 fake snow glitter set。',
        "scenes_en": 'Y2K infinity backdrop studio, disco ball sparkle, glitter snow set, chrome text floating, early 2000s music video stage',
        "colors": '银, 粉红, 婴儿蓝, 全息, 白',
        "image_prompt": 'retro Y2K fantasy aesthetic, glitter makeup chrome accessories, silver pink baby blue palette, disco ball sparkle, early 2000s music video stage, glossy ring flash, pop millennium optimism, 4k',
        "video_prompt": 'glitter burst overlay, disco ball spin lights, chrome text float in, Y2K hair flip slow motion, glossy pop fantasy motion',
        "references": [
        'Britney Spears Oops era MV',
        'Paris Hilton aesthetics',
        'Final Fantasy X promotional',
        ],
    },
    "shadow_puppet_illustration": {
        "summary": '皮影插画风格：侧视剪影、镂空纹样与暖幕布光。中国传统皮影戏视觉转译至静态插画与 motion 分镜。',
        "category": '皮影/剪影插画',
        "artist_refs": '陕西皮影、唐山皮影、《影之刃》美术',
        "era_texture": '传统皮影当代数码再设计',
        "line_control": '侧面剪影100%，镂空装饰',
        "lighting_color": '幕布暖光透射',
        "palette_strategy": '黑剪影+金红装饰+幕布橙',
        "atmosphere": ' folk、 myth、 theatrical',
        "materials": ' leather cut patterns, paper screen',
        "quality": '纹样清晰可辨',
        "taboos": ' 正面写实脸,  3D,  赛博',
        "characters_zh": '侧脸武将、仙女、妖怪，关节杆影可选。',
        "characters_en": 'Chinese shadow puppet character, profile silhouette cutout, ornate leather pattern armor, warm backlit screen, traditional opera pose',
        "scenes_zh": '幕布、宫殿剪影、战马、祥云镂空。',
        "scenes_en": 'shadow puppet theater screen glow, palace silhouette cutout, war horse profile shadow, cloud pattern leather lace background',
        "colors": '剪影黑, 幕布橙, 金漆, 朱红, 暖黄',
        "image_prompt": 'Chinese shadow puppet illustration, profile silhouette cutout, ornate leather lace patterns, warm backlit screen glow, traditional opera warrior, folk myth aesthetic, gold red decorative details, theatrical composition, 4k',
        "video_prompt": 'shadow puppet joint animation, warm screen light flicker, silhouette horse gallop profile, cloud pattern scroll move, traditional theater motion',
        "references": [
        '陕西皮影戏',
        '影之刃系列美术',
        '中国皮影博物馆',
        ],
    },
    "stop_motion": {
        "summary": '定格动画总风格：Laika/Coraline 式 puppet + 真实材质 lighting，帧间 intentional micro jitter。',
        "category": '定格动画',
        "artist_refs": 'Laika、Aardman、Tim Burton stop motion',
        "era_texture": 'contemporary feature stop motion',
        "line_control": 'puppet joint readable',
        "lighting_color": 'miniature set physical lights',
        "palette_strategy": 'set design color script',
        "atmosphere": 'handcrafted、 uncanny tactile',
        "materials": 'fabric, resin face, wire armature',
        "quality": 'feature film stop mo smoothness',
        "taboos": ' smooth CG without texture,  2D only',
        "characters_zh": ' puppet 面部 seam、 button eyes optional、 fabric clothes。',
        "characters_en": 'stop motion puppet character, visible fabric texture, replacement mouth animation ready, wire armature joints, handcrafted uncanny face',
        "scenes_zh": ' miniature house interior、 forest set、 workshop。',
        "scenes_en": 'miniature stop motion house interior, handcrafted forest set, workshop table puppet stage, tactile real materials',
        "colors": 'set design script, 暖木, 深绿, 暗红',
        "image_prompt": 'stop motion animation style, handcrafted puppet character, miniature set physical lighting, visible fabric and resin textures, intentional frame charm, Laika inspired design, tactile uncanny atmosphere, 4k',
        "video_prompt": 'stop motion walk cycle jitter, replacement mouth speak, miniature set camera slide, handcrafted puppet performance motion, tactile frame by frame charm',
        "references": [
        'Coraline (2009)',
        'Kubo and the Two Strings (2016)',
        'Fantastic Mr Fox (2009)',
        ],
    },
    "suspense_film": {
        "summary": (
            "悬疑电影风格：以 classic to contemporary thriller 高峰（Hitchcock《 Rear Window》"
            "Fincher《十二宫》《囚徒》Denis Villeneuve）为基准，呈现 framing 制造 suspense、"
            "frame 外 shadow threat 与 restrained color 并存的「unease + anticipation withheld」视觉语法。"
            "人物以 ordinary person wrong place、over shoulder 张望为核心；"
            "场景强调空停车场荧光灯、森林夜路车灯隧道、旅馆猫眼 POV。"
            "整体为 live-action clean thriller grade cinema，偏 desaturate+cool shadow LUT，"
            "绝不做 jump scare gore focus 或 bright comedy 主导。"
            "适合悬疑惊悚、犯罪调查、心理张力 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 悬疑电影（Suspense Film Thriller Cinematography Live-Action）",
        "artist_refs": (
            "导演：Alfred Hitchcock、David Fincher、Denis Villeneuve；"
            "作品：《 Rear Window》《十二宫》《囚徒》《消失的爱人》；"
            "美学：negative space framing、shadow threat outside frame、"
            "motivated practical low key、Dutch angle sparing、rain window paranoia。"
        ),
        "era_texture": (
            "classic to contemporary thriller digital clean grade；"
            "rain window streak、blind shadow stripe readable；"
            "fog atmospheric subtle 非 horror heavy；"
            "digital 须 preserve cool shadow detail 非 crushed muddy。"
        ),
        "line_control": (
            "构图 negative space + threat implied outside frame；"
            "Dutch angle sparing 仅高潮；"
            "parking garage fluorescent symmetry unease；"
            "movement：slow zoom window reflection、footstep echo hold。"
        ),
        "lighting_color": (
            "主光：motivated practical low key lamp/window；"
            "fluorescent overhead green-grey thriller；"
            "headlight tunnel forest road night；"
            "禁忌：bright comedy even fill、horror sick green dominant、neon cyber pop。"
        ),
        "palette_strategy": (
            "主调：冷灰、去饱和、危险黄灯、雨夜蓝、黑影；"
            "desaturate cool shadow base；"
            "danger yellow fluorescent accent；"
            "肤色 natural uneasy 非 glamour。"
        ),
        "atmosphere": (
            "unease、anticipation、reveal withheld、paranoia；"
            "雨声、脚步回声、荧光灯嗡鸣（视觉：rain streak、shadow pass edge）；"
            "suspense hold without jump 是核心；"
            "非 gore splatter horror franchise。"
        ),
        "materials": (
            "rain window glass、venetian blind shadow、"
            "concrete parking garage、motel peephole metal、"
            "forest road wet asphalt、staircase shadow；"
            "忌 pastel romance fabric、neon cyber dominant。"
        ),
        "quality": (
            "悬疑惊悚院线级：rain refraction、shadow edge sharp；"
            "fluorescent cast consistent；"
            "4K clean thriller，thumbnail 可辨 paranoia framing 与 cool grade。"
        ),
        "taboos": (
            "jump scare gore focus、bright comedy sitcom、"
            "epic blockbuster explosion、anime cartoon、pastel kawaii。"
        ),
        "characters_zh": (
            "ordinary clothes 普通人 wrong place；"
            "uneasy expression looking over shoulder；"
            "rain window reflection paranoia 双影；"
            "thriller protagonist 疲惫警觉。"
        ),
        "characters_en": (
            "suspense film character ordinary clothes uneasy expression, "
            "looking over shoulder paranoia, rain window reflection thriller protagonist, "
            "Hitchcock framing negative space low key motivated lighting"
        ),
        "scenes_zh": (
            "空停车场荧光灯、森林夜路车灯隧道、"
            "旅馆猫眼 POV、悬疑楼梯阴影、"
            "雨夜窗框张望。"
        ),
        "scenes_en": (
            "empty parking garage fluorescent unease symmetry, forest road headlight tunnel night, "
            "motel peephole POV suspense, staircase shadow thriller framing, "
            "rain window paranoia reflection hold"
        ),
        "colors": "冷灰, 去饱和, 危险黄灯, 雨夜蓝, 黑影, 荧白, 湿沥青黑",
        "image_prompt": (
            "suspense film cinematography Hitchcock framing negative space, "
            "low key motivated lighting ordinary figure paranoia, rain window reflection, "
            "desaturated cool thriller grade anticipation without reveal, Fincher Prisoners inspired, 4k"
        ),
        "video_prompt": (
            "slow zoom into window reflection paranoia, shadow pass edge of frame, "
            "footstep echo empty garage hold, suspense without jump scare beat, "
            "thriller tension motion rain streak drift"
        ),
        "references": [
            "Rear Window (1954)",
            "Prisoners (2013)",
            "Zodiac (2007)",
        ],
    },
    "teal_orange_cinematic": {
        "summary": (
            "蓝橙色调影视风格：以 2005–2020s Hollywood blockbuster grading 标准（Michael Bay、"
            "Marvel color pipeline、《疯狂的麦克斯4》互补色参考）为基准，呈现 skin orange vs shadow teal、"
            "sunset rim 与 anamorphic flare 并存的「epic commercial adrenaline」视觉语法。"
            "人物以 action hero 汗渍橙肤、青影下颌为核心；"
            "场景强调城市日落、直升机追逐、爆炸逆光烟尘。"
            "整体为 live-action IMAX blockbuster polish cinema，偏 complementary orange-teal strict LUT，"
            "绝不做 natural neutral documentary 或 pastel indie only 主导。"
            "适合商业大片、动作英雄、都市史诗 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 蓝橙电影调（Teal Orange Cinematic Blockbuster Live-Action）",
        "artist_refs": (
            "导演：Michael Bay《变形金刚》、Marvel Avengers pipeline；"
            "摄影：blockbuster colorists teal-orange standard；"
            "参照：《疯狂的麦克斯4》grade refs、anamorphic hero sunset；"
            "美学：orange skin sunset rim、teal shadow jaw、wide anamorphic flare。"
        ),
        "era_texture": (
            "2005–2020s blockbuster default IMAX polish；"
            "lens flare anamorphic streak、smoke backlit particle；"
            "chrome specular hero portrait；"
            "digital 须 emulate commercial grade 非 documentary flat neutral。"
        ),
        "line_control": (
            "构图 wide anamorphic heroes low angle；"
            "city sunset vanishing line helicopter pass；"
            "explosion backlit silhouette hero walk；"
            "movement：slow motion hero walk、helicopter pass smoke teal。"
        ),
        "lighting_color": (
            "主光：sunset orange rim on skin；"
            "shadow 与背景 teal/cyan fill；"
            "explosion white highlight + teal shadow contrast；"
            "禁忌：natural neutral doc flat、pastel indie desaturated only、flat office LED。"
        ),
        "palette_strategy": (
            "主调：橙肤、青影、暮金、烟灰、爆炸白；"
            "complementary orange teal strict split；"
            "skin orange highlight shadow teal jaw line；"
            "night 场景 city teal ambient + warm practical orange。"
        ),
        "atmosphere": (
            "epic、commercial、adrenaline、heroic spectacle；"
            "引擎轰鸣、爆炸冲击、直升机掠过（视觉：flare sweep、smoke teal）；"
            "blockbuster confidence 非 indie melancholy；"
            "triumph 与 destruction 可并存。"
        ),
        "materials": (
            "lens flare glass、smoke particle、chrome car、"
            "leather jacket action hero、helicopter metal、"
            "urban glass reflection sunset；"
            "忌 rustic organic only、ancient stone only、flat cartoon。"
        ),
        "quality": (
            "IMAX blockbuster polish 级：flare streak、skin orange grade consistent；"
            "smoke backlit particle readable；"
            "4K theatrical，thumbnail 可辨 orange-teal split 与 hero silhouette。"
        ),
        "taboos": (
            "natural neutral documentary only、pastel indie grey only、"
            "horror sick green dominant、anime cel flat。"
        ),
        "characters_zh": (
            "action hero 汗渍橙肤、青影下颌轮廓；"
            "皮革夹克或战术装 sunset rim；"
            "anamorphic flare 勾轮廓；"
            "表情 determined fierce 或 slow-mo walk cool。"
        ),
        "characters_en": (
            "teal orange cinematic hero sunset rim light orange skin, "
            "teal shadow contrast jaw blockbuster action portrait, "
            "anamorphic lens flare Michael Bay inspired adrenaline presence"
        ),
        "scenes_zh": (
            "城市日落 anamorphic、直升机追逐橙天、"
            "爆炸逆光烟尘青影、英雄慢步街道、"
            "高架桥车流暮光互补色。"
        ),
        "scenes_en": (
            "city sunset anamorphic flare orange sky, helicopter chase smoke teal shadows, "
            "explosion backlit hero silhouette slow motion, blockbuster urban action orange teal grade, "
            "overpass traffic twilight complementary color"
        ),
        "colors": "橙肤, 青影, 暮金, 烟灰, 爆炸白, 暮蓝青, 沥青黑",
        "image_prompt": (
            "teal orange cinematic color grade blockbuster sunset rim light, "
            "anamorphic lens flare hero portrait orange skin teal shadows, "
            "Michael Bay inspired action atmosphere IMAX commercial polish, 4k theatrical"
        ),
        "video_prompt": (
            "sunset orange teal grade lock consistent, anamorphic flare sweep across frame, "
            "helicopter pass smoke teal drift, blockbuster hero walk slow motion, "
            "adrenaline cinema motion explosion backlit flash"
        ),
        "references": [
            "Transformers (2007)",
            "Mad Max Fury Road grade refs",
            "Marvel Avengers look",
        ],
    },
    "tech_cinematic": {
        "summary": (
            "科技感电影风格：以 2010s near-future cinema（《机械姬》《她》、"
            "Apple keynote films、Denis Villeneuve《降临》clean 段落）为基准，呈现 white space、"
            "glass 与 soft UI glow 并存的「calm intelligent futurism」视觉语法。"
            "人物以 minimalist fashion、earpiece、calm tech worker 为核心；"
            "场景强调玻璃办公室、AI 白室、洁净实验室、悬浮 UI。"
            "整体为 live-action pristine commercial cinema，偏白灰+单 accent 色 LUT，"
            "绝不做 gritty war、巴洛克宫廷或 cartoon 主导。"
            "适合近未来科幻、科技品牌片、AI 叙事 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 科技感未来电影（Tech Cinematic Near-Future Live-Action）",
        "artist_refs": (
            "导演：Alex Garland《机械姬》、Spike Jonze《她》；"
            "Denis Villeneuve《降临》clean lab；"
            "Apple product films aesthetic；"
            "美学：symmetry minimal、soft top light+screen glow、"
            "glass brushed aluminum、holographic UI subtle。"
        ),
        "era_texture": (
            "2010s near-future cinema digital pristine；"
            "glass reflection、brushed aluminum grain subtle；"
            "holographic UI glow soft 非 cyber neon overload；"
            "digital 须 emulate commercial pristine 非 gritty documentary。"
        ),
        "line_control": (
            "构图 symmetry minimal center or rule thirds clean；"
            "glass corridor vanishing line slow push；"
            "AI chamber white void figure small；"
            "movement：slow push glass corridor、holographic UI fade in。"
        ),
        "lighting_color": (
            "主光：soft top diffuse + screen glow face fill；"
            "accent：single color UI blue or green subtle；"
            "wood warm dot 于白灰空间；"
            "禁忌：gritty war sodium、baroque palace candle、neon cyber purple overload。"
        ),
        "palette_strategy": (
            "主调：白、浅灰、屏幕蓝、木点缀、黑细线；"
            "white grey dominate 80%+；"
            "single accent color locked per scene；"
            "肤色 natural calm 非 glamour neon。"
        ),
        "atmosphere": (
            "calm、intelligent、slightly uncanny、serene futurism；"
            "屏幕低鸣、玻璃反光、UI 淡入（视觉：holographic fade、reflection drift）；"
            "Ex Machina isolation 与 Her warmth 可并存；"
            "非 action blockbuster adrenaline。"
        ),
        "materials": (
            "glass panel、brushed aluminum、holographic UI layer、"
            "minimalist furniture、earpiece plastic、clean lab epoxy floor；"
            "忌 rust industrial、velvet palace、synthetic neon sign。"
        ),
        "quality": (
            "商业科技片 pristine 级：glass edge、UI glow edge sharp；"
            "reflection mathematically clean；"
            "4K commercial，thumbnail 可辨 white space 与 glass symmetry。"
        ),
        "taboos": (
            "gritty war mud、baroque palace ornament、cartoon anime、"
            "horror sick green、cyber neon alley dominant。"
        ),
        "characters_zh": (
            "minimalist fashion 近未来剪裁；"
            "earpiece 或 subtle wearable tech；"
            "calm intelligent 表情 slightly uncanny optional；"
            "玻璃环境倒影中的 professional。"
        ),
        "characters_en": (
            "tech cinematic character minimalist futuristic fashion, calm intelligent expression, "
            "glass office environment reflection near future professional, "
            "Ex Machina Her inspired clean white grey aesthetic soft UI glow"
        ),
        "scenes_zh": (
            "极简玻璃未来办公室、AI 纯白室、"
            "洁净实验室全息 UI、对称未来建筑走廊、"
            "屏幕光人脸补光室内。"
        ),
        "scenes_en": (
            "minimalist glass future office symmetry, AI white chamber void clean, "
            "clean laboratory holographic UI subtle glow, near future architecture corridor slow push, "
            "screen glow face fill tech interior pristine"
        ),
        "colors": "白, 浅灰, 屏幕蓝, 木点缀, 黑细线, 淡绿UI, 银铝",
        "image_prompt": (
            "tech cinematic near future minimalist glass architecture, soft UI glow clean white grey palette, "
            "calm intelligent atmosphere Ex Machina inspired design, holographic interface subtle, "
            "commercial pristine quality Apple film aesthetic, 4k"
        ),
        "video_prompt": (
            "slow push clean glass corridor reflection, holographic UI fade in subtle, "
            "soft screen glow pulse calm, minimalist future office drift serene, "
            "calm tech atmosphere motion pristine"
        ),
        "references": [
            "Ex Machina (2014)",
            "Her (2013)",
            "Apple product films",
        ],
    },
    "traditional_ink_wash": {
        "summary": '传统水墨风格：工笔与写意结合，彩色淡染可选。山水、花鸟、人物一体，强调留白与气韵。',
        "category": '传统水墨/国画',
        "artist_refs": '张大千、吴冠中、故宫院体画',
        "era_texture": '传统国画当代数码再现',
        "line_control": '书法性笔锋，骨法用笔',
        "lighting_color": '无光源，墨阶与染色',
        "palette_strategy": '墨+石青石绿朱赭',
        "atmosphere": '诗意、文人、禅境',
        "materials": '宣纸、绢本、飞白枯笔',
        "quality": '墨不脏不板，留白透气',
        "taboos": ' 3D,  anime cel,  neon,  photoreal photo',
        "characters_zh": '仕女、高士、渔樵，衣纹游丝描。',
        "characters_en": 'traditional Chinese ink wash figure, flowing robe brush lines, scholar or lady painting style, poetic gesture minimal detail, xieyi gongbi blend',
        "scenes_zh": '江山万里、松瀑云泉、江南小景。',
        "scenes_en": 'traditional ink landscape mountains mist, pine waterfall clouds, Jiangnan village soft wash, scroll composition empty space',
        "colors": '墨, 石青, 石绿, 朱, 赭, 留白',
        "image_prompt": 'traditional Chinese ink wash painting, mountains mist poetic landscape, brush calligraphy linework, mineral color subtle wash, rice paper texture, scholar figure optional, scroll composition empty space, museum quality art, 4k',
        "video_prompt": 'ink brush stroke animate across scroll, mist reveal mountains, gentle water ripple wash painting, poetic empty space hold, traditional art motion',
        "references": [
        '千里江山图',
        '富春山居图',
        '吴冠中江南',
        ],
    },
    "ue5_realistic_render": {
        "summary": 'UE5写实渲染：Nanite+Lumen 实时电影级，MetaHuman 可选。虚拟制片与游戏 cinematics 的标杆 look。',
        "category": 'UE5写实渲染',
        "artist_refs": 'Epic Lumen in the Land of Nanite、Matrix Awakens、国内虚拟制片',
        "era_texture": '2022–2025 Unreal Engine 5 era',
        "line_control": 'photographic composition',
        "lighting_color": 'Lumen global illumination real time',
        "palette_strategy": 'natural HDR environment',
        "atmosphere": 'immersive、 next gen real time',
        "materials": 'Nanite micro detail, MetaHuman skin',
        "quality": 'real time 4K cinematic',
        "taboos": ' toon shader,  obvious game UI,  low poly',
        "characters_zh": ' MetaHuman 级皮肤， modern clothing。',
        "characters_en": 'UE5 MetaHuman character, realistic skin pores, modern casual outfit, Lumen lit portrait, next gen game cinematic quality',
        "scenes_zh": ' city block Nanite、 forest Lumen、 interior bounce light。',
        "scenes_en": 'UE5 Nanite city block detail, forest Lumen global illumination, realistic interior bounce light, next gen virtual production set',
        "colors": '自然HDR, 肤写实, 环境反射准确',
        "image_prompt": 'Unreal Engine 5 realistic render, Lumen global illumination, Nanite micro geometry detail, MetaHuman quality skin, cinematic real time lighting, next gen virtual production, photorealistic environment, 4k real time cinematic',
        "video_prompt": 'real time Lumen lighting change, camera flythrough Nanite city, MetaHuman subtle expression, UE5 cinematic sequence motion, next gen real time quality',
        "references": [
        'The Matrix Awakens UE5 demo',
        'Epic Valley of the Ancient',
        '国内UE5虚拟制片案例',
        ],
    },
    "vaporwave_illustration": {
        "summary": '蒸汽波插画：VHS glitch、 marble bust、 palm sunset grid 与 80s consumer nostalgia 讽刺美学。',
        "category": '蒸汽波插画',
        "artist_refs": 'Macintosh Plus aesthetic、James Ferraro visual、Poolside FM',
        "era_texture": '2010s internet vaporwave art',
        "line_control": 'Greek bust+ digital glitch',
        "lighting_color": 'sunset gradient+ scanline',
        "palette_strategy": 'pink purple cyan',
        "atmosphere": 'nostalgic、 ironic、 liminal',
        "materials": 'marble, chrome, VHS noise',
        "quality": 'intentional compression artifact ok',
        "taboos": ' clean corporate,  historical accuracy',
        "characters_zh": ' bust statue、 anime eyes overlay optional、 90s fashion。',
        "characters_en": 'vaporwave illustration figure, marble bust glitch, 90s sunglasses, pink purple sunset grid background, ironic nostalgia pose',
        "scenes_zh": ' palm grid sunset、 mall aquarium、 windows 95 desktop。',
        "scenes_en": 'vaporwave palm tree sunset grid, marble bust on checkered floor, VHS glitch mall aquarium, retro computer desktop surreal',
        "colors": '粉, 紫, 青, 日落橙, VHS噪点',
        "image_prompt": 'vaporwave illustration, marble bust glitch artifact, pink purple cyan sunset grid, palm tree silhouette, VHS scanlines, 80s consumer nostalgia ironic aesthetic, surreal liminal composition, 4k',
        "video_prompt": 'VHS tracking glitch loop, sunset grid scroll, marble bust slow spin, vaporwave color shift pulse, liminal nostalgic motion',
        "references": [
        'Macintosh Plus Floral Shoppe',
        'Poolside FM visuals',
        'James Ferraro Far Side Virtual',
        ],
    },
    "vintage_industrial_film": {
        "summary": (
            "老式工业影视风格：以 1920s–1970s 工业纪录片与苏联蒙太奇（Dziga Vertov《持摄影机的人》、"
            "早期工厂宣传片、王兵《铁西区》工厂段落）为基准，呈现巨构机器、"
            "蒸汽煤烟与 montage dynamic angle 并存的「labor hymn + monumental modernity」视觉语法。"
            "人物以工人集体、操作杠杆、早期安全帽为主；"
            "场景强调炼钢 montage、大坝施工、蒸汽火车挂钩、烟囱天际线。"
            "整体为 live-action archival B&W 或 early faded color documentary cinema，"
            "偏 steel grey + coal black LUT，绝不做 fantasy magic、romcom 或 digital clean 主导。"
            "适合工业史诗、劳动纪实、历史现代性 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 老式工业纪录片电影（Vintage Industrial Film Documentary Live-Action）",
        "artist_refs": (
            "导演：Dziga Vertov、早期苏联工业片、王兵《铁西区》；"
            "美学：montage dynamism、monumental machine scale、"
            "labor heroism documentary、factory interior hard lamp；"
            "作品：《持摄影机的人》、早期炼钢纪录片、王兵工厂片段。"
        ),
        "era_texture": (
            "1920s–1970s industrial documentary archival film；"
            "B&W 或 early faded color dye transfer；"
            "visible film grain、gate weave、scratch optional subtle；"
            "steam、coal smoke、oil smear on metal readable；"
            "digital 须 emulate archival 非 clean modern HDR。"
        ),
        "line_control": (
            "构图 montage dynamic angles：low under gear、high crane over factory；"
            "symmetry 于大坝/烟囱 monumental scale；"
            "close-up 挂钩、齿轮、汗水面孔 rapid cut rhythm；"
            "movement：crane sweep、train approach、steam blast。"
        ),
        "lighting_color": (
            "主光：工厂硬灯+高窗 dust beam；"
            "室外：overcast industrial yard 或 sun through smoke；"
            "B&W 高 contrast 或 early color faded ochre rust；"
            "禁忌：romcom soft fill、fantasy glow、neon cyber、clean studio white。"
        ),
        "palette_strategy": (
            "主调：黑白或褪色、钢灰、煤黑、锈红、烟尘褐；"
            "B&W 时 highlight 轧钢火花作唯一 bright accent；"
            "early color 偏 faded ochre 与 rust；"
            "肤色劳作红晕非 glamour peach。"
        ),
        "atmosphere": (
            "modernity、labor hymn、monumental、集体英雄主义与机器崇拜；"
            "蒸汽喷发、火车轰鸣、齿轮转动（视觉：steam blast、sparks fly）；"
            "documentary urgency 非 fiction melodrama；"
            "industrial sublime 是核心情绪符号。"
        ),
        "materials": (
            "steel gears、steam pipe、coal pile、"
            "早期安全帽、帆布工装、生锈铁轨、"
            "大坝混凝土、烟囱砖；"
            "忌 silk palace、glass skyscraper modern clean。"
        ),
        "quality": (
            "档案胶片还原级：grain、contrast、archival texture；"
            "metal specular 与 steam diffusion readable；"
            "4K scan 感保留 vintage artifact，thumbnail 可辨机器 scale 与 smoke。"
        ),
        "taboos": (
            "fantasy magic、romcom gloss、digital clean modern office、"
            "cyber neon、palace costume、3D cartoon。"
        ),
        "characters_zh": (
            "工人集体：操作巨杆、挂钩火车；"
            "早期帆布工装、安全帽、汗渍油污面孔；"
            "群像 montage 非单人明星 portrait 主导；"
            "劳动姿态有力、面向机器或镜头坚定。"
        ),
        "characters_en": (
            "vintage industrial film worker collective, operating massive machine levers, "
            "early hard hat canvas work clothes, documentary labor heroism, "
            "oil sweat on face steel mill, Dziga Vertov montage dynamism, "
            "monumental factory scale presence"
        ),
        "scenes_zh": (
            "炼钢厂 montage 齿轮蒸汽、大坝施工 monumental、"
            "蒸汽火车挂钩特写、工厂烟囱烟雾天际线、"
            "煤矿轨道推车集体。"
        ),
        "scenes_en": (
            "vintage steel mill montage massive gears steam sparks, "
            "dam construction monumental crane concrete, "
            "steam train coupling close impact, factory chimney smoke skyline, "
            "coal mine rail cart worker collective archival grain"
        ),
        "colors": "黑白或褪色, 钢灰, 煤黑, 锈红, 烟尘褐, 火花橙白",
        "image_prompt": (
            "vintage industrial film aesthetic, black white or faded early color factory, "
            "massive steel gears steam coal smoke, documentary labor monumental angles, "
            "archival film grain texture scratch, Dziga Vertov inspired montage dynamism, "
            "steel mill sparks hard factory light, 4k archival scan"
        ),
        "video_prompt": (
            "montage quick cut machines rhythm, steam blast rhythmic pulse, "
            "train coupling impact close, factory chimney smoke rise continuous, "
            "crane sweep over dam construction, vintage industrial documentary motion"
        ),
        "references": [
            "Man with a Movie Camera (1929)",
            "早期工业纪录片",
            "王兵工厂片段",
        ],
    },
    "western_stylized_3d": {
        "summary": '西部风格化3D：Rango/Red Dead stylized 式 desert frontier，夸张脸型与 gritty fairy tale western。',
        "category": '西部风格化3D',
        "artist_refs": 'Rango film、Red Dead Redemption art、Spaghetti western homages',
        "era_texture": '2010s stylized western animation/game',
        "line_control": 'cracked lips big eyes stylized',
        "lighting_color": 'harsh desert sun+ long shadow',
        "palette_strategy": 'dust orange+ turquoise sky',
        "atmosphere": 'gritty、fairy tale、 frontier myth',
        "materials": 'weathered leather, wood, sand particles',
        "quality": 'film or AAA game cinematic',
        "taboos": ' cyber city,  East Asian palace,  moe',
        "characters_zh": ' cowboy hat、 poncho、 squint eyes、 revolver。',
        "characters_en": 'stylized 3D western character, cracked skin squint eyes, cowboy hat poncho, revolver holster, gritty frontier hero design',
        "scenes_zh": ' desert town、 canyon duel sunset、 saloon swing door。',
        "scenes_en": 'stylized western desert town, canyon duel sunset long shadows, saloon swinging doors dust, tumbleweed frontier main street',
        "colors": '尘橙,  Turquoise sky,  leather棕,  blood sunset,  sand黄',
        "image_prompt": 'stylized 3D western scene, gritty cowboy character design, harsh desert sun long shadows, dusty frontier town, Rango inspired aesthetic, turquoise sky orange sand, fairy tale western atmosphere, cinematic 4k',
        "video_prompt": 'tumbleweed roll main street, saloon door swing dust puff, cowboy squint sun beat, stylized western standoff tension, desert wind motion',
        "references": [
        'Rango (2011)',
        'Red Dead Redemption 2 stylized art',
        'The Good the Bad and the Ugly homages',
        ],
    },
    "wilderness_cinematic": {
        "summary": (
            "荒野电影风格：以 contemplative nature cinema 高峰（Terrence Malick《生命之树》《天堂之战》、"
            "Emmanuel Lubezki magic hour、《荒野生存》《荒野猎人》自然段落）为基准，"
            "呈现 Steadicam 穿草、magic hour 与 vast landscape tiny human 并存的 "
            "「spiritual awe + solitude」视觉语法。"
            "人物以 vast landscape 中小身影、自然发丝无 glam、羊毛衫徒步者为核心；"
            "场景强调麦田奔跑、河流洗礼、山巅云雾、森林阳光柱。"
            "整体为 live-action large format nature cinema，偏 green-gold natural LUT，"
            "绝不做 urban neon、studio sitcom 或 cartoon 主导。"
            "适合自然史诗、精神沉思、户外生存 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 荒野自然电影（Wilderness Cinematic Nature Film Live-Action）",
        "artist_refs": (
            "导演：Terrence Malick、Sean Penn《荒野生存》；"
            "摄影：Emmanuel Lubezki magic hour、Rodrigo Prieto；"
            "作品：《生命之树》《天堂之战》《荒野生存》《荒野猎人》自然段；"
            "美学：Steadicam through grass、magic hour golden green、"
            "vast landscape human small、river mist forest、spiritual voiceover visual companion。"
        ),
        "era_texture": (
            "contemplative nature cinema large format clarity；"
            "wind grass motion blur、river mist soft、 bark texture readable；"
            "magic hour soft rolloff、overcast forest diffuse；"
            "digital 须 emulate film natural warmth 非 oversharpen HDR leaves。"
        ),
        "line_control": (
            "构图 wide vast landscape 人物极小；"
            "Steadicam low through wheat grass forward motion；"
            "forest sun shaft vertical emphasis；"
            "back to camera contemplative figure common；"
            "movement：run through field、river flow follow、cloud wrap timelapse。"
        ),
        "lighting_color": (
            "主光：magic hour golden 或 overcast soft forest；"
            "sun shaft through trees dust motes；"
            "river reflection sky gradient；"
            "禁忌：urban neon、studio three-point sitcom、flat office LED。"
        ),
        "palette_strategy": (
            "主调：草绿、麦金、河蓝、云白、树皮褐；"
            "green gold natural dominant，sky gradient warm to cool；"
            "肤色自然 wind-chapped 无 makeup glam；"
            "night campfire 延续 earth tone anchor。"
        ),
        "atmosphere": (
            "awe、solitude、spiritual、existential wonder；"
            "风声草浪、河水、鸟鸣（视觉：grass wave、mist drift）；"
            "whisper voiceover 视觉 companion 静谧节奏；"
            "非 action survival grit only（除非子类型标注）。"
        ),
        "materials": (
            "wind grass、river mist、树皮 texture、"
            "羊毛衫、帆布背包、赤脚泥土、"
            "麦田穗、山石苔藓；"
            "忌 glass skyscraper、neon sign、plastic urban。"
        ),
        "quality": (
            "large format nature 院线级：leaf、water、cloud detail readable；"
            "magic hour gradient smooth；"
            "4K theatrical，thumbnail 可辨 vast scale 与 golden green mood。"
        ),
        "taboos": (
            "urban neon dominant、studio sitcom lighting、cartoon、"
            "cyber punk、palace interior、flat smartphone indoor。"
        ),
        "characters_zh": (
            "vast landscape 中小身影、背对镜头沉思；"
            "自然发丝风吹无 glam、羊毛衫徒步装；"
            "赤脚或登山靴、帆布背包；"
            "表情 contemplative awe 非 action fierce 主导。"
        ),
        "characters_en": (
            "wilderness cinematic figure small in vast landscape, "
            "natural hair wind blown no glamour makeup, contemplative back to camera, "
            "hiking wool sweater canvas backpack, Terrence Malick magic hour presence, "
            "spiritual awe solitude expression"
        ),
        "scenes_zh": (
            "magic hour 麦田风吹、河流雾气森林、"
            "山巅云雾缠绕、森林阳光柱 dust motes、"
            "草原远景孤树。"
        ),
        "scenes_en": (
            "magic hour wheat field wind Steadicam path, river mist forest soft light, "
            "mountain peak cloud wrap timelapse, sun shaft through tall trees dust particles, "
            "vast prairie lone tree tiny human figure wilderness scale"
        ),
        "colors": "草绿, 麦金, 河蓝, 云白, 树皮褐, 苔藓绿, 夕阳橙金",
        "image_prompt": (
            "wilderness cinematic nature, magic hour golden grass field wind, "
            "vast landscape tiny human figure scale, Terrence Malick Lubezki inspired light, "
            "wind blown trees river mist spiritual awe, large format nature clarity, "
            "green gold natural palette contemplative atmosphere, 4k theatrical"
        ),
        "video_prompt": (
            "Steadicam run through wheat grass forward, river water flow close follow, "
            "cloud wrap mountain timelapse slow, sun shaft forest drift dust motes, "
            "contemplative wilderness motion spiritual pace"
        ),
        "references": [
            "The Tree of Life (2011)",
            "The Revenant (2015)",
            "Into the Wild (2007)",
        ],
    },
    "wuxia_realistic_photo": {
        "summary": (
            "武侠江湖写实摄影风格：以 2000s 香港武侠电影高峰（《卧虎藏龙》《英雄》《十面埋伏》"
            "徐克《笑傲江湖》系列、Peter Pau 摄影）写实摄影美学为基准，"
            "呈现真外景自然光、丝绸 wind、竹雨与 wet stone 并存的 "
            "「martial romanticism + film photography grain」视觉语法。"
            "人物以侠客长袍束发、剑穗飘、轻功滞空瞬间为核心；场景强调竹林雨战、"
            "沙漠对决、湖面镜影、屋顶月夜。整体为 live-action 35mm martial cinema，"
            "可选张艺谋式 monochromatic hero color panel，绝不做 pure anime、现代都市或 gore horror。"
            "适合武侠、江湖、古装动作 AIGC 的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 武侠江湖写实（Wuxia Realistic Photography Live-Action）",
        "artist_refs": (
            "导演：李安、张艺谋、徐克、袁和平动作设计；"
            "摄影：Peter Pau、吕乐、赵小丁；"
            "作品：《卧虎藏龙》《英雄》《十面埋伏》《笑傲江湖》《新龙门客栈》；"
            "美学：wide martial composition、wirework grace frozen frame、"
            "natural location rain wind、optional monochromatic color staging。"
        ),
        "era_texture": (
            "2000s wuxia cinema peak 35mm film grain sharp action freeze；"
            "silk fabric motion blur 与 rain streak；"
            "沙漠 heat haze、bamboo mist、lake mirror calm；"
            "digital 须 retain film contrast 与 skin texture，no plastic smooth。"
        ),
        "line_control": (
            "构图 wide martial arts tableau，人物占 frame 动态对角；"
            "竹林用 vertical line 与 falling rain depth；"
            "沙漠 duel 极简 horizon；"
            "轻功 freeze frame mid-air silk spread，少 shaky cam chaos。"
        ),
        "lighting_color": (
            "主光：natural location sun/cloud + color gel panel optional（张艺谋红/黄/蓝幕）；"
            "雨战：diffused grey + sword metal flash；"
            "月夜：cool blue moon rim + warm lantern accent；"
            "禁忌：flat office LED、cyber neon、modern street lamp only。"
        ),
        "palette_strategy": (
            "自然场景：竹青、雨灰、侠黑、血红点缀、沙漠金；"
            "英雄式单色幕：整场景 dominant red/yellow/blue with black costume；"
            "肤色真实晒痕，lip natural not glamour；"
            "水面倒影场景降 saturation 保 mirror symmetry。"
        ),
        "atmosphere": (
            "romantic martial、gravity defying grace、江湖义气与孤独；"
            "竹叶飘落、剑气与雨滴（视觉：silk flutter、ripple）；"
            "epic stillness before clash；"
            "诗意而非 blood splatter horror。"
        ),
        "materials": (
            "丝绸长袍、竹、湿石、剑金属、"
            "斗笠、马鞍、红布幔、寺庙木瓦；"
            "忌 modern synthetic sportswear、sci-fi armor、cartoon outline。"
        ),
        "quality": (
            "武侠大片摄影级：fabric weave 与 rain droplet on blade readable；"
            "action freeze sharp without CGI rubber feel；4K film scan quality。"
        ),
        "taboos": (
            "pure anime cel shading、modern urban street、horror gore splatter、"
            "cyberpunk、western cowboy default、3D game plastic。"
        ),
        "characters_zh": (
            "侠客：束发长袍、腰带剑穗、斗笠或面纱；"
            "轻功空中展袍、剑指前方；"
            "女侠红衣/白衣、男侠黑衣或青衫；"
            "肤质真实，风吹乱发，表情英气或凄美。"
        ),
        "characters_en": (
            "wuxia realistic martial hero, flowing silk robes wind motion, "
            "jian sword bamboo forest rain, mid air wirework graceful pose frozen, "
            "natural skin film photography grain, Zhang Yimou Hero color staging optional, "
            "cinematic martial arts composition Ang Lee aesthetic"
        ),
        "scenes_zh": (
            "竹林雨战、沙漠橙幕对决、湖面镜影对峙、"
            "寺庙屋顶月夜、瀑布练功、客栈灯笼巷战、戈壁骑马远景。"
        ),
        "scenes_en": (
            "bamboo forest rain sword fight wet stone, desert orange monochromatic duel wide, "
            "lake mirror reflection wuxia standoff, temple roof moonlight silhouette, "
            "waterfall mist martial training, inn lantern alley combat, "
            "Gobi horsemen epic horizon"
        ),
        "colors": "竹青, 雨灰, 侠黑, 血红点缀, 沙漠金, 月夜靛蓝, 灯笼琥珀",
        "image_prompt": (
            "wuxia realistic photography martial arts cinema, silk robes wind motion, "
            "bamboo forest rain sword fight, natural skin 35mm film grain, "
            "Hero Zhang Yimou monochromatic color staging optional, "
            "gravity defying graceful mid air pose, cinematic wide martial composition, "
            "wet stone and fabric detail, 4k"
        ),
        "video_prompt": (
            "silk robe wind slow motion arc, rain bamboo sword clash sparks, "
            "lake surface ripple mirror reflection, rooftop moonlight standoff drift, "
            "desert orange dust swirl martial step, wuxia graceful combat motion"
        ),
        "references": [
            "Crouching Tiger Hidden Dragon (2000)",
            "Hero (2002)",
            "House of Flying Daggers (2004)",
            "新龙门客栈 (1992)",
        ],
    },
    "shaw_brothers_cinema": {
        "summary": (
            "邵氏电影风格：以 1960s–1980s 香港邵氏兄弟（Shaw Brothers / Shawscope）片厂美学为基准，"
            "呈现高饱和 Eastmancolor、影棚布景、硬光照明与武侠/古装类型片并存的「studio martial opera + golden age HK cinema」视觉语法。"
            "人物以京剧化妆面、华丽古装、束发冠饰与清晰武打 staging 为核心；场景强调邵氏清水湾片厂宫廷、"
            "客栈大堂、竹林假景与红幕金柱。整体为 live-action 宽银幕电影摄影，偏 bold primary color + hard studio key，"
            "绝不做 90 年代旺角霓虹、2000s 自然光武侠艺术片或日系动漫化。"
            "适合港式武侠、古装动作、江湖传奇向 AIGC 短剧的角色定妆、场景氛围与分镜参考。"
        ),
        "category": "真人电影摄影 / 邵氏兄弟片厂（Shaw Brothers Studio Cinema Live-Action）",
        "artist_refs": (
            "邵氏兄弟（Run Run Shaw）清水湾片厂；"
            "导演：张彻、胡金铨、李翰祥、楚原、刘家良；"
            "摄影：邵氏摄影组 Shawscope 2.35:1 宽银幕；"
            "作品：《大醉侠》《独臂刀》《五毒》《少林三十六房》《江山美人》《梁山伯与祝英台》《洪熙官》；"
            "美学：影棚硬光、高饱和 Eastmancolor、京剧化武戏 staging、宫廷/江湖布景。"
        ),
        "era_texture": (
            "1960s–1980s 香港邵氏片厂黄金期，35mm Eastmancolor / Shawcolor 饱和胶片感；"
            "可见 studio set 平面透视与 backlot 假景，非自然光外景纪录片；"
            "武打场面 frame 清晰、动作可读，少 handheld chaos；"
            "digital 须 emulate film：bold saturation、hard shadow edge、轻微 grain，避免 HDR 过亮与网红磨皮。"
        ),
        "line_control": (
            "构图以宽银幕 2.35:1 horizontal staging 为主，人物与群像排布如舞台 tableau；"
            "武打：full body readable，少 rapid cut 糊影；"
            "宫廷/客栈：对称或纵深柱廊，人物居中或三角站位；"
            "胡金铨式：纵深空间与门窗框景；张彻式：群侠列阵、血色对比；"
            "少 shaky cam，多用 locked-off 或 slow dolly 展示 choreography。"
        ),
        "lighting_color": (
            "主光：影棚 hard key + strong fill（高键室内）或 single hard source（夜戏）；"
            "彩色片：饱和 primary gel（红幕、金柱、青竹）；"
            "夜戏：蓝青 moonlight gel + 灯笼 warm practical；"
            "肤色：略 theatrical powder base，仍保留 film texture；"
            "禁忌：flat beauty dish 网红光、Wong Kar-wai 霓虹、natural overcast Nordic doc。"
        ),
        "palette_strategy": (
            "主调：朱红、明黄、金、 Jade 绿、靛青、侠黑；"
            "服色：高饱和 silk（红袍、白侠、金甲、五毒彩衣）；"
            "肤色：偏 warm powder，唇色清晰；"
            "叙事：正邪对照用红/黑/白，五毒/奇门用多色 identifier costume；"
            "血战场景可提 red density 但非 modern gore splatter。"
        ),
        "atmosphere": (
            "江湖义气、片厂武侠歌剧感、皇权与侠义、复仇与门派；"
            "竹林剑战、客栈掷杯、宫廷礼仪、擂台比武（视觉：silk flutter、incense smoke）；"
            "张彻「阳刚血勇」与胡金铨「诗意侠骨」可并存于同一 aesthetic 框架；"
            "保持 theatrical clarity，非 gritty doc realism。"
        ),
        "materials": (
            "服饰：丝绸长袍、铠甲、斗笠、束发冠、云肩、腰带佩剑；"
            "化妆：京剧影响眉眼线、脸谱化反派 optional；"
            "布景：朱漆柱、金箔屏、假山石、纸窗、红帘、客栈木桌酒坛；"
            "道具：长剑、双刀、禅杖、飞镖、酒葫芦、圣旨、折扇；"
            "环境：片厂宫廷、backlot 竹林、沙漠假景（饱和 sky backdrop）。"
        ),
        "quality": (
            "邵氏宽银幕电影级：costume embroidery 与 set paint 清晰；"
            "适合 9:16 竖版角色卡与 2.35:1 宽银幕场景；"
            "action pose sharp readable，live-action realistic studio cinema；"
            "4K 细节但 retain period saturation 与 hard light character。"
        ),
        "taboos": (
            "90 年代旺角霓虹、现代香港 street、手机/现代装；"
            "2000s 卧虎藏龙式 natural mist minimalism 主导；"
            "日系 anime、3D CG 游戏、赛博霓虹；"
            "过度 gore horror、Western medieval default、low sat Morandi doc；"
            "watermark、字幕条、多格漫画分镜（单图角色卡时）。"
        ),
        "characters_zh": (
            "【面部】剑眉、英气或妩媚古装脸，妆面略 theatrical；"
            "反派可脸谱化色块（五毒、宦官）；"
            "表情：侠义凛然、含怒、娇媚、醉态（大醉侠）。"
            "【发型】束发、高冠、发簪、侠女双环髻；"
            "张彻群侠：短发或束发统一英挺。"
            "【服饰】红/白/黑侠袍、宫廷华服、僧袍、五毒彩衣；"
            "持剑、双刀、禅杖、酒碗、折扇。"
            "【体态】马步、剑指、轻功 staging（清晰 suspension 非 blur）；"
            "群像：列阵、对垒、客栈围桌。"
            "【气质范例】方燕平——英侠；王润生——独臂刀客；"
            "五毒成员——色标化造型；乾隆/西施——宫廷华美。"
        ),
        "characters_en": (
            "Shaw Brothers studio cinema character, 1960s-1980s Hong Kong martial arts film, "
            "elaborate period costume and opera influenced makeup, hard studio lighting, "
            "saturated Eastmancolor red gold jade palette, jian sword martial arts pose, "
            "Shawscope widescreen staging, theatrical wuxia hero portrait, "
            "Clearwater Bay studio set aesthetic, bold primary colors, "
            "no neon 1990s HK, no naturalistic 2000s wuxia art film, highly detailed 4k"
        ),
        "scenes_zh": (
            "【典型环境】邵氏宫廷大殿、客栈大堂、片厂竹林、"
            "擂台、红帘寝宫、寺庙庭院、沙漠 backdrop 对决、江边酒楼。"
            "【构图】宽银幕群像 staging、柱廊纵深、"
            "竹林剑战 full body readable、客栈内对称桌席。"
            "【光影】影棚 hard key、红幕 gold accent、"
            "夜戏 blue gel moon + lantern warm。"
            "【质感】saturation 高、set paint 可见、"
            "incense smoke 与 silk motion 强调。"
        ),
        "scenes_en": (
            "Shaw Brothers studio palace hall red pillars golden screen, "
            "martial arts bamboo grove backlot hard sunlight, "
            "inn tavern interior widescreen staging, saturated Eastmancolor 1960s Hong Kong cinema, "
            "wuxia sword fight clear choreography tableau, Shawscope 2.35 anamorphic framing, "
            "theatrical period costume drama atmosphere, bold red gold jade palette, 4k"
        ),
        "colors": (
            "主色：朱红、明黄、金、 Jade 绿、靛青、侠黑、肤粉；"
            "点缀：五毒彩衣、白侠袍、血 red accent；"
            "叙事：宫廷提金红，夜戏加青蓝 gel"
        ),
        "image_prompt": (
            "Shaw Brothers studio cinema live-action, 1960s-1980s Hong Kong martial arts film aesthetic, "
            "saturated Eastmancolor red gold jade palette, hard studio lighting theatrical wuxia staging, "
            "elaborate period silk costume and opera influenced makeup, Shawscope widescreen palace hall red pillars, "
            "bamboo grove backlot sword fight clear pose, inn tavern martial arts tableau, "
            "Clearwater Bay studio set Shaw Brothers golden age, bold primary colors film grain, "
            "no 1990s neon HK, no naturalistic 2000s wuxia minimalism, no anime, highly detailed 4k vertical 9:16"
        ),
        "video_prompt": (
            "martial arts sword clash clear choreography Shaw Brothers staging, "
            "silk robe spin slow motion hard studio light, "
            "incense smoke palace hall dolly, saturated Eastmancolor grade consistent, "
            "wuxia hero tableau widescreen motion, no shaky neon street cam, theatrical HK golden age pacing"
        ),
        "references": [
            "Come Drink with Me / 大醉侠 (1966)",
            "One-Ararmed Swordsman / 独臂刀 (1967)",
            "The Five Deadly Venoms / 五毒 (1978)",
            "The Love Eterne / 梁山伯与祝英台 (1963)",
        ],
    },
}
