# AI 短剧创作 Agent 产品方案（v0.3）

> 基于 2026-06-18 方案评审延续；**图/视频生产仍走 cokey_ai 无限画布 + ModelGateway**，本 Agent 负责「创意 → 结构化资产 → 可执行提示词」。
> 关联：`agent.md` §零、`PROTOCOL_SPEC.md`（生产出口）、无限画布 `canvas_service.py`
> **v0.3.1 增量**：§5.7~5.8 参考 liblib 风格库 UI + 89 项内置风格种子目录

---

## 一、产品定位与边界

### 1.1 一句话定义

**导演型短剧 Agent**：在单个「短剧项目」内，通过对话 + Skill 编排，完成创意孵化、剧本、分镜、角色卡、场景卡与提示词包；**确认后的视觉/视频生产一键推到无限画布**，由现有图/视频节点 + 渠道网关执行。

### 1.2 做什么 / 不做什么

| 本 Agent 负责 | 不重复建设（复用 cokey_ai） |
|---------------|---------------------------|
| 项目记忆、阶段状态机、Skill 调度 | 模型/渠道/ProtocolProfile |
| 剧本/分镜/角色/场景结构化数据 | 最终文生图、图生视频任务 |
| 风格库 + 专业知识库检索注入 | CDN 上传、下载代理 |
| 一致性检查、格式转换 | TraceLog、TaskAdmin |
| **导出到画布**（节点模板 + config 映射） | 画布编辑器、节点 run、标记工具 |

### 1.3 目标产出链（用户视角）

```text
创意 Brief
  → 故事方案（卖点 / 大纲 / 集数规划）
  → 单集剧本（场景 / 对白 / 动作 / 情绪）
  → 分镜表（镜头 / 运镜 / 时长 / 提示词）
  → 角色卡 + 场景卡（视觉约束 + 参考图占位）
  → 【推到画布】每镜头：text/image/video 节点链
  → 用户在画布微调、批量 run、下载成片
```

---

## 二、系统架构

### 2.1 分层总览

```text
┌─────────────────────────────────────────────────────────────────┐
│ 前端：短剧项目空间（DramaStudio）                                  │
│  左：资产树（大纲/剧本/分镜/角色/场景/风格）                        │
│  中：导演对话（阶段条 + Skill 建议 + 确认设定）                     │
│  右：预览 / 一致性面板 / 「推到画布」                               │
└────────────────────────────┬────────────────────────────────────┘
                             │ POST /api/drama/*
┌────────────────────────────▼────────────────────────────────────┐
│ DramaOrchestrator（主控）                                         │
│  · 意图识别 + 阶段状态机                                          │
│  · 记忆切片加载（ProjectMemory）                                  │
│  · Skill 路由 + Tool 调用                                         │
│  · 风格库 / 知识库 RAG 注入                                       │
│  · 结构化输出校验（JSON Schema）                                  │
│  · trace_log 步骤记录                                             │
└───────┬─────────────────┬─────────────────┬─────────────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
   Skill Registry    Tool Layer      Knowledge + Style
   (Prompt+Schema)   (memory/RAG/     (向量检索 + 标签)
                      check/export)
        │                 │                 │
        └─────────────────┴─────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        ▼                                         ▼
  tasks/generate (text)                    canvas_service
  编剧/检查类 LLM 调用                      export_storyboard_to_canvas
        │                                         │
        └───────────────── 生产出口 ───────────────┘
                    无限画布 image/video 节点 run
```

### 2.2 与现有模块映射

| 新模块 | 复用/扩展 |
|--------|-----------|
| `DramaOrchestrator` | 新建；模式参考 `gateway_service` 的步骤 trace |
| Skill 模板 | 扩展 `prompt_service`，新增 `skill_code` + `stage` 维度 |
| 知识库 | 新建 `drama_knowledge` + **向量索引层**（见 §6.6） |
| 风格库 | 新建 `drama_style_presets` + 参考图 asset |
| Skill 注册 | `drama_skills` + **code / markdown 双源**（见 §4.5） |
| 项目记忆 | 新建 `drama_projects` 等；与 `sessions` 可 1:1 绑定 |
| 画布出口 | 扩展 `canvas_service`：`import_from_drama_shots()` |
| LLM 调用 | `ModelGateway.execute(category=text)` + `project_id` 上下文 |

---

## 三、创作阶段状态机

### 3.1 阶段枚举

| 阶段 | code | 主要 Skill | 用户确认门禁 |
|------|------|------------|--------------|
| 初始化 | `init` | `skill.intake` | 题材 / 平台 / 集数 / 时长 |
| 创意 | `concept` | `skill.concept` | Brief + 方向选定 |
| 大纲 | `outline` | `skill.outline` | 集数大纲锁定 |
| 剧本 | `script` | `skill.script` | 单集剧本 `confirmed` |
| 角色 | `character` | `skill.character` | 角色卡 `locked` |
| 场景 | `scene` | `skill.scene` | 场景卡 `locked` |
| 分镜 | `storyboard` | `skill.storyboard` | 分镜表 `confirmed` |
| 提示词包 | `prompt_pack` | `skill.prompt_engineer` | 可导出 |
| 生产 | `production` | —（画布） | 用户在画布 run |

**规则**：
- 仅 `status=confirmed|locked` 的实体进入 **长期记忆注入** 与 **一致性检查基准**
- `draft` 可对话内多版本并存；用户「确认」后升版并写 `confirmed_at`
- 主控每轮回复附带 **建议下一步**（可跳过阶段，但须警告缺失依赖）

### 3.2 意图路由（Orchestrator）

```text
用户消息
  → classify_intent: continue | revise | expand | check | export_canvas | apply_style
  → resolve_stage: 当前项目 stage + 用户显式跳转
  → pick_skills: 1 主 Skill + 0~2 辅助（如 script + consistency）
  → build_context: 记忆切片 + 风格 preset + 知识库 top-k
  → execute → validate_schema → persist_draft → render_markdown_block
```

---

## 四、Skill 体系设计

### 4.1 Skill 定义结构

每个 Skill 是 **可版本化的 Prompt Profile + 输出 Schema + 工具依赖**，存 MongoDB `drama_skills`（或复用 `prompts` 加 namespace）。

```json
{
  "skill_code": "skill.storyboard",
  "name": "分镜导演",
  "stage": "storyboard",
  "version": "1.0.0",
  "system_prompt_ref": "prompt_versions:xxx",
  "user_prompt_template": "…{{episode_script}}…{{style_preset}}…{{knowledge_snippets}}…",
  "output_schema": "schemas/shot_list.v1.json",
  "required_memory": ["project", "characters", "scenes", "episode_script"],
  "optional_tools": ["consistency_check", "knowledge_search", "format_convert"],
  "default_knowledge_tags": ["shot_size", "camera_movement", "vertical_framing"],
  "model_hint": { "category": "text", "temperature": 0.7 }
}
```

### 4.2 Skill 清单（MVP → 完整）

| skill_code | 名称 | 输入 | 输出 |
|------------|------|------|------|
| `skill.intake` | 立项问诊 | 用户自由文本 | 项目 Brief JSON |
| `skill.concept` | 创意策划 | Brief + 风格 | 3~5 方向 + 推荐 |
| `skill.outline` | 剧集大纲 | 选定方向 + 集数 | Episode[] 摘要 |
| `skill.script` | 编剧 | 本集大纲 + 角色 | ScriptScene[] |
| `skill.character` | 人设 | 大纲/剧本 | CharacterCard[] |
| `skill.scene` | 场景设计 | 剧本场景列表 | SceneCard[] |
| `skill.storyboard` | 分镜导演 | 剧本 + 角色 + 场景 + 风格 | Shot[] |
| `skill.action` | 动作设计 | 剧本片段 / Shot | ActionBeat[] |
| `skill.prompt_engineer` | 提示词工程 | Shot + 角色/场景卡 | image_prompt + video_prompt + negative |
| `skill.consistency` | 一致性审查 | 项目快照 | Issue[] + 修复建议 |
| `skill.viral_tune` | 爆款优化 | 剧本/标题 | 钩子/标题/切片建议 |
| `skill.format_convert` | 格式转换 | 任意阶段文档 | 目标阶段 draft |

### 4.3 Skill 调用协议（Orchestrator 内部）

```python
# 伪代码
async def run_skill(skill_code, project_id, inputs, overrides):
    skill = skill_registry.get(skill_code)
    memory = project_memory.slice(skill.required_memory)
    style = style_library.resolve(project.style_preset_id)
    knowledge = knowledge_service.search(
        query=inputs.get("query") or skill.default_query(memory),
        tags=skill.default_knowledge_tags,
        top_k=6,
    )
    prompt = render_template(skill, memory, style, knowledge, inputs)
    result = await gateway.execute(category="text", params={"prompt": prompt, ...})
    parsed = validate_json(result, skill.output_schema)
    await project_repo.save_draft(project_id, skill.stage, parsed)
    trace.append_step("skill_invoke", skill_code=skill_code)
    return parsed, render_markdown(parsed)
```

### 4.4 Skill 与 PromptManager 关系

- **内置种子（code 源）**：仓库 `backend/app/core/drama_skills/` 随版本发布，不可在 Admin 直接改内容，仅可「启用/禁用/覆盖参数」
- **运营可配（markdown 源）**：管理端 CRUD，走 Prompt 版本流
- **A/B**：项目级可覆盖 `skill_overrides`（如更虐/更爽微调块）

### 4.5 Skill 运营化管理（新增 / 编辑 / 删除）

#### 4.5.1 设计原则

| 原则 | 说明 |
|------|------|
| **双源合一** | 运行时 `SkillRegistry` 合并 code 源 + DB 源；同 `skill_code` 时 **DB 运营版优先**（可配置） |
| **不可硬删内置** | code 源 Skill 仅 `disabled`；DB 源支持软删 `deleted_at` |
| **版本可追溯** | 每次编辑产生新版本；Orchestrator trace 记录 `skill_code + version` |
| **发布门禁** | `draft → review → published`；仅 published 对生产项目可见 |

#### 4.5.2 两种编写模式

**模式 A：`code`（代码库源）**

适用：核心 Skill、复杂 JSON Schema 校验、需单测的逻辑型 Skill。

```text
backend/app/core/drama_skills/
  skill.storyboard/
    manifest.yaml          # skill_code、stage、schema 路径、默认知识标签
    system.md                # 系统提示（可选，也可内联 yaml）
    user_template.jinja2     # 用户模板
    schema.shot_list.v1.json
    handler.py               # 可选：post_process / 自定义 tool 编排
```

- 部署时 `SkillLoader.scan_repo()` 注册到内存 + 写入 `drama_skills` 索引行（`source=code`, `immutable=true`）
- Admin 可改：`enabled`、`default_model_code`、`knowledge_tags[]`，**不可改** prompt 正文（须走 PR）

**模式 B：`markdown`（文本运营源）**

适用：运营/编剧同学快速迭代 Prompt，无需发版。

Admin 表单字段：

| 字段 | 说明 |
|------|------|
| `skill_code` | 全局唯一；新建时自动生成或手填 |
| `name` / `stage` / `description` | 展示与路由 |
| `system_markdown` | 系统提示（Markdown，支持变量说明块） |
| `user_markdown` | 用户侧模板（Jinja2 变量：`{{project}}` `{{style}}` `{{knowledge}}`） |
| `output_schema_id` | 绑定平台 JSON Schema |
| `required_memory[]` / `default_knowledge_tags[]` | 注入配置 |
| `model_hint` | 推荐模型 / temperature |
| `examples[]` | Few-shot 示例（Markdown 块） |

- 保存 → 新版本 `draft`；「发布」→ `published`，旧版 `archived`
- 支持 **从 code 源 Fork 为 markdown 源**（复制后独立演进）

#### 4.5.3 Skill 注册表结构（扩展）

```json
{
  "skill_id": "sk_xxx",
  "skill_code": "skill.storyboard",
  "source": "code | markdown",
  "source_ref": "repo:skill.storyboard@v1.2.0 | db:sk_xxx",
  "immutable": false,
  "version": "1.3.0",
  "status": "draft | review | published | archived | disabled",
  "system_markdown": "…",
  "user_markdown": "…",
  "output_schema_id": "shot_list.v1",
  "published_at": "2026-06-19T00:00:00Z",
  "published_by": "user_id",
  "changelog": "优化竖屏拆镜规则"
}
```

#### 4.5.4 Admin API（Skill）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/drama/skills` | 列表（source/status/stage 筛选） |
| POST | `/api/admin/drama/skills` | 新建 markdown 源 |
| GET | `/api/admin/drama/skills/{id}` | 详情 + 版本历史 |
| PUT | `/api/admin/drama/skills/{id}` | 编辑 → 新 draft 版本 |
| POST | `/api/admin/drama/skills/{id}/publish` | 发布 |
| POST | `/api/admin/drama/skills/{id}/fork` | 从 code 或他人版本 Fork |
| DELETE | `/api/admin/drama/skills/{id}` | 软删（仅 markdown 源） |
| POST | `/api/admin/drama/skills/{id}/test` | 沙箱试跑（指定 project fixture） |

前端页：`/admin/drama/skills` — 列表 + Markdown 编辑器 + Schema 绑定 + 试跑面板

---

## 五、风格库（Style Library）

### 5.1 定位

风格库是 **跨 Skill 的视觉与叙事约束包**，避免每个 Skill 各自发挥导致人物/光影/节奏漂移。

### 5.2 风格标准规范（StyleSpec v1）

风格库条目须符合 **StyleSpec v1**，保证 LLM / 生图 / 生视频模型可稳定解析。分为 **结构化字段** + **模型提示词包** + **参考图** 三部分。

```json
{
  "style_id": "ancient_revenge_cinematic_vertical",
  "spec_version": "1.0",
  "name": "古风复仇 · 电影感竖屏",
  "origin": "template | manual | reverse_from_image",
  "genre_tags": ["女频", "重生", "复仇", "古风"],
  "narrative": {
    "pace": "fast",
    "hook_style": "3s_conflict",
    "dialogue_density": "short_punchy",
    "emotion_curve": "压抑→爆发→冷静复仇"
  },
  "visual": {
    "aspect_ratio": "9:16",
    "color_palette": ["深红", "玄黑", "冷白", "玉色点缀"],
    "lighting": "low_key_dramatic",
    "texture": "cinematic_realistic",
    "reference_films": ["《影》室内光影", "《一代宗师》对峙构图"]
  },
  "camera_defaults": {
    "preferred_shot_sizes": ["close_up", "medium_close"],
    "movement_bias": ["slow_push_in", "static_tension"],
    "avoid": ["超广角变形", "复杂多人全景"]
  },
  "model_prompts": {
    "style_summary_zh": "古风复仇、电影感竖屏、低调光影、冷色为主红点缀",
    "style_summary_en": "ancient Chinese revenge drama, cinematic vertical framing, low-key dramatic lighting",
    "image_positive_en": "cinematic, low key lighting, vertical 9:16, muted palette with red accent, realistic texture, shallow depth of field",
    "image_negative_en": "blurry, oversaturated, modern clothing, cartoon, watermark, text",
    "video_positive_en": "slow push-in, cinematic motion, stable subject, shallow DOF, 9:16 vertical",
    "video_negative_en": "rapid zoom, morphing face, extra limbs, shaky cam",
    "character_suffix_en": "consistent costume, jade hairpin, cold expression",
    "scene_suffix_en": "incense smoke, candlelight, wooden interior"
  },
  "locked_tokens": ["white hanfu", "jade hairpin"],
  "reference_images": [
    {
      "asset_id": "ast_xxx",
      "role": "moodboard | character | scene | color_ref",
      "caption_zh": "大婚夜低光红色烛火参考",
      "weight": 1.0
    }
  ],
  "status": "draft | published | archived",
  "created_by": "user_id",
  "reverse_meta": {
    "source_asset_id": "ast_yyy",
    "model_code": "gpt-4o",
    "derived_at": "2026-06-19T00:00:00Z",
    "confidence": 0.86
  }
}
```

**StyleSpec 校验**：Admin 保存 / 发布前跑 JSON Schema + `model_prompts.*_en` 非空检查；可选试跑「用该风格生成一条 image_prompt 样例」。

### 5.3 风格创建方式（三种入口）

| 入口 | 流程 | 适用 |
|------|------|------|
| **标准模板** | Admin 选模板（电影感/竖屏爽剧/赛博/新海诚风…）→ 填表 → 校验 → 发布 | 运营手工精调 |
| **复制派生** | 从已有 preset Fork → 改 modifier 字段 | 快速变体 |
| **参考图反推** | 上传 1~5 张 moodboard → Vision LLM 反推 StyleSpec → 人工校对 → 发布 | 有明确视觉参考 |

**参考图反推流程**（`POST /api/admin/drama/styles/reverse-from-image`）：

```text
上传图片 → CDN asset
  → Vision LLM（平台 text 模型 + images 多模态，如 GPT-4o / 同级）
  → 输出 StyleSpec v1 JSON draft（含 model_prompts + color_palette + camera_defaults）
  → Admin 表单预填 + 侧栏展示原图
  → 运营编辑 / 锁定 locked_tokens
  → 校验 → published
```

反推 Prompt 要点：要求模型只输出 StyleSpec JSON；`reference_images` 自动绑定上传图；低置信度字段标 `needs_review`。

### 5.4 风格库层级

| 层级 | 说明 | 示例 |
|------|------|------|
| **平台内置** | 运营维护，全员可用 | 竖屏爽剧 / 横屏电影感 / 甜宠高亮 / 悬疑冷调 |
| **项目绑定** | 创建项目时选 1 主风格 + 可叠加 modifier | 主风格 +「更虐」「更低成本 AI」 |
| **镜头级 override** | 分镜 Shot 可覆盖单镜光影 | 回忆镜头加 `desaturated` |

### 5.5 风格注入点

- `skill.script`：注入 `narrative.*` + `style_summary_zh`
- `skill.character`：注入 `model_prompts.character_suffix_en` + `locked_tokens` + 角色参考图
- `skill.scene`：注入 `visual.*` + `scene_suffix_en` + moodboard 图
- `skill.storyboard`：注入 `camera_defaults` + `aspect_ratio`
- `skill.prompt_engineer`：拼接完整 `model_prompts.image/video_*` + 参考图 URL（图生图连线）

图生图/视频时：`reference_images` 中 `role=moodboard|character` 的 CDN URL 进入 `params.images`（复用现有 CDN 校验）。

### 5.6 风格库运营化管理

#### Admin API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/drama/styles` | 列表（tags/status/origin） |
| POST | `/api/admin/drama/styles` | 模板创建 |
| POST | `/api/admin/drama/styles/reverse-from-image` | 上传图反推 StyleSpec |
| GET/PUT | `/api/admin/drama/styles/{id}` | 详情 / 编辑 |
| POST | `/api/admin/drama/styles/{id}/publish` | 发布 |
| POST | `/api/admin/drama/styles/{id}/fork` | 复制派生 |
| DELETE | `/api/admin/drama/styles/{id}` | 软删（内置 preset 仅 archive） |
| POST | `/api/admin/drama/styles/{id}/validate` | Schema + 试生成样例 prompt |

#### 前端页 `/admin/drama/styles`

- 列表 + 卡片预览（主 moodboard 缩略图）
- 表单：StyleSpec 分区折叠（叙事 / 视觉 / 模型提示词 / 参考图）
- 「从图片反推」向导：上传 → 反推 →  diff 对比 → 发布
- 用户侧项目创建：仅可选 `published` 风格

### 5.7 用户侧风格库 UI（参考 liblib）

**布局**（与参考图一致）：

| 区域 | 行为 |
|------|------|
| 标题 | 「风格库」 |
| Tab | **全部** / **真人** / **2D** / **3D** — 按 `render_class` 筛选 |
| 搜索 | 按 `name` / `genre_tags` 模糊搜 |
| 网格 | 5 列卡片；圆角缩略图 + 底部渐变条 + 白字风格名 |
| 选中态 | 卡片紫色描边（`--primary`） |
| 首卡特殊项 | **自定义风格提示词** — 不进 preset 库，打开 StyleSpec 手工/反推编辑器 |

**数据字段（列表卡片）**：

```json
{
  "style_id": "retro_sci_fi_atompunk",
  "name": "复古科幻原子朋克",
  "render_class": "live_action",
  "cover_asset_id": "ast_xxx",
  "genre_tags": ["科幻", "复古"],
  "status": "published"
}
```

**筛选映射**：`render_class` → Tab

| Tab | `render_class` 值 |
|-----|---------------------|
| 全部 | 不过滤 |
| 真人 | `live_action` |
| 2D | `illustration_2d` |
| 3D | `render_3d` |

### 5.8 内置风格种子目录（参考图全量，共 89 项 + 1 自定义入口）

> 来源：产品参考图风格库全量截图。MVP 入库时：每项需 **封面图 asset** + **StyleSpec v1**（可批量「参考图反推」补全 `model_prompts`）。  
> `style_id` 为建议 slug；`render_class` 用于 Tab 筛选。

#### 5.8.1 特殊入口（非 preset）

| style_id | 名称 | 说明 |
|----------|------|------|
| `_custom` | 自定义风格提示词 | 用户/运营手工填写 StyleSpec 或上传反推，不占用内置 id |

#### 5.8.2 真人 / 写实影视（`live_action`，35 项）

| # | style_id | 名称 |
|---|----------|------|
| 1 | `retro_sci_fi_atompunk` | 复古科幻原子朋克 |
| 2 | `palace_intrigue_cold` | 宫斗权谋冷峻风格 |
| 3 | `cn_suspense_cold_tone` | 国产悬疑冷调 |
| 4 | `ancient_romance_soft_glow` | 古偶唯美柔光 |
| 5 | `jp_youth_film` | 日式青春胶片 |
| 6 | `jp_life_natural` | 日式生活自然 |
| 7 | `kdrama_urban_soft` | 韩剧都市柔光 |
| 8 | `cn_urban_realistic` | 国产都市写实 |
| 9 | `wuxia_realistic_photo` | 武侠江湖写实摄影风格 |
| 10 | `cn_90s_realistic_film` | 90年代写实电影风格 |
| 11 | `retro_narrative_film` | 复古叙事电影风格 |
| 12 | `american_retro_hollywood` | 美式复古好莱坞 |
| 13 | `neon_cyber_film` | 霓虹赛博电影风格 |
| 14 | `cn_90s_rural_film` | 90年代中国农村电影风格 |
| 15 | `cn_warm_blue_glow` | 中式暖调蓝辉风格 |
| 16 | `vintage_industrial_film` | 老式工业影视风格 |
| 17 | `jp_bw_film_photo` | 日本黑白胶片摄影风格 |
| 18 | `kr_cold_minimal_film` | 韩国冷淡风电影风格 |
| 19 | `wilderness_cinematic` | 荒野电影风格 |
| 20 | `orange_yellow_cinematic` | 橙黄色电影风格 |
| 21 | `retro_war_film` | 复古战争电影风格 |
| 22 | `horror_film` | 恐怖电影风格 |
| 23 | `retro_cinematography` | 复古电影摄影风格 |
| 24 | `american_retro_weird` | 美式复古怪异影视风格 |
| 25 | `absurdist_high_key_white` | 荒诞高调白色调电影风格 |
| 26 | `teal_orange_cinematic` | 蓝橙色调影视风格 |
| 27 | `industrial_film` | 工业电影风格 |
| 28 | `american_boom_era` | 美式经济上行风格 |
| 29 | `hk_90s_film` | 90年代港片风格 |
| 30 | `tech_cinematic` | 科技感电影风格 |
| 31 | `suspense_film` | 悬疑电影风格 |
| 32 | `greek_mythology_film` | 希腊神话电影风格 |
| 33 | `american_retro_film_tv` | 美式复古影视风格 |
| 34 | `hollywood_bw_classic` | 好莱坞黑白电影风格 |
| 35 | `purple_tone_cinematic` | 紫色色调电影风格 |

#### 5.8.3 2D 插画 / 二维动画（`illustration_2d`，29 项）

| # | style_id | 名称 |
|---|----------|------|
| 1 | `anime_concept_art_2d` | 二次元概念艺术风格 |
| 2 | `anime_3render2` | 动漫三渲二风格 |
| 3 | `jp_flat_illustration` | 日系平涂插画风格 |
| 4 | `vaporwave_illustration` | 插画蒸汽波风格 |
| 5 | `cyberpunk_digital_illustration` | 赛博朋克数字插画风格 |
| 6 | `game_concept_art` | 游戏概念艺术风格 |
| 7 | `guoman_2d_illustration` | 国漫二维插画风格 |
| 8 | `dali_surreal` | 达利风格 |
| 9 | `bw_ink_wash` | 黑白水墨风格 |
| 10 | `american_comic_sketch` | 美国漫画简笔插画风格 |
| 11 | `retro_psychedelic_texture` | 复古肌理迷幻插画风格 |
| 12 | `children_crayon_handdrawn` | 儿童蜡笔手绘插画风格 |
| 13 | `bw_2d_comic_animation` | 黑白二维漫画动画风格 |
| 14 | `hq_2d_shonen_anime` | 高质量2D热血动漫风格 |
| 15 | `2d_cartoon_illustration` | 二维卡通插画风格 |
| 16 | `dark_concept_art` | 黑暗原画概念风格 |
| 17 | `shadow_puppet_illustration` | 皮影戏插画风格 |
| 18 | `american_dark_illustration` | 美式黑暗插画风格 |
| 19 | `dark_fantasy_illustration` | 黑暗奇幻插画风格 |
| 20 | `dark_manga` | 暗黑漫画风格 |
| 21 | `minimal_illustration` | 简洁插画风格 |
| 22 | `retro_halftone_gothic` | 复古半色调暗色调哥特风格 |
| 23 | `traditional_ink_wash` | 传统水墨风格 |
| 24 | `moe_kawaii` | 萌系风格 |
| 25 | `retro_y2k_fantasy` | 复古Y2K奇幻风格 |
| 26 | `hq_animation_render` | 高品质动画渲染风格 |
| 27 | `clay_animation` | 粘土动画风格 |
| 28 | `stop_motion` | 定格动画风格 |
| 29 | `american_game_concept_art_2d` | 美国游戏概念艺术风格 |

> 说明：`粘土动画` / `定格动画` 视觉偏 3D 质感，参考图归在「全部」混合展示；若 Tab 互斥严格，可改划 `render_3d`，运营配置 `render_class` 即可。

#### 5.8.4 3D 渲染 / 三维（`render_3d`，25 项）

| # | style_id | 名称 |
|---|----------|------|
| 1 | `3d_stylized_render` | 3D风格化渲染 |
| 2 | `3d_digital_sculpt` | 3D数字雕刻风格 |
| 3 | `3d_cn_style_hd` | 3D国风高清渲染风格 |
| 4 | `3d_american_cartoon_game` | 3D美式卡通游戏美术 |
| 5 | `3d_blind_box_paint` | 3D盲盒涂装风 |
| 6 | `3d_surreal_render` | 超现实3D渲染风格 |
| 7 | `ue5_realistic_render` | UE5写实渲染 |
| 8 | `3d_cn_fantasy_hd` | 国风3D高清渲染风格 |
| 9 | `3d_cartoon_render` | 3D卡通渲染风格 |
| 10 | `3d_american_cartoon_render` | 美国卡通3D渲染风格 |
| 11 | `3d_impasto_paint` | 3D厚涂风格 |
| 12 | `3d_pbr_realistic` | 3D真实感PBR渲染风格 |
| 13 | `3d_game_render` | 3D游戏渲染风格 |
| 14 | `3d_character_simple_cartoon` | 3D人物(简约卡通风) |
| 15 | `3d_cartoon_animation` | 3D卡通动画风格 |
| 16 | `3d_diorama_miniature` | 3D卡通微缩景观 |
| 17 | `3d_western_cartoon_draw` | 3D西方卡通风格的绘制 |
| 18 | `western_stylized_3d` | 欧美风格化3D渲染 |
| 19 | `3d_fantasy_rpg` | 3D魔幻角色扮演游戏 |
| 20 | `3d_enhanced_cartoon_render` | 3D加强版卡通渲染风格 |
| 21 | `3d_cn_fantasy_animation` | 3D中国奇幻动画 |
| 22 | `3d_glossy_latex` | 3D光泽乳胶渲染风格 |
| 23 | `3d_jelly_plastic` | 3D果冻状塑料风格 |
| 24 | `3d_western_cartoon` | 3D西方卡通风格 |
| 25 | `3d_hd_realistic_render` | 高清3D真实渲染风格 |

#### 5.8.5 种子入库 Checklist（运营 / 研发）

每条内置风格发布前须满足：

| 项 | 要求 |
|----|------|
| 封面 | `reference_images[0].role=cover`，CDN 就绪 |
| StyleSpec | `spec_version=1.0`，`model_prompts.*_en` 非空 |
| 分类 | `render_class` + `genre_tags[]` |
| 来源 | `origin=seed`，`source_ref=liblib_style_catalog_v1` |
| 状态 | 批量导入默认 `draft` → 反推/校对 → `published` |

**批量初始化建议**：

```text
1. 将参考图 89 张上传 assets，按 style_id 命名
2. 跑 batch reverse-from-image → StyleSpec draft
3. 运营抽检 10% + 全量 validate
4. 发布并写入 drama_style_presets 种子
```

**API 扩展（可选）**：

```http
POST /api/admin/drama/styles/seed/import-catalog
  Body: { "catalog_version": "liblib_v1", "mode": "draft_only" }
```

---

## 六、知识库（专业知识沉淀）

### 6.1 定位

知识库是 **可检索、可标签、可版本、可导入** 的专业知识片段库，覆盖短剧、AIGC、动漫、电影等域；在 Skill 执行前按需 **混合检索**（标签过滤 + 关键词 + 向量语义）注入 top-k。

**与 MongoDB 关系**：MongoDB 存 **权威元数据与正文**；向量引擎存 **检索索引**（可重建）。

### 6.2 知识类型体系（可扩展）

一级 `category`（运营可扩展，内置种子如下）：

| category | 中文 | 子域示例 |
|----------|------|----------|
| `short_drama` | 短剧 | 钩子结构、集尾悬念、女频/男频节拍 |
| `film` | 电影 | 镜头语言、蒙太奇、类型片叙事 |
| `anime` | 动漫 | 分格节奏、演出符号、新海诚/京阿尼风构图 |
| `aigc` | AIGC | 文生图/视频 prompt 结构、负向词、模型 quirks |
| `cinematography` | 摄影 | 景别、机位、运镜、焦段 |
| `color_light` | 色彩与光影 | 配色情绪、光位、LUT 气质 |
| `composition` | 构图 | 三分法、引导线、竖屏安全区 |
| `performance` | 表演 | 微表情、短剧外化、动作节拍 |
| `sound` | 声音 | BGM 情绪、音效点（分镜标注用） |
| `platform` | 平台 | 抖音/快手竖屏规范、字幕区 |
| `custom` | 自定义 | 团队私有域 |

每条知识除 `category` 外还有 `domain`（细分类，兼容 v0.2 的 `film_grammar` 等）与自由 `tags[]`。

### 6.3 知识域分类（domain 细项，兼容 v0.2）

| domain | 中文 | 典型条目 | 主要消费 Skill |
|--------|------|----------|----------------|
| `film_grammar` | 电影语法 | 180°规则、轴线、视线匹配 | storyboard |
| `shot_size` | 景别 | 特写/近景/中景/全景功能与情绪 | storyboard, prompt_engineer |
| `camera_angle` | 机位 | 平视/俯拍/仰拍心理含义 | storyboard |
| `camera_movement` | 运镜 | 推/拉/摇/移/跟/升降/手持 | storyboard, prompt_engineer |
| `lens` | 镜头焦段 | 35mm 叙事 / 85mm 人像压缩 | storyboard |
| `composition` | 构图 | 三分法、框中框、对称、负空间 | storyboard, scene |
| `color` | 配色 | 冷暖对比、单色强调、情绪色板 | scene, prompt_engineer |
| `lighting` | 光影 | 高调/低调、伦勃朗光、剪影 | scene, prompt_engineer |
| `blocking` | 场面调度 | 站位、距离=关系、群戏简化 | script, storyboard |
| `performance` | 表演 | 微表情、克制崩溃、短剧外化冲突 | script, action |
| `short_drama` | 短剧结构 | 3s 钩子、15s 困境、集尾悬念 | concept, outline, script, viral_tune |
| `ai_video` | AI 视频约束 | 单主体、少复杂交互、5s 镜头限制 | storyboard, prompt_engineer |
| `genre` | 类型套路 | 重生复仇节拍、甜宠误会模板 | concept, outline |
| `platform` | 平台规范 | 竖屏安全区、字幕区留白 | storyboard |

### 6.4 知识条目结构（扩展）

```json
{
  "entry_id": "kb.camera_movement.push_in",
  "category": "cinematography",
  "domain": "camera_movement",
  "tags": ["推镜头", "情绪聚焦", "竖屏可用"],
  "title": "推镜头（Push In）",
  "summary": "镜头向前靠近主体，强化情绪或揭示细节。",
  "content_markdown": "正文（可更长，Admin Markdown 编辑）",
  "when_to_use": ["情绪升级", "发现关键线索"],
  "when_to_avoid": ["已极近特写再推", "AI 视频 rapid zoom 易变形"],
  "examples": [{ "scenario": "女主发现背叛", "shot_hint": "从 MS 推至 CU，3-4s" }],
  "prompt_tokens_en": ["slow push-in", "dolly in"],
  "related_entries": ["kb.shot_size.close_up"],
  "source": {
    "type": "manual | import | seed",
    "import_job_id": "imp_xxx",
    "document_name": "运镜手册.pdf",
    "chunk_index": 3
  },
  "embedding": {
    "model": "text-embedding-3-small",
    "vector_id": "kb.camera_movement.push_in@v1"
  },
  "version": 1,
  "status": "draft | published | archived",
  "published_at": null
}
```

**Chunk 级导入**：长文档切分为多条 `entry`，共享 `source.import_job_id`，检索时去重同文档相邻 chunk。

### 6.5 文档导入（按知识类型）

Admin 入口：`/admin/drama/knowledge/import`

| 步骤 | 说明 |
|------|------|
| 1. 选 category | 如 `anime` / `film` / `aigc` |
| 2. 上传 | `.md` / `.txt` / `.pdf` / `.docx`（MVP 先 md+txt） |
| 3. 解析 | 提取文本 → 按标题/段落/chunk（512~1024 token）切分 |
| 4. LLM 结构化（可选） | 每 chunk → 提取 title/summary/when_to_use/prompt_tokens |
| 5. 预览 | 运营逐条确认 / 批量编辑 / 丢弃 |
| 6. 入库 | 写 MongoDB + 异步写向量索引 |
| 7. 发布 | `draft` → `published` |

API：

```http
POST /api/admin/drama/knowledge/import
  Body: multipart { file, category, domain?, auto_structure?: bool }
GET  /api/admin/drama/knowledge/import/{job_id}   # 进度 / 预览
POST /api/admin/drama/knowledge/import/{job_id}/commit
```

**扩展口子**：`category` 与 `import_parser` 插件映射（如 `anime` 用分镜术语表增强切分），代码库注册 `KnowledgeImportParser` 接口，运营配置无需发版即可挂新类型。

### 6.6 检索策略（混合检索）

```text
1. 硬过滤：category/domain/tags/status=published（向量引擎 payload 同步）
2. 混合打分：
   score = 0.45 * vector_sim + 0.35 * BM25(keyword) + 0.20 * tag_overlap
3. 去重：同 import_job 相邻 chunk 合并为一条 snippet
4. 预算裁剪：按 Skill 模板槽位 ≤ 1200 中文字（可配置）
5. 输出：KnowledgeSnippet[] + entry_id 列表（trace + 前端「引用知识」）
```

### 6.7 向量检索引擎选型（建议）

#### 现状与约束

- 平台已具备：**MongoDB（主库）**、**Redis（可选缓存）**，尚无 ES/OpenSearch
- 知识库规模预期：MVP **500~2k 条** → 1 年内 **2~10 万 chunk**
- 检索需求：**语义相似 + 专业术语精确匹配**（如「推镜头」「180°规则」）+ 多维过滤（category/domain/tags）

#### 方案对比

| 方案 | 优点 | 缺点 | 适用 |
|------|------|------|------|
| **Elasticsearch 8.x** | BM25 + kNN 混合检索成熟；导入 pipeline；聚合统计；运营熟悉 | 运维较重；内存占用高；向量维度/版本要规划 | **有运维能力、重视混合检索与文档导入** |
| **OpenSearch 2.x** | 与 ES 能力接近；开源协议友好 | 生态略滞后于 ES 8 | 自建、避 ES 许可顾虑 |
| **Qdrant** | 向量专精、轻量、payload 过滤好、易 Docker | 弱全文；需自拼 BM25 层 | 向量为主、条目已结构化 |
| **MongoDB Atlas Vector** | 与 Mongo 一体 | 当前自建 Mongo **不可用** | 仅云 Mongo 场景 |
| **pgvector** | 关系型 + 向量 | 新增 PostgreSQL 栈 | 已有 PG 的团队 |
| **纯 Mongo + 内存 brute** | 零新增组件 | 规模 >5k 性能差；无语义 | **仅 MVP 0~2k 条过渡** |

#### 推荐路线（分阶段）

**阶段 A — MVP（迭代 1~2，可 4~6 周）**

```text
MongoDB（权威存储）
  + MongoDB text index（title/summary/tags 关键词）
  + 可选：条目量 <2k 时内存 cosine（启动时加载 embedding）
  + Redis 缓存 hot query
```

- Embedding 调用：走平台已有 text 渠道或独立 embedding API（`text-embedding-3-small` 等）
- **不阻塞 MVP 交付**；接口层抽象 `KnowledgeSearchBackend`，便于切换

**阶段 B — 生产（迭代 4~5 或条目 >5k / 导入文档量上来）**

**首选推荐：Elasticsearch 8.x（单集群）**

理由：
1. 知识库同时有 **专业名词精确匹配** 与 **语义检索**，ES 混合检索最省心
2. 文档导入后的 **全文检索 + 高亮 + 聚合**（按 category 统计、运营审计）开箱即用
3. 与 Mongo **主从同步**模式清晰：Mongo 为 source of truth，ES 为 `drama_knowledge_index`（可重建）
4. 后续可接 **ingest pipeline**（PDF 解析、chunk、embedding 一条龙）

建议索引 mapping 要点：

```json
{
  "entry_id": "keyword",
  "category": "keyword",
  "domain": "keyword",
  "tags": "keyword",
  "title": "text",
  "summary": "text",
  "content_markdown": "text",
  "status": "keyword",
  "embedding": { "type": "dense_vector", "dims": 1536, "index": true, "similarity": "cosine" }
}
```

查询：`bool.filter(category/domain) + hybrid(knn + match on title/summary)`。

**备选：Qdrant + MongoDB text index**

- 若团队 **不愿维护 ES**，可 Qdrant 管向量 + Mongo `$text` 管关键词，应用层做 hybrid 打分（见 §6.5 公式）
- 适合条目结构规范、import 时已拆好 `title/summary/prompt_tokens` 的场景

#### 不推荐作为长期主方案

- 仅 Redis 向量（无持久化与混合检索）
- 仅 Mongo 暴力向量（规模与延迟不可控）
- 一上来 Pinecone 等纯 SaaS（数据主权与成本不可控，除非明确上云战略）

#### 架构示意（推荐终态）

```text
Admin CRUD / Import
       ↓
 MongoDB drama_knowledge（权威）
       ↓ async sync (Celery/后台任务)
 Elasticsearch drama_knowledge_index
       ↓
 KnowledgeSearchService.search()
       ↓
 DramaOrchestrator → Skill prompt 注入
```

**配置项**（`config.py`）：

```python
knowledge_search_backend: Literal["mongo", "elasticsearch", "qdrant"] = "mongo"
elasticsearch_url: Optional[str] = None
embedding_model: str = "text-embedding-3-small"
embedding_dims: int = 1536
```

### 6.8 知识库运营化管理

#### Admin CRUD API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/drama/knowledge` | 列表（category/domain/tags/status） |
| POST | `/api/admin/drama/knowledge` | 手工新建条目 |
| GET/PUT | `/api/admin/drama/knowledge/{id}` | 详情 / 编辑（新版本） |
| POST | `/api/admin/drama/knowledge/{id}/publish` | 发布 → 触发索引 sync |
| DELETE | `/api/admin/drama/knowledge/{id}` | 软删 → 索引删除 |
| POST | `/api/admin/drama/knowledge/reindex` | 全量重建向量索引 |
| GET | `/api/admin/drama/knowledge/categories` | 类型列表（内置+自定义） |
| POST | `/api/admin/drama/knowledge/categories` | 扩展自定义 category |

#### 前端 `/admin/drama/knowledge`

- 左侧：category 树（短剧 / 电影 / 动漫 / AIGC / …）
- 列表：标题、domain、tags、来源（手工/导入）、状态
- 编辑：Markdown 正文 + 结构化字段表单
- 导入向导：上传 → 解析预览 → 批量发布
- 检索调试：输入 query 看 hybrid 命中与打分（便于运营调 tags）

#### 用户侧

- 对话中仅展示「本次引用 N 条知识」+ 标题列表，**不暴露** Admin 全文库

---

## 七、Tool 层

| Tool | 职责 |
|------|------|
| `memory_read` / `memory_write` | 结构化读写 Project / Character / Scene / Episode / Shot |
| `memory_confirm` | draft → confirmed/locked，写 confirmed_settings |
| `knowledge_search` | 按 domain/tags/语义检索知识库 |
| `style_resolve` | 解析项目风格 + modifier |
| `consistency_check` | 规则引擎 + LLM audit（人物/时间线/风格/分镜可执行性） |
| `format_convert` | 大纲→剧本、剧本→分镜、分镜→prompt_pack |
| `export_markdown` / `export_csv` | 分镜表导出 |
| `export_to_canvas` | 见 §九 |

---

## 八、核心数据结构

### 8.1 MongoDB 集合（新增）

| 集合 | 说明 |
|------|------|
| `drama_projects` | 项目元信息、stage、style_preset_id、canvas_project_id |
| `drama_characters` | 角色卡 + constraints + ref_image_asset_id |
| `drama_scenes` | 场景卡 + 环境/光色/道具 |
| `drama_episodes` | 集大纲 + script draft/confirmed |
| `drama_shots` | 分镜镜头 + prompt 字段 + canvas_node_ids |
| `drama_confirmed_settings` | 用户锁定设定（禁止改动项） |
| `drama_style_presets` | 风格库（StyleSpec v1 + reference_images） |
| `drama_knowledge` | 知识条目（权威正文 + embedding 元数据） |
| `drama_skills` | Skill 注册（code/markdown 双源 + 版本） |
| `drama_knowledge_import_jobs` | 文档导入任务 |
| `drama_agent_traces` | Agent 步骤（或复用 trace_logs 加 type=drama） |

**向量索引**（非 Mongo 集合，依后端而定）：ES index `drama_knowledge_index` 或 Qdrant collection `drama_knowledge`

### 8.2 Project（扩展）

```json
{
  "project_id": "drp_xxx",
  "title": "重生复仇：大婚之夜",
  "stage": "storyboard",
  "genre": "女频重生",
  "target_platform": "竖屏短剧",
  "episode_count": 20,
  "episode_duration_sec": 90,
  "style_preset_id": "ancient_revenge_cinematic_vertical",
  "style_modifiers": ["更爽", "更低成本AI"],
  "canvas_project_id": "cp_xxx",
  "session_id": "sess_xxx",
  "confirmed_settings": [],
  "forbidden_settings": []
}
```

### 8.3 Character / Scene / Shot

与昨日草案一致，**新增字段**：

**Character**：
- `style_tokens[]`：来自风格库
- `ref_images[]`：asset_id（画布或上传）
- `prompt_pack`：`face`, `costume`, `negative`
- `status`: `draft | confirmed | locked`

**Scene**：
- `location`, `time_of_day`, `interior_exterior`
- `color_palette[]`, `lighting`, `key_props[]`
- `prompt_pack`：`environment_en`, `negative`
- `status`

**Shot**：
- `shot_number`, `duration_sec`, `shot_size`, `camera_angle`, `camera_movement`
- `characters_in_frame[]`, `scene_id`
- `visual_description`, `action`, `dialogue`, `audio`
- `image_prompt`, `video_prompt`, `negative_prompt`
- `knowledge_refs[]`：引用了哪些 kb entry
- `canvas_nodes`：`{ text_node_id?, image_node_id?, video_node_id? }`
- `status`

### 8.4 输出双轨

每个 Skill 产出同时存：
1. **JSON**（机器可读，供校验 / 画布 / 导出）
2. **Markdown**（人类可读，对话展示）

Schema 文件建议：`backend/app/schemas/drama/*.json`

---

## 九、无限画布衔接（生产出口）

### 9.1 原则

- Agent **不自动**调用图/视频模型（MVP）
- 用户在本集分镜 **确认** 后，点击 **「推到画布」** 生成节点图
- 用户在画布内：调 prompt、换模型、跑 image/video、标记、下载

### 9.2 导出模板（每集一条生产链）

```text
[Episode 节点组]
  ├── resource（可选）角色参考图 / 场景 moodboard
  ├── text（剧本摘要节点，供 @ 引用）
  ├── 对每个 Shot（可配置「每镜一组」或「按场景合并」）：
  │     ├── text：镜头描述 + 对白（run 可扩写 prompt）
  │     ├── image：character/scene ref 连线 → image 节点
  │     │         config.prompt = shot.image_prompt
  │     └── video：image 主图连线 → video 节点
  │               config.prompt = shot.video_prompt
  │               config.duration = shot.duration_sec
  └── 节点 metadata：drama_shot_id, episode_id（回写用）
```

### 9.3 API（规划）

```http
POST /api/drama/projects/{id}/episodes/{ep_id}/export-canvas
Body: { "mode": "per_shot" | "per_scene", "include_script_text": true }
Response: { "canvas_project_id", "created_node_ids", "created_edge_ids" }
```

### 9.4 字段映射表

| drama_shots 字段 | canvas node config |
|------------------|-------------------|
| `image_prompt` | image/text → `params.prompt` |
| `video_prompt` | video → `params.prompt` |
| `negative_prompt` | `params.negative_prompt`（若模型 schema 支持） |
| `duration_sec` | video → `params.duration` |
| `characters[].ref_image` | resource 节点 → edge → image |
| `style.aspect_ratio` | video/image → `params.ratio` 或 size spec |

### 9.5 回写

- 画布 image/video run 成功后，可选 **回写** `drama_shots[].production_asset_id`
- Drama 项目资产树展示「已出片 / 待生成」状态

---

## 十、前端信息架构（DramaStudio）

```text
/drama                          项目列表
/drama/:projectId               项目工作台
  ├── Tab: 对话（默认）          阶段条 + Chat + Skill 快捷指令
  ├── Tab: 资产                  大纲 | 剧本 | 分镜 | 角色 | 场景
  ├── Tab: 风格                  当前 preset + modifier
  ├── Tab: 检查                  一致性报告
  └── Tab: 画布                  跳转 / 嵌入 canvas_project_id
```

**对话内快捷操作**：
- 「确认本集大纲」「锁定角色」「生成分镜」「应用风格：电影感竖屏」
- 「检查一致性」「推到画布」「导出 CSV」

---

## 十一、API 概要（`/api/drama`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/projects` | 列表/创建 |
| GET/PUT | `/projects/{id}` | 详情/更新 stage、风格 |
| POST | `/projects/{id}/chat` | 主入口：message → Orchestrator |
| GET | `/projects/{id}/memory` | 记忆快照（分类型） |
| POST | `/projects/{id}/confirm` | 确认 draft → confirmed |
| CRUD | `/projects/{id}/characters` | 角色卡 |
| CRUD | `/projects/{id}/scenes` | 场景卡 |
| CRUD | `/projects/{id}/episodes` | 集 + 剧本 |
| CRUD | `/projects/{id}/episodes/{eid}/shots` | 分镜 |
| POST | `/projects/{id}/consistency-check` | 触发审查 |
| POST | `/projects/{id}/episodes/{eid}/export-canvas` | 推到画布 |
| GET | `/styles` | 风格库列表 |
| GET | `/knowledge/search` | 内部/调试检索 |

Admin：

| 模块 | 路径 |
|------|------|
| Skill | `/api/admin/drama/skills` CRUD + publish + test + fork |
| 风格 | `/api/admin/drama/styles` CRUD + reverse-from-image + validate |
| 知识 | `/api/admin/drama/knowledge` CRUD + import + reindex + categories |

---

## 十二、MVP 迭代计划（建议 10 周）

### 迭代 1（2 周）：底座 + 运营口子

- 数据模型 + Project CRUD + `memory_confirm`
- **SkillRegistry 抽象** + code 源加载；Admin markdown Skill CRUD（draft/publish）
- **StyleSpec v1** Schema + Admin 模板创建；**内置 89 项风格种子**（§5.8，参考 liblib 风格库）
- **Knowledge** Mongo 存储 + text index 检索；category 树 + 手工 CRUD
- `skill.intake` / `skill.concept` + 对话页壳

### 迭代 2（2 周）：剧本链 + 导入

- `skill.outline` / `skill.script` / `skill.character`
- 知识库 **md/txt 导入向导**（按 category）
- 风格 **参考图反推**（Vision LLM → StyleSpec draft）

### 迭代 3（2 周）：场景 + 分镜

- `skill.scene` / `skill.storyboard` / `skill.action`
- 分镜表 UI（表格 + 镜头卡片）
- `skill.prompt_engineer` 出 image/video/negative 三包

### 迭代 4（2 周）：一致性 + 画布出口

- `skill.consistency` + 检查面板
- `export_to_canvas` + 字段映射
- drama_shots ↔ canvas 回写 asset 状态

### 迭代 5（2 周）：运营 polish + 向量检索上线

- Admin：Skill 试跑 / 风格 validate / 知识 reindex
- **Elasticsearch 8.x 接入**（或 Qdrant 备选）+ embedding 流水线 + hybrid 检索
- PDF import、知识检索调试面板
- Demo 项目模板（重生复仇全流程）

**MVP 仍不做**：Agent 内自动跑图/视频、多人协作、投放分析

---

## 十三、验收标准（MVP Demo）

用固定 Demo：**「重生复仇，大婚之夜开局，竖屏 20 集」**

1. 10 分钟内完成：Brief → 大纲前 3 集 → 第 1 集剧本 → 2 角色 + 2 场景卡
2. 分镜：第 1 集 12~18 镜，每镜含景别/运镜/时长/英文 video prompt
3. 一致性检查能发现故意植入的「人名不一致」
4. 一键推到画布：至少 3 个 shot 形成 text→image→video 链，手动 run 成功
5. Trace 可看到每次 Skill 名、知识 entry_id、风格 preset_id

---

## 十四、风险与对策

| 风险 | 对策 |
|------|------|
| 上下文过长 | 分阶段 memory slice；剧本按集注入 |
| 风格漂移 | 项目级 preset + locked_tokens + 一致性检查 |
| 分镜不可生成 | `ai_video` 知识域 + Shot 级 feasibility 字段 |
| Skill 输出 JSON 不稳定 | Schema 校验 + 重试 + 降级 Markdown 人工修复 |
| Skill markdown 与 code 分叉 | Fork 机制 + 版本 trace；合并策略文档化 |
| 风格反推不准 | 人工校对门禁 + `needs_review` + 试生成样例 |
| 导入文档噪音 | chunk 预览 + 批量 discard + LLM 结构化可选 |
| 向量引擎迁移 | `KnowledgeSearchBackend` 接口 + Mongo 权威 + 可 reindex |

---

## 十五、后续子文档

1. `docs/DRAMA_AGENT_STATE_MACHINE.md` — 状态机与 confirm 规则
2. `docs/DRAMA_KNOWLEDGE_SEED.md` — 知识库初始条目清单
3. `docs/DRAMA_STYLE_SPEC.md` — StyleSpec v1 JSON Schema + 反推 Prompt + **内置 89 风格 seed 清单**
4. `docs/DRAMA_CANVAS_EXPORT.md` — 画布节点模板与 config 映射
5. `docs/DRAMA_ADMIN_IA.md` — Skill/风格/知识 Admin 信息架构
6. `backend/app/schemas/drama/` — JSON Schema 文件

---

*文档版本 v0.3.1 | 2026-06-19 | cokey_ai 短剧 Agent 方案（含 liblib 风格库全量种子）*
