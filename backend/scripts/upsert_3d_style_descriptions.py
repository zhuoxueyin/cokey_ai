"""将 7 个 3D 风格完整描述 upsert 到 drama_style_presets 并发布。"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import close_mongodb, init_mongodb
from app.services.drama_style_service import get_drama_style_service

STYLES = [
    {
        "style_id": "3d_cn_fantasy_animation",
        "name": "3D中国奇幻动画",
        "render_class": "render_3d",
        "genre_tags": ["国风", "奇幻", "3D动画", "神话", "东方美学", "电影级"],
        "style_description_md": """# 3D中国奇幻动画

## 风格摘要

以国产奇幻动画电影为参照的 3D 渲染美学：融合东方神话叙事、水墨意境与电影级光影，强调宏大世界观、灵韵氛围与史诗感镜头，适用于仙侠、神魔、志怪与东方史诗题材。

## 风格特点

- 角色造型偏东方骨相，五官精致、轮廓柔和，服饰层叠飘逸（宽袖、披帛、铠甲纹样）
- 场景兼具写实体积感与国画留白：云雾、瀑布、古建飞檐、浮空岛屿、灵兽与法阵
- 材质混合 PBR 与手绘笔触：皮肤 subsurface、丝绸高光、金属做旧、玉石半透明
- 光影戏剧化：体积光、丁达尔效应、冷暖对比、夜景灯笼与法术 glow
- 镜头语言电影化：大全景建立世界观、低角度仰拍显威仪、慢速推拉与环绕
- 粒子与特效：灵气流转、花瓣雨、符咒光纹、水墨扩散转场

## 人物角色

delicate East Asian facial features, expressive eyes with subtle eyeliner, flowing long hair with ornamental hairpins, layered hanfu or xianxia robes with embroidery and jade accessories, heroic or ethereal body language, martial arts poses, divine aura, mythical beast companions

## 场景描述

ancient Chinese palaces on cliff edges, misty bamboo forests, floating celestial mountains, dragon gates over stormy seas, lantern-lit night markets, sacred temples with incense smoke, epic battlefields with magic sigils, ink-wash sky gradients

## 色彩倾向

青绿山水, 黛蓝, 朱砂红, 金色点缀, 月白, 墨黑, 琥珀暖光

## 代表作品

哪吒之魔童降世 (2019)
白蛇：缘起 (2019)
深海 (2023)
长安三万里 (2023)
姜子牙 (2020)

## 生图提示词参考

3D Chinese fantasy animation film style, cinematic xianxia aesthetic, oriental mythological epic, volumetric god rays, ink-wash atmospheric haze, detailed PBR silk and jade materials, flowing hanfu costumes, floating mountains and ancient architecture, dramatic rim lighting, high detail character sculpt, Unreal Engine quality render, 8k, film still

## 生视频提示词参考

slow cinematic camera orbit around hero, mist drifting through temple courtyard, magical particles swirling, cloth and hair physics, epic establishing shot pull-back, ethereal atmosphere, smooth motion, Chinese fantasy animation look
""",
    },
    {
        "style_id": "3d_character_simple_cartoon",
        "name": "3D人物(简约卡通风)",
        "render_class": "render_3d",
        "genre_tags": ["3D", "简约", "卡通风", "人物", "可爱", "低多边形感"],
        "style_description_md": """# 3D人物(简约卡通风)

## 风格摘要

面向角色展示与轻量叙事的 3D 简约卡通风：形体概括、线条干净、表情可读性强，减少写实皮肤与复杂材质，突出可爱、亲和与商业插画感，适合 IP 形象、社交头像、轻喜剧与儿童向内容。

## 风格特点

- 头身比略 Q 化（约 1:4 至 1:5），五官大而圆，腮红与简笔眉形
- 建模面数感低、边缘圆润，少褶皱多色块分区
- 材质以 flat color + 轻微渐变为主，皮肤 matte，头发块状高光
- 光影简化：单一主光 + 柔和环境光，轮廓光勾勒形体
- 配色明快、饱和度中等偏高，背景常纯色或极简几何
- 姿态夸张、可读性强，适合表情包与短视频角色 loop

## 人物角色

cute simplified 3D cartoon character, large round eyes, small nose and mouth, soft blush cheeks, clean smooth skin shader, chunky hair tufts, minimal clothing folds, friendly smile, expressive hand gestures, stylized proportions, mascot-like appeal

## 场景描述

minimal studio backdrop, soft gradient background, simple geometric props, clean floor shadow, occasional flat-color environment blocks, product-shot style character presentation

## 色彩倾向

糖果粉, 天蓝, 奶黄, 薄荷绿, 珊瑚橙, 柔白

## 代表作品

Apple Memoji 系列视觉
Duolingo 3D 角色风格
各类品牌 3D IP 吉祥物广告

## 生图提示词参考

3D simple cartoon character, cute stylized proportions, clean minimal modeling, soft matte skin, flat color shading with gentle gradient, large expressive eyes, rounded shapes, studio lighting, solid pastel background, mobile game avatar quality, high readability, no photorealism

## 生视频提示词参考

character idle loop with subtle bounce, simple head turn and wave, minimal background, smooth cartoon motion, friendly expression change, lightweight 3D render
""",
    },
    {
        "style_id": "3d_glossy_latex",
        "name": "3D光泽乳胶渲染风格",
        "render_class": "render_3d",
        "genre_tags": ["3D", "乳胶", "光泽", "潮流", "充气感", "高反光"],
        "style_description_md": """# 3D光泽乳胶渲染风格

## 风格摘要

强调高光泽乳胶/塑胶质感的当代 3D 视觉：物体与角色表面如充气玩具或乳胶材质，强 specular 高光、饱和色块与圆润体积，带有潮流艺术、波普与装置感，适合时尚海报、概念艺术与强视觉冲击力镜头。

## 风格特点

- 材质核心：latex / vinyl / inflated plastic，高 reflectivity、清晰高光点
- 形体鼓胀、边缘圆滑，似充气或软胶模具
- 颜色高饱和、对比强烈，常单色块或渐变包裹整体
- 环境反射明显，可搭配镜面地面或霓虹背景
- 人物可选全乳胶连体造型或局部乳胶配饰，面部可写实或 stylized
- 布光：硬光主灯 + 多盏轮廓光，强调曲面反光条

## 人物角色

glossy latex suit character, inflated rounded body volumes, shiny vinyl skin, fashion pose, reflective curves, bold silhouette, optional mask or hood, high-end editorial attitude

## 场景描述

mirror floor studio, neon gradient backdrop, floating latex spheres and tubes, minimalist set with strong color blocking, product hero lighting, surreal inflated furniture

## 色彩倾向

电光紫, 荧光粉, 铬黄, 液态银, 深黑对比, 霓虹青

## 代表作品

各类 latex/inflatable 3D art direction（Behance 潮流视觉）
KAWS 充气雕塑美学延伸
时尚品牌 3D campaign 乳胶质感大片

## 生图提示词参考

3D glossy latex render style, inflated vinyl material, high specular highlights, smooth rubber surface, saturated bold colors, studio hard lighting with rim lights, mirror reflections, trendy pop art aesthetic, rounded inflated shapes, octane render look, ultra shiny, fashion editorial

## 生视频提示词参考

slow rotation of glossy latex object, light sliding across reflective surface, subtle inflation wobble, neon color shift, cinematic product reveal, smooth camera dolly
""",
    },
    {
        "style_id": "3d_enhanced_cartoon_render",
        "name": "3D加强版卡通渲染风格",
        "render_class": "render_3d",
        "genre_tags": ["3D", "卡通渲染", "NPR", "加强版", "游戏CG", "描边"],
        "style_description_md": """# 3D加强版卡通渲染风格

## 风格摘要

在标准 toon/cel-shade 基础上「加强」的 3D 卡通渲染：更明确的描边、分层明暗、饱和色彩与游戏 CG 级细节，兼顾动画可读性与次世代精度，适合动作冒险、格斗、MOBA 过场与高品质卡通剧集。

## 风格特点

- NPR + PBR 混合：硬边明暗阶（2–3 阶或渐变 cel），可控 rim light
- 描边：外轮廓 ink outline + 内部分线（结构线、阴影线）
- 材质细节加强：金属战甲、皮革、魔法能量仍保留卡通概括
- 表情与肌肉形变夸张，战斗 pose 张力强
- 场景层次丰富：远景 atmospheric perspective，近景 sharp contrast
- 特效层：冲击波、速度线、元素魔法与 cartoon bloom

## 人物角色

heroic stylized 3D character, strong silhouette, cel-shaded skin and armor, thick outline, exaggerated muscles or costume layers, dynamic action pose, glowing weapon, confident expression

## 场景描述

fantasy arena, ruined temple battleground, stylized forest with painted sky, game cinematic environment, dramatic clouds, foreground rocks with toon shading, midground architecture, volumetric light shafts

## 色彩倾向

皇家蓝, 战损金, 翠绿植被, 暮光紫, 高对比阴影色

## 代表作品

原神 过场动画风格
英雄联盟 3D 宣传 CG
双城之战 部分 3D 镜头气质（加强描边向）

## 生图提示词参考

enhanced 3D cartoon render, cel-shaded with PBR details, bold ink outlines, multi-step toon lighting, game cinematic quality, vibrant colors, rim light, stylized anatomy, detailed costume, dynamic composition, Unreal Engine stylized render, high contrast shadows

## 生视频提示词参考

action game cinematic camera, character dash with motion blur streaks, cel-shaded lighting flicker, magic spell burst, camera shake on impact, stylized VFX trails
""",
    },
    {
        "style_id": "3d_cartoon_animation",
        "name": "3D卡通动画风格",
        "render_class": "render_3d",
        "genre_tags": ["3D", "卡通动画", "皮克斯", "家庭向", "电影级"],
        "style_description_md": """# 3D卡通动画风格

## 风格摘要

主流 3D 卡通动画长片美学（皮克斯/梦工厂系）：角色魅力优先、表演驱动、材质真实但形体 stylized，光影物理可信、色彩温暖，强调情感叙事与家庭向视觉语言，适用于喜剧、冒险、成长题材。

## 风格特点

- 角色设计：appeal 优先，夸张但不失重量感，眼睛大而有神
- 皮肤 subsurface scattering，毛发 groom 精细，布料 simulation
- 环境写实度中等偏高，道具有生活细节与 humor 造型
- 三点布光 + 全局 illumination，柔和 contact shadow
- 色彩脚本随情绪变化：暖色安全、冷色危机、高饱和高潮
- 镜头遵循经典动画原则：anticipation、follow-through、clear staging

## 人物角色

appealing 3D animated character, Pixar-style proportions, expressive eyebrows, clear mouth shapes for dialogue, stylized hair groom, soft skin SSS, personality-driven pose, family-friendly design

## 场景描述

cozy suburban home, colorful town square, whimsical workshop, sunny meadow with stylized trees, interior with warm practical lights, storybook geography with readable layouts

## 色彩倾向

暖橙, 天空蓝, 草绿, 奶油白, 柔和紫（夜景）

## 代表作品

玩具总动员系列
疯狂动物城 (2016)
寻梦环游记 (2017)
超人总动员 2 (2018)

## 生图提示词参考

3D cartoon animation film style, Pixar-like appeal, soft subsurface skin, stylized proportions, warm cinematic lighting, detailed groom hair, rich environment storytelling, family animation aesthetic, physically based but stylized materials, depth of field, movie still quality

## 生视频提示词参考

character performance shot with emotional acting, subtle squash and stretch, camera over-shoulder dialogue, warm interior lighting, gentle camera push-in, animated film pacing
""",
    },
    {
        "style_id": "3d_diorama_miniature",
        "name": "3D卡通微缩景观",
        "render_class": "render_3d",
        "genre_tags": ["3D", "微缩", "景观", "移轴", "手办感", "卡通"],
        "style_description_md": """# 3D卡通微缩景观

## 风格摘要

将场景呈现为桌面级微缩模型或立体书景观：卡通化比例、移轴景深、手工质感与玩具沙盘感，适合展示城市街区、主题公园、故事切片与品牌世界观「一览全貌」镜头。

## 风格特点

- 比例压缩：建筑与人物如 HO/N 比例或 custom diorama scale
- 移轴摄影效果：浅景深、顶部俯角或等距视角，边缘虚化
- 材质偏 matte 塑料、纸模、黏土感，可见手工笔触或轻微 imperfections
- 灯光像摄影棚打光，整体小而精，细节集中在前景
- 植被、车辆、行人均为 simplified chunks
- 叙事以「一镜全景」呈现完整小故事

## 人物角色

tiny stylized cartoon figures, simplified silhouettes, mini people in diorama scale, cute blocky pedestrians, optional blurred background characters

## 场景描述

miniature city block diorama, tilt-shift perspective, tiny parks and rivers, model train scale buildings, snow globe atmosphere, tabletop landscape with roads and bridges, isometric cute town

## 色彩倾向

模型绿, 砖红, 浅灰路面, 天蓝背景, 奶白建筑

## 代表作品

移轴摄影城市短片
Google Miniature 概念视觉
各类品牌「微观世界」3D 广告

## 生图提示词参考

3D cartoon miniature diorama, tilt-shift photography effect, shallow depth of field, tiny stylized buildings and figures, tabletop scale model look, soft studio lighting, isometric or high-angle view, matte plastic and clay textures, whimsical toy landscape, macro lens aesthetic

## 生视频提示词参考

slow pan across miniature cityscape, tilt-shift blur at edges, tiny cars moving on loop, gentle parallax, stop-motion feel in 3D, cozy diorama reveal
""",
    },
    {
        "style_id": "3d_cartoon_render",
        "name": "3D卡通渲染风格",
        "render_class": "render_3d",
        "genre_tags": ["3D", "卡通渲染", "Toon", "NPR", "通用"],
        "style_description_md": """# 3D卡通渲染风格

## 风格摘要

通用 3D 卡通渲染（Toon/NPR）基线风格：清晰轮廓、分层明暗、非写实材质，在保持 3D 体积与透视的同时呈现 2D 动画可读性，适配广泛的角色、场景与商业插画需求，是多数 stylized 3D 项目的默认起点。

## 风格特点

- Cel-shading 或 gradient toon：明暗分界清晰，可选 2–4 色阶
- 外轮廓线（可粗细变化），内部结构线可选
- 材质简化：皮肤、布料、金属均以色块 + 高光形为主
- 透视与构图遵循 3D 空间，但纹理细节克制
- 光照方向明确，阴影形状干净，适合 frame-by-frame 感
- 色彩饱和、对比适中，背景可简化以突出主体

## 人物角色

stylized 3D toon character, clean cel shading, outline stroke, simple costume design, readable facial features, neutral hero pose, NPR skin shader

## 场景描述

stylized outdoor park, simple trees with flat color layers, toon clouds, clean ground plane shadow, minimal background clutter, poster-friendly composition

## 色彩倾向

明黄, 草绿, 天蓝, 中性灰阴影, 白色高光

## 代表作品

《塞尔达传说：旷野之息》风格化 3D
各类 toon shader 商业插画
独立游戏 stylized 3D 美术

## 生图提示词参考

3D cartoon render, toon shading, cel-shaded lighting, clean black outlines, stylized NPR materials, simple color blocks, clear shadow shapes, game art style, vibrant but controlled palette, full body character on simple background

## 生视频提示词参考

gentle turntable of toon-shaded character, consistent outline thickness, simple lighting rotation, stylized idle animation, clean NPR look
""",
    },
]


async def upsert_styles() -> None:
    await init_mongodb()
    svc = get_drama_style_service()
    results = []

    for item in STYLES:
        style_id = item["style_id"]
        payload = {
            "name": item["name"],
            "render_class": item["render_class"],
            "genre_tags": item["genre_tags"],
            "style_description_md": item["style_description_md"],
        }
        existing = await svc.get_by_style_id(style_id)
        if existing:
            await svc.update(style_id, payload)
            action = "updated"
        else:
            await svc.create({**payload, "style_id": style_id, "publish": False})
            action = "created"
        published = await svc.publish(style_id)
        results.append(
            {
                "style_id": style_id,
                "name": item["name"],
                "action": action,
                "status": published.get("status") if published else "failed",
            }
        )

    await close_mongodb()
    return results


def main() -> None:
    results = asyncio.run(upsert_styles())
    print("Upsert complete:")
    for r in results:
        print(f"  [{r['action']}] {r['style_id']} · {r['name']} → {r['status']}")


if __name__ == "__main__":
    main()
