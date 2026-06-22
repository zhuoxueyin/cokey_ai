---
skill_name: 角色设计·定妆图·角色卡
skill_id: skill.character
version: 4.4.0
author: cokey
update_time: 2026-06-21
tag: 短剧/漫剧/角色设计/定妆图/16:9角色卡/Markdown出图prompt/JSON任务参数
---

# 一、技能简介

**生产级角色生产 Skill**：按固定 **三步流水线** 为剧本角色产出结构化设定与生图 prompt：

1. **角色设计**（宏观）：背景、身份、性格、性别、年龄、关系、目标等，不涉及定妆视觉细节
2. **角色定妆图设计**（单视角基础）：画风、形象、服饰、头像气质、配色、线条等人物视觉基底，**不要多视角**
3. **角色卡片**（细节设定卡）：多角度、多表情、多动作、服饰细节、关键道具、武器等，输出 **16:9 设定卡** prompt

风格层遵循 **绑定风格 + 参考图（若有）** 双源融合；人物身份与宏观设定 **只来自用户文字**。

# 二、适用场景

- character 阶段：逐个/批量走完三步流水线
- 用户 @ 参考图：画风对齐参考图，人物身份仍按剧本/用户描述
- 已绑定视觉风格：定妆与角色卡美学须与风格 preset 一致

不适用：跳过宏观设计直接出角色卡；与 `render_class` 冲突的混搭。

# 三、输入条件

| 输入 | 必填 | 说明 |
|------|------|------|
| 绑定风格 → `style_analysis` | 是 | 平台 `resolve_style_context` 注入 |
| 用户角色描述 / 剧本片段 | 是 | 人物设定唯一权威来源 |
| 用户 @ 参考图 | 否 | 有则 vision 分析，**仅**提取风格/线条/配色/光影 |
| 项目上下文 | 否 | 题材、平台、时代 |

# 四、核心执行流程

**ReAct 执行协议**：可保留 `### ReAct 执行记录`，但只允许精简摘要（<=6 行）；每轮必须先给结果与交付，再给过程。

## 4.0 风格准备（所有角色共用）

| 步骤 | Act | 产出 |
|------|-----|------|
| 0 | Observe | 复述需求、style_analysis 要点、是否有参考图 |
| 1 | 深度解读绑定风格 | 确认 render_class、trait、suffix、palette、正负向词 |
| 2 | 分析参考图（条件） | `ref_style_analysis`（Vision，仅风格层） |
| 3 | 融合双源风格 | `fused_style` |

无参考图时 Step 2 标记 `skipped=true`，`fused_style` 等同 `style_analysis`。

## 4.0.5 用户意图识别与阶段路由（先判再做）

每轮先判断用户当前诉求，默认**单轮只交付一个阶段**，避免一把梭导致回复冗长混杂：

- 用户在“补人物设定/确认人设”：交付 Step 4.1（角色设计）
- 用户在“出定妆图/形象图”：仅在 4.1 `ready` 后交付 Step 4.2
- 用户在“出角色卡八维/16:9 设定卡”：仅在 4.1 与 4.2 `ready` 后交付 Step 4.3
- 只有用户明确要求“全流程一次出完”时，才交付 4.1→4.2→4.3 全套

**活跃角色锁定（高优先级）**：

1. 平台会在 Prompt 注入 `【当前活跃角色 · 必须遵守】`（含角色名、子步骤、来源）
2. 用户**未再次点名**时，**必须**继续该活跃角色；**禁止**跳回对话中更早角色或默认第一个已设计角色
3. 活跃角色解析顺序：用户显式点名 → 线程上下文 → 上轮助手「下一步可选」 → 近期用户消息
4. 开头须明确写出活跃角色全名；`### 下一步可选` 选项须全部围绕同一角色
5. 若同时无法确定角色名，须追问用户，**不得**擅自选白小檀等历史角色

## 4.0.6 角色设计队列（按顺序协作 · KV 持久化）

平台会在 Prompt 注入 `【角色设计队列 · 按顺序协作】`（含：角色名单、设/定/卡 进度、当前活跃位）。

1. **顺序意识**：须按队列 **1→2→3…** 逐位完成三步流水线；当前位「设/定/卡」未齐时，默认不跳下一位（除非用户点名下一位）。
2. **记忆继承**：**禁止**以「压缩上下文缺少某某设定」为由换角或重开第一位角色；须从队列进度 + 对话摘要 + 本轮之前同角色交付中 **继承已确认字段**，缺口标 `draft` 并列出待补项。
3. **阶段切换**：用户说「进入主链路下一环 / 进入下一阶段 / 进入场景阶段」等 → **立即**按 **scene**（或 pipeline 下一环）Skill 协作，**不得**继续产出角色卡/定妆。
4. 完成当前角色 **角色卡** 后，「下一步可选」须包含 **进入下一位角色**（若队列仍有未完成）与 **进入主链路下一环**（若用户拟进入场景）。

未交付阶段写 `pending` 与下一步输入需求，不展开长篇过程描述。

## 4.1 第一步 · 生成角色设计 → `character_design`

**目标**：宏观人物设定，**不写**定妆 prompt、不写多视角。

| 字段 | 说明 |
|------|------|
| `name` | 角色名 |
| `role` | 主角 / 配角 / 反派 |
| `gender_zh` | 性别 |
| `age_range_zh` | 年龄段 |
| `identity_zh` | 身份 / 职业 / 社会角色 |
| `background_zh` | 出身、时代、环境背景 |
| `personality_zh` | 性格、气质、说话方式 |
| `story_function_zh` | 在剧中的功能（推动冲突 / 情感锚点等） |
| `relationships_zh` | 与主要人物关系 |
| `goals_zh` | 目标与动机 |
| `conflicts_zh` | 核心矛盾 / 弧光方向 |
| `status` | `draft` \| `ready` |

**原则**：信息只来自用户文字；不足则 `draft` 并列出待补项，**不得**进入 Step 4.2。

## 4.2 第二步 · 生成角色定妆图设计 → `look_design` + `look_prompt_pack`

**目标**：在 `character_design` + `fused_style` 基础上，确定 **单视角** 视觉基底（定妆图），**不要** turnaround / 表情集 / 多动作分格；提示词需突出“角色本体”，弱化环境叙事。

| `look_design` 字段 | 说明 |
|--------------------|------|
| `render_notes_zh` | 画风一句话（对齐 fused_style.render_class） |
| `appearance_zh` | 体型、五官、发型、肤色 |
| `costume_zh` | 主服装层次、材质、配色 |
| `avatar_notes_zh` | 头像/面部特写气质（非多表情表） |
| `color_palette_zh` | 角色侧主色与辅色 |
| `line_art_zh` | 线条/勾线/笔触特征 |
| `accessories_zh` | 代表性配件（宏观层，非武器细节表） |
| `status` | `draft` \| `ready` |

**`look_prompt_pack` 硬约束**：

- `image_count`: **1**
- `aspect_ratio`: `3:4` 或 `1:1`（单张定妆 portrait / 3/4 身）
- `layout_en` 须含：`single unified illustration`, `one view only`, `no turn-around`, `no character sheet`, `no multiple panels`, `head and shoulders or three-quarter body`, `plain solid color background`, `clean studio backdrop`, `no environmental storytelling`
- **禁止**：多角度、表情集、动作分格、九宫格

**`positive_en` 拼接顺序**：layout → subject（性别/年龄）→ appearance → costume → color_palette → line_art → background_clean → style_tokens（fused_style）→ character_suffix

## 4.3 第三步 · 生成角色卡片 → `character_card` + `card_prompt_pack`

**目标**：在定妆图基底上扩展 **设定卡级细节**，输出 16:9 角色卡 prompt；背景信息仅作辅助，不抢角色主体。

**八维 `card_dimensions`**（中文，无信息写「无」+依据）：

| 键 | 含义 |
|----|------|
| `background_zh` | 出身/时代/环境气质（可与 design 呼应） |
| `appearance_zh` | 体型/五官/发型/肤色 |
| `expression_zh` | **多种**代表表情（≥2，逗号分隔） |
| `action_zh` | **多种**代表动作/姿态（≥2） |
| `costume_zh` | 服饰层次/材质/配色 **细节** |
| `style_zh` | 与 fused_style 一致的角色侧写 |
| `accessories_zh` | 配件细节 |
| `tools_weapons_zh` | 关键道具 / 武器 |

另：`card_copy_zh`（≤40 字，图内文字层）。

**`card_prompt_pack` 硬约束**：

- `image_count`: **1**
- `aspect_ratio`: **16:9**
- `layout_en` 须含：`character reference sheet`, `character profile card`, `16:9`, `multiple angles`, `multiple facial expressions`, `multiple action poses`, `outfit details`, `key props and weapons`, `single character only`
- **禁止**：与定妆图冲突的 render_class；非 16:9 主卡

**`positive_en` 拼接顺序**：layout → subject → appearance → expressions → actions → costume → accessories → tools_weapons → background → style_tokens → character_suffix

**`locked_tokens`**：3~8 个，来自 appearance/costume/accessories 英文关键词。

## 4.4 Finish

输出 Markdown 设定 + 生图 Prompt 块 + 出图任务 JSON + 自检清单。

**Think 原则**：宏观设计 → 定妆单视角 → 角色卡多细节；风格冲突时 render_class 以绑定风格为准。

# 五、输出标准

## 5.1 回复顺序（结果优先）

1. **本轮可交付结果**（一句话说明完成了哪个阶段）
2. **本轮交付物清单**（如：角色设计表 / look-prompt / character-image-tasks）
3. **Markdown 设定摘要**（宏观设计表、定妆要点、八维角色卡 — 给人读）
4. **生图 Prompt 块**（Markdown fenced · **主力 prompt**，见 5.2）
5. **出图任务 JSON**（fenced · 尺寸/负向/引用，见 5.3）
6. `### ReAct 执行记录`（精简版，<=6 行）

**禁止**用一大段嵌套 JSON 代替 Markdown 设定；**禁止**在 JSON 任务里写长篇正向 prompt（正向主力在 Markdown 块）。

## 5.2 生图 Prompt（Markdown · 主力）

每个需出图的角色须输出 **两个** fenced 块。正文为专业生图描述（英文为主，可夹必要中文注释），这是提交出图模型的 **主力 prompt**。

**定妆图**（单视角）：

````markdown
```look-prompt
single unified illustration, one view only, head and shoulders or three-quarter body,
young woman, silver twin tails, gentle smile, school uniform with blue ribbon,
plain solid color background, clean studio backdrop, no environmental storytelling,
cel shading, clean lineart, [按 fused_style 补充风格 token]
```
````

**角色卡**（16:9 设定卡）：

````markdown
```card-prompt
character reference sheet, 16:9 widescreen, multiple angles turn-around,
multiple facial expressions, multiple action poses, outfit and accessory details,
key props and weapons, young woman, silver twin tails, school uniform,
minimal neutral background blocks, character-focused composition,
cel shading, soft lighting, [按 fused_style 补充风格 token]
```
````

要求：

- 定妆 `look-prompt` **不得**含 turnaround / expression sheet / 多分格
- 定妆 `look-prompt` 必须强调 `plain solid color background` / `clean studio backdrop`，避免环境叙事
- 角色卡 `card-prompt` **须**含多角度、多表情、多动作、道具/武器细节
- 与 `fused_style.render_class` 一致；人物 identity 只来自用户文字

## 5.3 出图任务参数（JSON · 传给平台）

紧随 Prompt 块之后，输出 **一个** `character-image-tasks` fenced JSON 数组。平台一键出图时：

- **正向 prompt**：读取 5.2 中 `prompt_ref` 指向的 Markdown 块（主力）
- **负向 prompt**：JSON 中的 `negative_en`（标准化，来自 fused_style + 阶段约束）
- **尺寸**：JSON 中的 `aspect_ratio` / 可选 `width`×`height`

````markdown
```character-image-tasks
[
  {
    "task_id": "look",
    "character_name": "小雪",
    "label": "小雪·定妆图",
    "aspect_ratio": "3:4",
    "prompt_ref": "look-prompt",
    "negative_en": "turn-around, multiple views, character sheet, expression sheet, multiple panels, deformed face, blurry, watermark",
    "image_count": 1
  },
  {
    "task_id": "card",
    "character_name": "小雪",
    "label": "小雪·角色卡",
    "aspect_ratio": "16:9",
    "prompt_ref": "card-prompt",
    "negative_en": "single portrait only, one view only, wrong aspect ratio, not 16:9, multiple people, deformed face, extra limbs, blurry, watermark",
    "image_count": 1
  }
]
```
````

| 字段 | 必填 | 说明 |
|------|------|------|
| `task_id` | 是 | `look` \| `card` |
| `character_name` | 是 | 角色名 |
| `label` | 否 | 任务展示名 |
| `aspect_ratio` | 是 | `3:4` / `1:1` / `16:9` |
| `prompt_ref` | 是 | `look-prompt` 或 `card-prompt` |
| `negative_en` | 是 | 标准化负向词（英文逗号分隔） |
| `image_count` | 否 | 默认 1 |
| `width` / `height` | 否 | 可选像素尺寸，缺省由 aspect_ratio 推导 |

可选：`positive_en` 仅作 API 兜底短句；**优先使用 Markdown 块正文**。

## 5.4 设定摘要（Markdown 表格 · 非出图 JSON）

ReAct 之后、Prompt 块之前，用 Markdown 表格输出（示例）：

- **角色设计**：性别、身份、性格、背景、关系、目标…
- **定妆设计**：形象、服饰、配色、线条…
- **角色卡八维**：`card_dimensions` 各字段（expression/action 各 ≥2 项）

此部分不写 fenced JSON；便于人读与后续存库。

## 5.5 质量自检

- [ ] 风格准备 0~3 完成；有参考图则 Step 2 非 skip
- [ ] 先完成“意图识别与阶段路由”，本轮只交付目标阶段（除非用户要求全流程）
- [ ] **先**宏观设计 **再**定妆 **再**角色卡（ReAct 与表格顺序一致）
- [ ] 存在 `look-prompt` + `card-prompt` 两个 Markdown 块
- [ ] 存在 `character-image-tasks` JSON，且 `prompt_ref` 与块名一致
- [ ] look 任务 aspect_ratio 为 3:4 或 1:1；card 为 16:9
- [ ] look prompt 已限制纯色/干净背景，未喧宾夺主写环境大场景
- [ ] negative_en 已标准化；未假装已出图
- [ ] ReAct 记录为精简版（<=6 行），未盖过结果与交付物

# 六、异常兜底

| 情况 | 处理 |
|------|------|
| 无绑定风格 | render_class 默认 live_action；声明假设 |
| 无参考图 | ref_style_analysis.skip；fused_style = style_analysis |
| 宏观信息不足 | character_design.status=draft，禁止出 look/card prompt |
| 定妆未完成 | look_design.status=draft，card 仅输出草案并标注缺口 |
| 参考图无法识别 | 仅用 style_analysis，注明失败 |
| 用户只要某一步 | 仍输出完整 JSON 结构，未完成步 status=draft |

# 七、约束禁忌

1. 本 SKILL 为唯一规范源
2. 禁止跳步（未 character_design 直接写 card prompt）
3. 禁止用参考图覆盖用户文字中的性别/身份/性格
4. 定妆图禁止多视角 / 表情集 / 分格；角色卡禁止单视角 portrait 冒充设定卡
5. 禁止与 render_class 冲突的主体描述

# 八、版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 4.3.0 | 2026-06-21 | 活跃角色锁定：未点名时继续上轮焦点，禁止跳回已完成角色 |
| 4.2.0 | 2026-06-21 | 结果优先交付、意图识别分阶段路由、定妆提示词强化纯色/干净背景与角色主体 |
| 4.1.0 | 2026-06-18 | 出图：Markdown 主力 prompt（look/card-prompt）+ JSON 任务参数（character-image-tasks） |
| 4.0.0 | 2026-06-18 | 三步流水线：角色设计 → 定妆图（单视角）→ 角色卡（16:9 多细节） |
| 3.0.1 | 2026-06-18 | 对齐八段式章节标题 |
| 3.0.0 | 2026-06-21 | ReAct + 双源 fused_style |
| 2.0.0 | 2026-06-20 | 八维角色卡 + 16:9 单图 |
