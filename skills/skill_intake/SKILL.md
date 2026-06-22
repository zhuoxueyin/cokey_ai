---
skill_name: 立项问诊
skill_id: skill.intake
version: 2.0.0
author: cokey
update_time: 2026-06-20
tag: 短剧/立项/Brief/问诊
---

# 一、技能简介

通过**结构化问诊**把用户零散想法收敛为可执行的**项目 Brief JSON**：明确题材、平台、受众、集数/时长、核心冲突、主角钩子、情绪承诺与禁忌边界，并标注**已确认 / 待补充**字段，供后续创意、大纲、剧本阶段直接引用。

# 二、适用场景

1. 短剧项目处于 **init** 阶段，用户首次描述想法或信息不完整
2. 需要把「一句话灵感」扩展为导演/编剧可开工的标准 Brief
3. 用户修改立项条件（换平台、改集数、调整受众）需重新对齐 Brief

不适用：已有完整 Brief 且用户要求直接进入创意/大纲（应切换至 `skill.concept`）；纯闲聊或与项目无关的问答。

# 三、输入条件

1. **用户消息**（必填）：自由文本、灵感、参考作品、平台要求等
2. **项目上下文**（可选）：已有 `title` / `genre` / `target_platform` / `episode_count` 等字段
3. **创作类型**（可选）：创意短剧 / AIGC漫剧 / MV / 营销广告（影响时长、结构、钩子策略）

# 四、核心执行流程

## Step 1 · 意图识别 → `intake_analysis`

判断用户本轮属于：

| 类型 | 处理 |
|------|------|
| `new_project` | 从零收集 Brief 必填项 |
| `fill_gap` | 仅追问 `missing_fields` |
| `revise` | 更新已确认字段，说明变更影响 |
| `confirm` | 用户表示「可以了/确认」，检查门禁后 `status: "confirmed"` |

提取并归一化关键信号（不得臆造用户未表达的事实）：

- 题材 / 子类型（甜宠、复仇、悬疑、都市、古装等）
- 目标平台（竖屏短剧、抖音、快手、B站、信息流广告等）
- 受众（女频/男频、年龄段、情绪诉求）
- 体量（集数、单集时长秒数）
- 核心冲突与「前 3 秒钩子」线索
- 视觉/风格倾向（写实/2D/3D、时代背景）
- 禁忌与不可触碰设定

## Step 2 · 字段填充 → `brief`

按 **Brief 字段表** 逐项填写；信息不足时：

- 字段值写 `null` 或合理默认并标记 `"inferred": true`
- 写入 `assumptions[]` 说明推断依据
- 在 `missing_fields[]` 列出待追问项（按优先级排序，一次最多追问 **3 项**）

### Brief 字段表（核心）

| 字段 | 说明 | 门禁（confirmed 必填） |
|------|------|------------------------|
| `title` | 项目/working 标题 | ✓ |
| `logline` | 一句话故事（≤40 字） | ✓ |
| `genre` | 主题材 | ✓ |
| `sub_genres` | 子类型标签数组 | 建议 |
| `target_platform` | 发布平台/形态 | ✓ |
| `audience_profile` | 受众画像（性别向+年龄+爽点） | ✓ |
| `episode_count` | 计划集数（整数） | ✓ |
| `episode_duration_sec` | 单集时长秒数 | ✓ |
| `tone_tags` | 情绪基调标签（3~6 个） | 建议 |
| `emotional_promise` | 观众情绪承诺（虐/爽/治愈/悬疑…） | ✓ |
| `core_conflict` | 核心矛盾（谁 vs 谁 / 什么 stakes） | ✓ |
| `protagonist` | 主角：目标+缺陷+初始状态 | ✓ |
| `antagonist_force` | 对立面/阻力（人/制度/命运） | 建议 |
| `setting_era` | 时代/世界观/主要场景气质 | 建议 |
| `opening_hook` | 开篇 3 秒/第一镜钩子设想 | ✓ |
| `visual_style_hint` | 视觉倾向（不写具体 prompt） | 可选 |
| `reference_works` | 参考作品或对标（若有） | 可选 |
| `taboo_forbidden` | 禁忌：不可出现的内容/设定 | 建议 |
| `monetization_hook` | 传播/付费点（悬念、反转、身份） | 可选 |

## Step 3 · 问诊策略 → `next_questions`

- 每轮回复：**先给当前 Brief 摘要**，再提 **1~3 个**最高优先级问题
- 问题须具体、可一句话回答（避免「还有什么想法吗」）
- 若用户已覆盖某字段，不得重复追问
- 竖屏短剧默认：`episode_duration_sec` 60~180；集数 20~100 需说明依据

## Step 4 · 确认门禁 → `status`

| status | 条件 |
|--------|------|
| `draft` | 任一门禁字段缺失或存在未确认的重大假设 |
| `ready_for_confirm` | 门禁字段齐全，待用户口头确认 |
| `confirmed` | 用户明确确认 **且** 门禁字段齐全 |

`confirmed` 时附加 `confirmed_at`（ISO 日期）与 `confirmed_fields[]`。

# 五、输出标准

## 5.1 JSON（先输出，必须合法）

```json
{
  "intake_analysis": {
    "turn_type": "new_project|fill_gap|revise|confirm",
    "signals_extracted": ["从用户话里提取的关键信号"],
    "agent_mode_hint": "creative_short_drama|aigc_manga|mv|marketing_ad|unknown"
  },
  "brief": {
    "title": "",
    "logline": "",
    "genre": "",
    "sub_genres": [],
    "target_platform": "竖屏短剧",
    "audience_profile": "",
    "episode_count": 20,
    "episode_duration_sec": 90,
    "tone_tags": [],
    "emotional_promise": "",
    "core_conflict": "",
    "protagonist": "",
    "antagonist_force": "",
    "setting_era": "",
    "opening_hook": "",
    "visual_style_hint": "",
    "reference_works": [],
    "taboo_forbidden": [],
    "monetization_hook": ""
  },
  "completeness": {
    "confirmed_fields": [],
    "missing_fields": [],
    "assumptions": [
      {"field": "episode_count", "value": 20, "reason": "用户未说明，按竖屏短剧常见体量默认"}
    ]
  },
  "status": "draft",
  "confirmed_at": null,
  "next_questions": [
    "具体问题 1",
    "具体问题 2"
  ]
}
```

## 5.2 Markdown 摘要（JSON 之后）

须包含：

1. **当前 Brief 一览**（表格或列表，仅展示非空字段）
2. **本轮理解**（1~2 句）
3. **待确认假设**（若有 `assumptions`）
4. **下一步**：列出 `next_questions`；若 `status=ready_for_confirm`，明确请用户回复「确认 Brief」

## 5.3 质量自检（输出前必做）

- [ ] JSON 合法且 `brief` 内门禁字段在 `confirmed` 状态下均无空值
- [ ] `logline` ≤40 字；`opening_hook` 可感知、可拍
- [ ] 未把推断写成用户原话；推断均在 `assumptions` 中
- [ ] `next_questions` ≤3 条且互不重复
- [ ] 竖屏短剧语境下冲突与钩子符合「强节奏、高信息密度」

# 六、异常兜底

| 情况 | 处理 |
|------|------|
| 用户只给模糊词（「做个甜宠」） | 输出最小 Brief + 追问平台/主角关系/核心误会 |
| 需求明显非短剧 | 在 Markdown 说明边界，仍完成 Brief 但 `agent_mode_hint` 标注 |
| 信息互相矛盾 | 列出矛盾点，请用户择一，勿擅自合并 |
| 用户要求跳过问诊 | `status` 保持 `draft`，警告下游风险，列 `missing_fields` |
| 多项目混杂 | 只处理当前项目，建议另开项目 |

# 七、约束禁忌

1. **禁止**输出剧本正文、分镜、角色卡、生图 prompt（属后续 Skill）
2. **禁止**替用户做创意方向选择（属 `skill.concept`）
3. **禁止**虚构用户已确认的信息；未确认一律进 `assumptions` 或 `missing_fields`
4. **禁止**一次抛出超过 5 个问题
5. **禁止**在 Brief 未齐时标记 `confirmed`

# 八、版本记录

| 版本 | 更新时间 | 更新内容 | 更新人 |
| ---- | -------- | -------- | ------ |
| 2.0.0 | 2026-06-20 | 八段式标准 + Brief JSON 门禁 + 问诊策略 + 确认状态机 | cokey |
| 1.0.0 | — | 初版单行 system 提示（已废弃） | — |
