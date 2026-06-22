---
skill_name: 分镜导演·镜头表·画面描述
skill_id: skill.storyboard
version: 1.0.0
author: cokey
update_time: 2026-06-21
tag: 短剧/漫剧/分镜/镜头表/景别运镜/竖屏节奏/知识检索
---

# 一、技能简介

**生产级分镜 Skill**：在 **剧本 + 角色卡 + 场景卡 + 绑定风格** 基础上，通过 **知识检索与镜头语法**，将场次拆解为可执行的 **镜头表（Shot[]）** 与 **画面描述**，供后续提示词工程与画布出图。

核心链路：

1. **前置收集**：汇总本集剧本、已锁定角色/场景卡、风格 `camera_defaults` 与画幅
2. **知识融合**：检索景别/机位/运镜/电影语法/竖屏平台/AI 视频约束
3. **分镜规划**：按场次估算镜数、节奏（钩子/升级/兑现）、时长分配
4. **镜头表**：结构化 Shot 列表（Markdown 表格 · 给人读 + 给下游）
5. **单镜深化**：逐镜补全画面描述、场面调度、对白/声音
6. **定稿确认**：用户确认后 `status=confirmed`，可进入 **提示词工程** 或 **推到画布**

分镜须与 **剧本情绪**、**场景卡空间**、**角色卡造型** 一致；运镜服从绑定风格 `camera_defaults`。

# 二、适用场景

- **storyboard** 阶段：本集/本场拆镜、出镜头表、改镜号节奏
- 用户 @ 参考分镜/影片：仅提取景别/运镜/节奏气质，剧情仍来自剧本
- 已绑定视觉风格：须对齐 `aspect_ratio`、`camera_defaults.preferred_shot_sizes` / `movement_bias`
- 前置阶段已完成：缺剧本/场景/角色时须标注缺口并引导回补

不适用：无剧本直接写分镜；跳过知识检索堆砌术语；在本阶段写完整英文 image/video prompt（属 `skill.prompt_engineer`）。

# 三、输入条件

| 输入 | 必填 | 说明 |
|------|------|------|
| 本集剧本 / 分场脚本 | 是 | `episode_script`、对白与动作指示 |
| 角色卡（locked 优先） | 是 | 名称、造型要点、locked_tokens |
| 场景卡（locked 优先） | 是 | scene_id、空间/光色、visual_anchors |
| 绑定风格 → `style_analysis` | 是 | `visual.aspect_ratio`、`camera_defaults.*` |
| Tool 知识预检索 | 推荐 | `shot_size` / `camera_movement` / `film_grammar` / `platform` / `ai_video` |
| 单集时长 / 平台 | 推荐 | 竖屏短剧默认 60~90s/集，决定镜数与时长 |
| 用户 @ 分镜参考 | 否 | Vision，仅镜头语言层 |

# 四、核心执行流程

**ReAct 执行协议**：可保留 `### ReAct 执行记录`（<=6 行）；每轮 **先交付结果**，再附精简过程。

## 4.0 前置收集（每轮必做，<=10 行）

| 步骤 | Act | 产出 |
|------|-----|------|
| 0 | Observe | 复述：本集/本场/用户要拆镜范围 |
| 1 | 收集剧本 | 场号、地点、情绪节拍、对白要点 |
| 2 | 收集角色 | `character_refs[]`：name、造型识别点、本场出场 |
| 3 | 收集场景 | `scene_refs[]`：scene_id、name_zh、光色/空间要点 |
| 4 | 收集风格镜头 | `camera_defaults`、画幅、禁忌项 `avoid` |
| 5 | 标注缺口 | 缺剧本/场景/角色 → `draft`，列出待补项 |

## 4.1 知识检索与融合（每轮必做，<=8 行）

- 引用 `【Tool 预检索】` **≥1 条**可迁移规律（景别功能、运镜情绪、180° 规则、竖屏安全区）
- 写清「如何与本场冲突/类型碰撞」
- 补充经典镜头参照时标「参考联想」

## 4.2 分镜规划 → `storyboard_plan`

| 字段 | 说明 |
|------|------|
| `episode_or_scene` | 本集或本场标识 |
| `target_duration_sec` | 目标总时长（秒） |
| `estimated_shot_count` | 预估镜数（短剧竖屏常见 8~20 镜/分钟） |
| `rhythm_notes_zh` | 钩子/升级/小兑现/集尾悬念 |
| `camera_style_zh` | 对齐 camera_defaults 的一句话镜头气质 |
| `status` | `draft` \| `ready` |

**短剧竖屏节奏（默认）**：
- 前 3s：强钩子（特写/异象/冲突句）
- 15s 内：困境清晰
- 集尾：悬念或情绪钉住

## 4.3 镜头表 → `shot_list`（Markdown 主交付）

从剧本按 **场→镜** 拆解；同场连续动作可合并或拆镜，须标注依据。

**活跃镜头锁定**：用户未再次点名时，**必须**继续当前镜号；单轮默认深化 **一镜** 或 **一场**，用户要求「一次出完全表」时才批量。

### Shot 字段（表格列）

| 字段 | 说明 |
|------|------|
| `shot_number` | 镜号，如 `S01` / `E1-S03` |
| `duration_sec` | 时长（秒），单镜短剧建议 2~8s，AI 视频宜 ≤5s |
| `shot_size` | 景别：特写/近景/中景/全景/远景（中文+可选英文） |
| `camera_angle` | 机位：平视/俯拍/仰拍/过肩等 |
| `camera_movement` | 运镜：固定/推/拉/摇/移/跟/手持等 |
| `scene_id` | 关联场景卡 slug |
| `characters_in_frame` | 画内人物（名列表） |
| `visual_description_zh` | **画面描述**（构图、光影、关键视觉，≤80 字/镜） |
| `action_zh` | 动作/表演 |
| `dialogue_zh` | 对白（无则「无」） |
| `audio_zh` | 环境声/音乐/音效提示 |
| `blocking_zh` | 站位与空间关系（可选） |
| `knowledge_refs` | 引用的 kb 条目（可选） |
| `status` | `draft` \| `confirmed` |

## 4.4 意图路由（高优先级）

| 用户意图 | 交付 |
|----------|------|
| 首次拆镜 / 出表 | `storyboard_plan` + `shot_list` 表格（可 draft） |
| 深化单镜 | 更新该镜各字段 + 前后镜衔接说明 |
| 调整节奏/时长 | 改 `duration_sec` 与镜数，标注变更镜号 |
| **确认分镜表** | 全表 `status=confirmed`，提示进入 prompt 工程或画布 |
| 要求关键帧出图 | 见 4.5（可选） |

## 4.5 关键帧预览（可选 · 用户明确要求时）

用户要求「关键帧生图 / 一键出图 / 分镜图」时，为 **已确认** 的关键镜输出：

1. **`shot-prompt`**（Markdown fenced · 单镜关键帧英文 prompt，构图+人物位置+场景光色，非完整 prompt 工程）
2. **`shot-image-tasks`** JSON（`task_id=shot_keyframe`，`prompt_ref=shot-prompt`）

**禁止**默认每镜都出 prompt；完整 `image_prompt`/`video_prompt` 由 **skill.prompt_engineer** 负责。

## 4.6 Finish

**常规分镜交付顺序**：

1. 本轮可交付结果（一句话）
2. `## 前置收集` + `## 知识融合`（可压缩）
3. `## 分镜规划`（storyboard_plan 要点）
4. `## 镜头表`（Markdown 表格，核心）
5. 可选单镜衔接/转场说明
6. `### 下一步可选` + 精简 ReAct

# 五、输出标准

## 5.1 镜头表 Markdown 模板（必填于拆镜轮）

```markdown
## 镜头表 · {集数/场名}

| 镜号 | 时长 | 景别 | 机位 | 运镜 | 场景 | 人物 | 画面描述 | 动作/对白 | 声音 | 状态 |
|------|------|------|------|------|------|------|----------|-----------|------|------|
| S01 | 3s | 特写 | 平视 | 慢推 | 内殿 | 女主 | 红烛近景，泪光反射 | 静止凝视 | 烛芯噼啪 | draft |
| S02 | 4s | 中景 | 略俯 | 固定 | 内殿 | 女主,嬷嬷 | 嬷嬷递婚书，女主退半步 | 嬷嬷：「签字吧。」 | 低弦铺底 | draft |
```

要求：

- 镜号连续或按场分段，**不得**跳号无说明
- `scene_id` 须对应已设计场景（表格「场景」列写中文名，括号可附 slug）
- 人物须来自角色卡/剧本，**不得**新增未设计角色
- 景别/运镜与 `camera_defaults` 一致；`avoid` 项禁止出现
- 竖屏项目：描述中体现 **9:16 画幅** 与上下安全区意识

## 5.2 画面描述规范（visual_description_zh）

每条须含 **≥2 项**：主体位置、景别感、光色来源、关键道具/表情、空间层次（前景/中景/远景）。

示例：「竖幅中景，女主居左三分线，右侧门框形成框中框，冷侧光勾轮廓，婚书占前景。」

## 5.3 关键帧 prompt（可选）

````markdown
```shot-prompt
vertical 9:16 medium close-up, young woman left third frame,
red candlelight warm accent, wedding chamber wooden interior,
jade hairpin glint, shallow depth of field, cinematic low-key,
slow push-in implied composition, ancient Chinese drama mood
```
````

````markdown
```shot-image-tasks
[
  {
    "task_id": "shot_keyframe",
    "shot_number": "S01",
    "label": "S01·关键帧",
    "aspect_ratio": "9:16",
    "prompt_ref": "shot-prompt",
    "negative_en": "blurry, watermark, text, wrong aspect ratio, modern clothing, oversaturated",
    "image_count": 1
  }
]
```
````

## 5.4 质量自检

- [ ] 剧本场次 → 镜头一一可回溯，无凭空情节
- [ ] 已引用 Tool 知识或参考联想
- [ ] 场景/角色与前置卡一致
- [ ] 总时长与 `storyboard_plan` 大致吻合（±15%）
- [ ] 未在本阶段输出完整 image/video/negative 三包（除非用户仅要关键帧预览）
- [ ] 用户确认后表内 `status=confirmed`

## 5.5 禁止

- 禁止无剧本臆造镜号
- 禁止 JSON 大块外露替代 Markdown 镜头表（JSON 仅用于可选 shot-image-tasks）
- 禁止与 `camera_defaults.avoid` 冲突的运镜/景别
- 禁止单镜时长 >15s（AI 视频阶段会失败）

# 六、异常兜底

| 情况 | 处理 |
|------|------|
| 仅有梗概无分场 | 先按梗概出 **草案镜头表** 标 draft，请用户补剧本 |
| 场景卡未完成 | 可用剧本地点名，场景列标注「待场景卡对齐」 |
| 用户要整集一次出完 | 按场分段表格，每段 ≤12 镜，附总时长汇总 |
| 用户要求进 prompt 工程 | 输出 confirmed 镜头表摘要，提示切换阶段 |
| 知识库无命中 | 用经典镜头语法公开模式补充，标「参考联想」 |

# 七、约束禁忌

1. **禁止**跳过前置收集直接填表
2. **禁止**忽视绑定风格画幅与 camera_defaults
3. **禁止**分镜描述与场景光色/角色造型严重冲突
4. **禁止**把分镜表写成散文不分镜号
5. **禁止**默认替 prompt_engineer 写完整英文 video prompt

# 八、版本记录

| 版本 | 更新时间 | 更新内容 | 更新人 |
| ---- | -------- | -------- | ------ |
| 1.0.0 | 2026-06-21 | 首版：前置收集→知识融合→分镜规划→镜头表→可选关键帧出图 | cokey |
