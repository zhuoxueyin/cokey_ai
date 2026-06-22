# 创意超级智能体（Super Creative Agent）设计 v1.0

> 替代原「DramaOrchestrator 占位方案」；**保留** Skill 库、知识库、风格库与无限画布生产出口。  
> 技术栈：**LangChain**（Prompt / Tool / Memory / Runnable）+ 平台 **ModelGateway**（大文本模型）+ MongoDB（线程记忆）。

---

## 一、定位

**平台内嵌超级智能体**：以对话驱动「创意脑暴 → 剧本 → 分镜 → 角色 → 场景」，具备**线程级持续记忆**；结构化产出确认后可推到**固定/项目画布**做图视频。

| 保留 | 重做 |
|------|------|
| Skill / 知识库 / 风格库 Admin | Agent 编排（LangChain） |
| tasks / ModelGateway / CDN | 原 MVP Orchestrator 占位回复 |
| 画布 run 生产 | DramaProjectHome 旧 UI |

---

## 二、入口与布局

### 2.1 主入口：左侧「短剧创作」→ `/drama`

**未开始对话（参考 liblib 起始页）**

```
┌─────────────────────────────────────────────┐
│        有什么新的故事灵感？                    │
│  ┌───────────────────────────────────────┐  │
│  │ [上传剧本]                             │  │
│  │ 短剧漫剧 / 输入灵感…                    │  │
│  │ 📎 🧊 @ 🎨  [模型▼]  [多剧集]     ⬆   │  │
│  └───────────────────────────────────────┘  │
│  [创意短剧] [AIGC漫剧] [MV] [营销广告]        │
└─────────────────────────────────────────────┘
```

- **模型**：平台 `category=text` 在线模型（Composer 同源 `getModels('text')`）
- **风格**：风格库 picker（`style_preset_id`）
- **@ 资源**：资产库 / 画布节点 / 已确认角色卡（MVP：资产 URL）
- **快捷模式**：切换 `agent_mode` + 默认 Skill 链

**对话中**：左侧阶段条 + 中间消息流 + 底部 Composer（同组件，可折叠为紧凑条）

### 2.2 画布入口：右下角 FAB → 右侧 Agent 面板

- FAB 固定于画布 workspace 右下
- 点击展开 **右侧面板**（非 Modal）
- **宽度可拖拽**调节（280–560px，`localStorage: drama_agent_panel_width`）
- **收起/展开**；与画布并行操作
- 绑定 `canvas_project_id` + 可选 `thread_id`（同用户可复用线程）

---

## 三、LangChain Agent 架构

```text
用户消息 + 线程配置(mode/model/style/@refs)
  → SuperCreativeAgent (LangChain Runnable)
       ├─ ThreadMemoryLoader（Mongo 最近 N 轮 + 项目 confirmed 快照）
       ├─ ModeRouter（创意短剧 / 漫剧 / MV / 广告 → stage 权重）
       ├─ ToolSelector
       │    ├─ search_knowledge（知识库 hybrid）
       │    ├─ resolve_style（风格库 StyleSpec）
       │    ├─ invoke_skill（Skill Registry markdown/code）
       │    ├─ read_project_memory / write_project_memory
       │    ├─ list_assets（@ 资源解析）
       │    └─ export_to_canvas（后续：推分镜/角色到画布）
       ├─ GatewayChatModel → ModelGateway.execute(category=text)
       └─ ResponseParser（Markdown + 可选 JSON block）
  → 持久化 assistant 消息 + trace 步骤
```

### 3.1 与 Skill / 知识库 / 风格库关系

| 能力层 | Agent 用法 |
|--------|-----------|
| **Skill** | `invoke_skill(skill_code, inputs)` 加载 published Skill 模板，注入 memory/style/knowledge 后调 LLM |
| **知识库** | 每轮按 mode+stage 自动 `search_knowledge` + Tool 可再检索 |
| **风格库** | 线程级 `style_preset_id`；`resolve_style` 注入 `model_prompts` |
| **画布** | 生产阶段 Tool `export_to_canvas`；平时 thread 可挂 `canvas_project_id` |

### 3.2 持续上下文记忆（三层）

| 层 | 存储 | 内容 |
|----|------|------|
| **线程对话** | `drama_agent_messages` | user/assistant/tool 消息，窗口 30 轮 |
| **项目结构化** | `drama_projects` + characters/scenes/episodes | confirmed 设定 |
| **KV 快取** | `kv_store` namespace `drama_agent` | 线程摘要 summary（可选压缩） |

---

## 四、快捷模式（agent_mode）

| mode | 名称 | 默认阶段侧重 | 知识 category 偏向 |
|------|------|--------------|---------------------|
| `creative_short_drama` | 创意短剧 | 脑暴→剧本→分镜 | short_drama, film |
| `aigc_manga` | AIGC漫剧 | 分镜→角色→场景 | anime, aigc |
| `mv` | MV | 创意→分镜→场景 | film, sound |
| `marketing_ad` | 营销广告 | 脑暴→脚本→分镜 | short_drama, platform |

---

## 五、API（`/api/drama/agent`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/threads` | 创建线程（project_id/mode/model/style/canvas_id） |
| GET | `/threads/{id}` | 线程详情 |
| GET | `/threads/{id}/messages` | 历史消息 |
| POST | `/threads/{id}/chat` | 发送消息（body: message, refs[]） |
| POST | `/threads/{id}/compact` | 压缩摘要（后续） |

兼容：原 `POST /drama/projects/{id}/chat` 可转发到 agent thread。

---

## 六、数据模型

### drama_agent_threads

```json
{
  "thread_id": "dat_xxx",
  "project_id": "drp_xxx",
  "user_id": "u1",
  "canvas_project_id": "proj_xxx",
  "agent_mode": "creative_short_drama",
  "model_code": "xxx",
  "style_preset_id": "retro_sci_fi_atompunk",
  "multi_episode": false,
  "stage": "concept",
  "title": "未命名创作",
  "status": "active"
}
```

### drama_agent_messages

```json
{
  "message_id": "msg_xxx",
  "thread_id": "dat_xxx",
  "role": "user|assistant|tool|system",
  "content": "…",
  "refs": [],
  "meta": { "skill_code": "", "knowledge_refs": [], "stage": "" }
}
```

---

## 七、实施分期

| 迭代 | 交付 |
|------|------|
| **A（当前）** | 设计文档 + 起始页 UI + 画布侧栏 + LangChain 骨架 + 线程/chat API + Gateway LLM |
| B | @ 资源 picker、上传剧本、多剧集、JSON 结构化产出 |
| C | export_to_canvas、角色/场景/分镜 CRUD 与 confirm 流 |
| D | LangGraph 阶段状态机、摘要压缩、trace 可视化 |

---

## 八、依赖

```text
langchain-core>=0.3.19
langchain>=0.3.19
```

LLM 不直连 OpenAI，经 `GatewayChatModel` 走平台渠道。

---

*文档版本 v1.0 | 2026-06-20*
