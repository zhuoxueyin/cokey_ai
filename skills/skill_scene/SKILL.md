---
skill_name: 场景设计·场景卡·空间氛围
skill_id: skill.scene
version: 1.1.0
author: cokey
update_time: 2026-06-21
tag: 短剧/漫剧/场景设计/场景卡/一键生图/六宫格多角度/光色构图
---

# 一、技能简介

**生产级场景设计 Skill**：在 **剧本场次 + 已设计角色 + 绑定风格** 基础上，通过 **知识检索与风格分析**，为每个关键场景产出结构化 **场景卡（SceneCard）** 与 **完整生图 prompt**。

核心链路：

1. **前置收集**：汇总剧本场次、出场角色、已锁定角色卡要点
2. **知识融合**：检索构图/配色/光影/场面调度/短剧空间节奏
3. **风格准备**：解读 `style_analysis`，融合 moodboard 参考（若有）
4. **场景清单**：从剧本提取需设计的场景列表
5. **场景设计**：逐场景输出环境、光色、道具、氛围
6. **确定场景出图**：场景 `locked` 后交付 **主图 prompt + 六宫格多角度 prompt + scene-image-tasks**（支持平台 **一键生图 / 一键六宫格生图**）

场景设定须与 **绑定风格** 及 **已设计角色** 一致；空间叙事服务于剧本情绪。

# 二、适用场景

- **scene** 阶段：按剧本场次批量或逐个设计场景
- 用户 **确认场景方向** 后：须产出完整 `scene-prompt` + `scene-grid-prompt` + `scene-image-tasks`
- 用户要求 **一键生图 / 六宫格**：走 `scene_master` + `scene_grid_6` 双任务
- 已绑定视觉风格：场景美学须与 `style_analysis.visual.*` 及 `scene_suffix_en` 一致

不适用：场景仍为 `draft` 时提前写六宫格 prompt；无剧本场次；与 `render_class` 冲突的混搭。

# 三、输入条件

| 输入 | 必填 | 说明 |
|------|------|------|
| 剧本 / 场次列表 | 是 | 平台注入 `episode_script`、分场对白或用户粘贴 |
| 角色卡 / 角色清单 | 是 | 已设计角色名称、造型要点、locked_tokens |
| 绑定风格 → `style_analysis` | 是 | 含 `visual.*`、`model_prompts.scene_suffix_en` |
| Tool 知识预检索 | 推荐 | `composition` / `color` / `lighting` / `blocking` / `short_drama` |
| 用户 @ 场景/氛围参考图 | 否 | Vision 分析，**仅**提取光色/材质/空间层次 |
| 用户确认场景 | 出图前必填 | 「确认」「定稿」「就这个场景」等 → `scene_card.status=locked` |

# 四、核心执行流程

**ReAct 执行协议**：可保留 `### ReAct 执行记录`（<=6 行）；每轮 **先交付结果**，再附精简过程。

## 4.0 前置收集（每轮必做，<=8 行）

| 步骤 | Act | 产出 |
|------|-----|------|
| 0 | Observe | 复述用户需求、当前场景名或「全剧本扫场」 |
| 1 | 收集剧本场次 | `script_scenes[]`：场号、地点、时间、摘要、情绪、出场角色 |
| 2 | 收集角色要点 | `character_refs[]`：name、造型/配色关键词 |
| 3 | 标注缺口 | 缺剧本/缺角色/缺风格 → `draft` 并列出待补项 |

## 4.1 知识检索与融合（每轮必做，<=8 行）

- 引用 `【Tool 预检索】` **≥1 条**可迁移规律
- 写清「如何与本场情绪碰撞」
- 不足时用经典影片空间模式补充，标「参考联想」

## 4.2 风格准备（所有场景共用）

| 步骤 | Act | 产出 |
|------|-----|------|
| 1 | 深度解读绑定风格 | render_class、color_palette、lighting、texture、scene_suffix_en |
| 2 | 分析参考图（条件） | `ref_scene_analysis`（Vision，仅空间/光色层） |
| 3 | 融合双源风格 | `fused_scene_style` |

## 4.3 场景清单 → `scene_inventory`

| 字段 | 说明 |
|------|------|
| `scene_id` | 稳定 slug |
| `name_zh` | 中文场景名 |
| `script_refs` | 关联场号 |
| `location_type` / `time_of_day` / `mood_zh` | 空间类型 / 时间 / 情绪 |
| `characters_present` | 出场角色 |
| `status` | `pending` \| `designing` \| `ready` |

## 4.4 单场景设计 → `scene_design` + `scene_card`

**活跃场景锁定**：用户未再次点名时，**必须**继续当前场景。

### `scene_design`（设计层，中文）

| 字段 | 说明 |
|------|------|
| `environment_zh` | 空间结构、尺度、材质、时代元素 |
| `layout_zh` | 前景/中景/远景、动线、场面调度 |
| `lighting_zh` | 主光/辅光/色温/明暗对比 |
| `color_zh` | 主色/辅色/点缀 |
| `props_zh` | 关键道具（≥2 若有） |
| `atmosphere_zh` | 雾/尘/雨/烟等 |
| `character_blocking_zh` | 人物与空间关系（可选 silhouette） |
| `status` | `draft` \| `ready` |

### `scene_card`

| 字段 | 说明 |
|------|------|
| `scene_id` / `name_zh` | 同清单 |
| `one_line_zh` | 一句话气质（≤30 字） |
| `visual_anchors_zh` | 3~5 个视觉识别点 |
| `locked_tokens` | 3~8 个英文空间/光色关键词 |
| `aspect_ratio` | 继承项目画幅 |
| `status` | `draft` \| `locked` |

## 4.5 意图路由 · 确定场景后才出完整 prompt（高优先级）

每轮先判断用户诉求：

| 用户意图 | 交付 |
|----------|------|
| 扫场 / 出清单 / 比选 | 仅 `scene_inventory` + 设计摘要，**不出** prompt |
| 深化某场景设计 | `scene_design` + `scene_card`（`draft`），**不出** prompt |
| **确认场景 / 定稿 / 一键生图 / 六宫格** | `scene_card.status=locked` + **完整双 prompt + scene-image-tasks** |
| 仅要主图 | 只交付 `scene-prompt` + `task_id=scene_master` |
| 仅要六宫格 | 只交付 `scene-grid-prompt` + `task_id=scene_grid_6` |
| 默认（场景 ready 未确认） | 设计摘要 + 询问是否确认出图 |

**硬规则**：`scene-prompt` / `scene-grid-prompt` / `scene-image-tasks` **仅在场景已确定（locked 或用户明确要求出图）时输出**。

## 4.6 确定场景 · 完整生图交付 → `scene_prompt_pack`

场景确认后，**必须**输出以下三块（顺序固定）：

1. **`scene-prompt`** — 单张 **场景主图**（建立镜头 / hero shot）
2. **`scene-grid-prompt`** — 单张 **六宫格**（同一场景 6 个不同机位/角度）
3. **`scene-image-tasks`** — 平台一键出图任务 JSON（含 `scene_master` + `scene_grid_6`）

### 4.6.1 `scene-prompt` · 场景主图

- **一张图 · 单一视角 · 完整环境**
- 英文为主；拼接顺序：`layout/scale` → `environment/materials` → `lighting` → `color_palette` → `atmosphere/props` → `style_tokens` + `scene_suffix_en`
- 须含画幅：`vertical 9:16` / `horizontal 16:9` 等与项目一致
- **禁止**：六宫格、多分格、turnaround sheet、人物肖像特写
- 可写 distant figures / silhouettes，**禁止**人物五官服装细节

### 4.6.2 `scene-grid-prompt` · 六宫格多角度

- **一张图 · 固定六宫格布局 · 同一场景 · 六个不同机位**
- 布局硬约束（`layout_en` 须全部出现）：
  - `6-panel grid layout`, `2 rows 3 columns`, `equal panel size`
  - `same environment`, `consistent lighting and color palette across all panels`
  - `environment exploration sheet`, `scene contact sheet`
  - `no text labels`, `no panel borders with captions`
- **六个 panel 机位（按序写入 prompt）**：

| Panel | 机位 | 英文关键词 |
|-------|------|------------|
| 1 | 建立全景 | establishing wide shot, full environment overview |
| 2 | 反打/对向 | reverse angle wide shot, opposite viewpoint |
| 3 | 低角度仰拍 | low angle shot, dramatic upward perspective |
| 4 | 高角度俯拍 | high angle shot, bird eye overview |
| 5 | 细节特写 | detail close-up, key prop or architectural feature |
| 6 | 纵深透视 | depth corridor shot, leading lines into background |

- 六格须共享：`locked_tokens`、同一时代/材质/光色逻辑；**禁止**六格变成六个不同地点
- **禁止**：人物大头照、表情特写、角色 turnaround

### 4.6.3 `scene-image-tasks` · 一键出图 JSON

平台读取规则（与 `character-image-tasks` 同构）：

- **正向 prompt**：读 `prompt_ref` 指向的 Markdown fenced 块（主力）
- **负向 prompt**：JSON 中 `negative_en`
- **画幅**：JSON 中 `aspect_ratio`；六宫格推荐 `16:9` 或 `3:2`

## 4.7 Finish

**场景已确定时**输出顺序：

1. 本轮可交付结果（一句话）
2. Markdown 场景卡（`scene_design` + `scene_card`，status=locked）
3. `scene-prompt` fenced 块
4. `scene-grid-prompt` fenced 块
5. `scene-image-tasks` JSON
6. `### 下一步可选` + 精简 ReAct

# 五、输出标准

## 5.1 回复顺序（结果优先）

**场景未确定**：清单 / 设计摘要 / 下一步确认，**无** prompt 块。

**场景已确定（须一键出图）**：

1. **本轮可交付结果**（如：「大婚夜内殿场景已锁定，已产出主图 + 六宫格 prompt」）
2. **本轮交付物清单**：scene_card / scene-prompt / scene-grid-prompt / scene-image-tasks
3. **Markdown 场景卡**（给人读）
4. **生图 Prompt 块**（两个 fenced · 主力，见 5.2）
5. **出图任务 JSON**（见 5.3）
6. `### ReAct 执行记录`（<=6 行）

**禁止**用嵌套 JSON 代替 Markdown 场景卡；**禁止**在 JSON 里写长篇正向 prompt。

## 5.2 生图 Prompt（Markdown · 主力）

每个 **已确定** 场景须输出 **两个** fenced 块。

**场景主图**：

````markdown
```scene-prompt
establishing cinematic environment shot, vertical 9:16 framing,
ancient Chinese wedding chamber interior, wooden beams and red silk drapes,
central altar with dragon phoenix candles, low-key dramatic lighting,
warm crimson accent on deep ebony wood, incense smoke haze,
shallow depth of field, empty room no portrait close-up,
incense smoke, candlelight, wooden interior, cinematic realistic texture,
[按 fused_scene_style 补充 render_class / scene_suffix_en token]
```
````

**六宫格多角度**：

````markdown
```scene-grid-prompt
6-panel grid layout, 2 rows 3 columns, equal panel size,
environment exploration sheet, same ancient Chinese wedding chamber,
consistent low-key crimson candlelight across all panels,
panel 1 establishing wide shot full chamber overview,
panel 2 reverse angle wide opposite doorway view,
panel 3 low angle dramatic upward perspective on altar,
panel 4 high angle bird eye overview of room layout,
panel 5 detail close-up dragon phoenix candle and red silk texture,
panel 6 depth corridor shot leading lines toward inner chamber,
no text labels, no caption borders, no character portrait close-up,
incense smoke, candlelight, wooden interior, cinematic realistic,
[按 fused_scene_style 补充 token]
```
````

要求：

- `scene-prompt` **不得**含 grid / multi-panel / contact sheet
- `scene-grid-prompt` **必须**含六宫格布局词 + 六个 panel 机位描述
- 两 prompt 的光色/材质/时代 **必须一致**
- 与 `fused_scene_style.render_class` 一致

## 5.3 出图任务参数（JSON · 传给平台 · 必填于 locked 场景）

紧随 Prompt 块之后，输出 **一个** `scene-image-tasks` fenced JSON 数组：

````markdown
```scene-image-tasks
[
  {
    "task_id": "scene_master",
    "scene_id": "palace_wedding_night",
    "scene_name": "大婚夜·内殿",
    "label": "大婚夜·内殿·场景主图",
    "aspect_ratio": "9:16",
    "prompt_ref": "scene-prompt",
    "negative_en": "6-panel grid, multiple panels, split screen, comic grid, collage, contact sheet, turn-around, people close-up portrait, face close-up, blurry, watermark, text, modern furniture, wrong era",
    "image_count": 1
  },
  {
    "task_id": "scene_grid_6",
    "scene_id": "palace_wedding_night",
    "scene_name": "大婚夜·内殿",
    "label": "大婚夜·内殿·六宫格多角度",
    "aspect_ratio": "16:9",
    "prompt_ref": "scene-grid-prompt",
    "negative_en": "single panel only, one view only, inconsistent lighting between panels, different locations, people portrait, face close-up, text labels, panel captions, blurry, watermark, wrong aspect ratio",
    "image_count": 1
  }
]
```
````

| 字段 | 必填 | 说明 |
|------|------|------|
| `task_id` | 是 | `scene_master`（一键生图）\| `scene_grid_6`（一键六宫格） |
| `scene_id` | 是 | 与场景卡 slug 一致 |
| `scene_name` | 是 | 中文场景名 |
| `label` | 否 | 按钮展示名；建议含「场景主图」「六宫格多角度」 |
| `aspect_ratio` | 是 | 主图跟项目；六宫格推荐 `16:9` 或 `3:2` |
| `prompt_ref` | 是 | `scene-prompt` 或 `scene-grid-prompt` |
| `negative_en` | 是 | 英文逗号分隔；主图禁 grid，六宫格禁 single panel |
| `image_count` | 否 | 默认 1 |

可选：`positive_en` 仅 API 兜底短句；**优先 Markdown 块正文**。

## 5.4 质量自检（locked 场景必过）

- [ ] 场景来自剧本，`scene_card.status=locked`
- [ ] 存在 `scene-prompt` + `scene-grid-prompt` **两个** Markdown 块
- [ ] 存在 `scene-image-tasks`，含 `scene_master` + `scene_grid_6`
- [ ] `prompt_ref` 与 fenced 块名一致
- [ ] 六宫格 prompt 含 `6-panel grid` + 六机位 + `same environment`
- [ ] 主图 prompt **不含** grid；六宫格 **不含** single view only
- [ ] 光色与 `fused_scene_style`、角色卡时代不冲突
- [ ] `### 下一步可选` 含：确认分镜 / 微调光色 / 下一场景

## 5.5 禁止

- 禁止场景 `draft` 时输出 scene-image-tasks
- 禁止六宫格六格变成六个不同地点
- 禁止把场景 prompt 写成人物定妆/肖像
- 禁止 JSON 代替 Markdown 场景卡

# 六、异常兜底

| 情况 | 处理 |
|------|------|
| 用户「确认 + 一键六宫格」但场景 draft | 先补全 scene_design，再 locked 后出双 prompt |
| 用户只要主图不要六宫格 | 仅 `scene_master`；询问是否需要六宫格 |
| 用户只要六宫格 | 仅 `scene_grid_6`；须仍有 scene-grid-prompt |
| 竖屏项目 9:16 | 主图 9:16；六宫格可用 16:9 横图承载 2×3 格 |
| 同地点光色 variants | 各 variant 独立 scene_id + 独立双 prompt 套 |

# 七、约束禁忌

1. **禁止**跳过前置收集直接写 prompt
2. **禁止**未确认场景就输出 scene-image-tasks
3. **禁止**忽视 `scene_suffix_en` 与绑定风格
4. **禁止**六宫格缺少布局硬约束词
5. **禁止**主图与六宫格光色/时代不一致

# 八、版本记录

| 版本 | 更新时间 | 更新内容 | 更新人 |
| ---- | -------- | -------- | ------ |
| 1.1.0 | 2026-06-21 | 确定场景产出完整双 prompt；scene_master + scene_grid_6 一键出图/六宫格 | cokey |
| 1.0.0 | 2026-06-21 | 首版：前置收集→知识融合→场景清单→场景卡 | cokey |
