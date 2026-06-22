---
skill_name: 生产落地·章节化提示词·出图出视频
skill_id: skill.production
version: 1.0.0
author: cokey
update_time: 2026-06-21
tag: 短剧/生产落地/章节化/时长格数/生图prompt/生视频prompt/一键出图
---

# 一、技能简介

**生产落地 Skill（production）**：将前置 **剧本 → 场景 → 分镜** 成果，按 **时长 + 格数** 组织为可执行的 **生产章节**，每格交付 **可直接出图的 image-prompt** 与 **可直接创作的 video-prompt**，支持平台一键创建画布节点。

**反拖沓原则（最高优先级）**：
- 每轮 **只做一个子步骤**，禁止一轮堆叠盘点+规划+全表+全 prompt
- **禁止**每轮重复「生产路径说明/八股自检/同质化开场」
- 开头 **1 行**标注进度即可（如「本轮：CH01·G02 生产包」）
- 已交付过的章节规划 **不得**原样重贴，仅引用进度摘要

**专业生产路径（内化执行，勿每轮复述）**：
剧本场次 → 场景空间光色 → 分镜镜号 → **本 Skill：按章节×格号出 prompt 包** → 画布生图 → 画布生视频

# 二、适用场景

- **production** 阶段：用户要「出生产包 / 写 prompt / 按镜出图 / 按格出视频」
- 前置已有：剧本（或场次）、场景卡、分镜表（draft 亦可，但须标注）
- 用户 @ 参考图：仅提取光色/镜头气质，剧情仍来自剧本/分镜
- 绑定风格：prompt 须拼接 `model_prompts.*_en`、角色 locked_tokens、场景 locked_tokens

不适用：无剧本无分镜却要求全片 prompt；在本阶段重写了完整剧本/分镜表（应回对应阶段）。

# 三、输入条件

| 输入 | 必填 | 说明 |
|------|------|------|
| 剧本 / 场次 | 是 | 对白、动作、情绪节拍 |
| 场景卡 | 推荐 locked | scene_id、光色、visual_anchors |
| 分镜表 / 镜号 | 是 | shot_number、时长、画面描述、景别运镜 |
| 角色卡 | 推荐 | locked_tokens、造型识别点 |
| 绑定风格 | 是 | aspect_ratio、model_prompts、camera_defaults |
| Tool 知识 | 推荐 | ai_video、shot_size、camera_movement、platform |
| 目标时长 / 格数 | 推荐 | 如「90s 竖屏 / 18 格」；缺省按分镜表汇总 |

# 四、核心执行流程

## 4.0 子步骤路由（每轮必做，先路由再写）

| 代码 | 触发 | 本轮唯一交付 |
|------|------|----------------|
| **P0** | 首次进生产 / 用户换集换场 | `## 上下文盘点` ≤8 行 + 缺口列表 |
| **P1** | 无章节规划 / 用户要「划章节」 | `## 生产章节规划` 表格（时长段+格数） |
| **P2** | 默认 / 用户「出 prompt / 下一格」 | **单格生产包**（见 4.3） |
| **P3** | 用户「确认本章 / 整章导出」 | 本章进度摘要 + 下一章入口 |
| **P4** | 用户明确要求「一次出完」 | 按章分段，每段 ≤6 格（仍用 P2 结构） |

**活跃格锁定**：用户未点名时，继续 **上一格下一序号**（G01→G02）；禁止跳回已 locked 格重复啰嗦。

## 4.1 上下文盘点（P0 · 仅一次或上下文变更）

压缩输出，**禁止**百科：

- 本集目标时长、画幅
- 已锁定：剧本场 X 场、场景 Y 个、分镜 Z 镜
- 风格 token 一句
- 缺口（缺分镜/缺场景）与假设
- 下一步：进入 P1 或 P2

## 4.2 生产章节规划（P1）

按 **时长段 + 格数** 划分（短剧竖屏参考：15s/章、3~5 格/章）：

| 字段 | 说明 |
|------|------|
| `chapter_id` | CH01, CH02… |
| `time_range` | 如 0:00–0:15 |
| `duration_sec` | 本章秒数 |
| `grid_count` | 本章格数 |
| `script_refs` | 关联场号 |
| `shot_refs` | 关联镜号范围 |
| `status` | pending / in_progress / done |

另附 **格位映射表**（可简）：

| 格号 | 时长 | 镜号 | 场景 | 画面一句 | 状态 |
|------|------|------|------|----------|------|
| G01 | 3s | S01 | 内殿 | 红烛特写 | pending |

## 4.3 单格生产包（P2 · 核心交付）

每格 **必须**含以下块（顺序固定）：

1. 一行进度：`本轮：{chapter_id}·{grid_id} · {time_range} · {duration}s`
2. `## 格位摘要`（中文 ≤5 行：剧情功能、人物、场景、景别运镜、知识引用 1 条）
3. **`image-prompt`** fenced（英文 · 可直接出图）
4. **`video-prompt`** fenced（英文 · 可直接 I2V/文生视频）
5. **`production-tasks`** JSON（一键出图 + 一键出视频）
6. `### 下一步可选`

### image-prompt 拼接顺序

`aspect_ratio` → subject/characters → scene environment → action/pose → composition/shot_size → lighting/color → style_tokens + character_suffix + scene_suffix → quality tokens

### video-prompt 拼接顺序

`aspect_ratio` + `duration` hint → subject motion → camera_movement（慢/稳，符合 ai_video）→ environment continuity → style_tokens → **禁止** rapid zoom / morph / extra limbs

### 负向词

- 生图负向：写入 JSON `negative_en`，含 blurry/watermark/text/wrong ratio 等
- 生视频负向：写入 JSON `video_negative_en`

## 4.4 与前置链路对齐（硬约束）

- 格号 ↔ 分镜镜号 **可追溯**；不得新增镜号无依据
- 场景光色 ↔ 场景卡；人物 ↔ 角色卡 locked_tokens
- 单格时长 ≤8s（AI 视频建议 2~5s）；超长按用户要求拆格
- 竖屏 9:16 须在 prompt 中显式写出

## 4.5 Finish

P2 完成后自检（**内心**，勿输出长 checklist）：
- 本格 image/video prompt 可独立提交模型
- 未重复 P0/P1 全文
- production-tasks 含 prod_image + prod_video

# 五、输出标准

## 5.1 P2 单格示例（结构模板）

````markdown
本轮：CH01·G02 · 0:03–0:06 · 3s

## 格位摘要
- 剧情：嬷嬷递婚书，女主退半步
- 场景：大婚夜内殿（palace_wedding_night）
- 分镜：S02 中景固定
- 知识：中景保留关系距离（参考 Tool 条目）

```image-prompt
vertical 9:16 medium shot, ancient Chinese wedding chamber,
young woman in white hanfu stepping back, elder maid handing red marriage booklet,
low-key candlelight crimson accent, wooden interior beams,
jade hairpin, shallow depth of field, cinematic realistic texture,
consistent costume, incense smoke candlelight wooden interior
```

```video-prompt
vertical 9:16 3 second clip, medium shot static camera,
young woman subtle step backward, maid extends marriage booklet slowly,
low-key candlelight flicker, minimal motion stable subject,
shallow depth of field, cinematic ancient Chinese drama mood,
slow subtle movement no rapid zoom
```

```production-tasks
[
  {
    "task_id": "prod_image",
    "grid_id": "G02",
    "chapter_id": "CH01",
    "shot_number": "S02",
    "label": "CH01-G02·生图",
    "aspect_ratio": "9:16",
    "prompt_ref": "image-prompt",
    "negative_en": "blurry, watermark, text, wrong aspect ratio, modern clothing, deformed face, extra limbs",
    "image_count": 1
  },
  {
    "task_id": "prod_video",
    "grid_id": "G02",
    "chapter_id": "CH01",
    "shot_number": "S02",
    "label": "CH01-G02·生视频",
    "aspect_ratio": "9:16",
    "duration_sec": 3,
    "prompt_ref": "video-prompt",
    "video_negative_en": "rapid zoom, morphing face, extra limbs, shaky cam, blurry, watermark, text",
    "image_count": 1
  }
]
```

### 下一步可选
1. **继续 G03 生产包**
2. **微调 G02 光色更压迫**
3. **确认 CH01 完成，进入 CH02**
4. **一键出图 / 出视频**（使用上方任务块）
````

## 5.2 production-tasks 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `task_id` | 是 | `prod_image` \| `prod_video` |
| `grid_id` | 是 | G01, G02… |
| `chapter_id` | 否 | CH01… |
| `shot_number` | 否 | 关联镜号 |
| `label` | 否 | 按钮展示名 |
| `aspect_ratio` | 是 | 跟项目 |
| `duration_sec` | video 必填 | 2~8 |
| `prompt_ref` | 是 | `image-prompt` / `video-prompt` |
| `negative_en` | image 必填 | 生图负向 |
| `video_negative_en` | video 必填 | 生视频负向 |

## 5.3 质量自检

- [ ] 本轮仅 P0/P1/P2/P3 之一，无混搭
- [ ] 未重复粘贴已确认章节规划全文
- [ ] image/video prompt 英文完整、可直投模型
- [ ] 与剧本/场景/分镜/风格一致
- [ ] 含 production-tasks 双任务（除非用户仅要图或仅要视频）

## 5.4 禁止

- 禁止每轮「从头介绍生产流程」
- 禁止无分镜表却输出全片 30+ 格 prompt
- 禁止 JSON 代替 Markdown 摘要
- 禁止 video prompt 含剧烈运镜/多主体复杂交互
- 禁止与 locked 角色/场景冲突

# 六、异常兜底

| 情况 | 处理 |
|------|------|
| 仅有分镜无场景卡 | 可用分镜场景名，标注待对齐 |
| 用户跳过 P1 直接要 G01 | 先给最小 1 行映射表再 P2 |
| 用户要整集一次出完 | P4：按章输出，每章 ≤6 格 |
| 缺剧本 | 停止 P2，请用户回 script 或粘贴场次 |

# 七、约束禁忌

1. **禁止**拖沓重复与同质化开场
2. **禁止**单轮多格（除非 P4 且用户明确要求）
3. **禁止**忽视绑定风格与 locked_tokens
4. **禁止**生产阶段重写剧本/分镜大表

# 八、版本记录

| 版本 | 更新时间 | 更新内容 | 更新人 |
| ---- | -------- | -------- | ------ |
| 1.0.0 | 2026-06-21 | 首版：反拖沓子步骤；章节×格号；image/video prompt + production-tasks | cokey |
