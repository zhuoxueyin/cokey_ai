# 新模型 / 渠道 / 协议 接入 SOP

> **产品入口**：管理后台 → **系统管理 → 接入工单**（`/admin/onboarding`）  
> 按步骤填写带 `*` 的必填项，右侧「必填项检查」实时提示遗漏；完成后 **复制发给 AI** 即可落库配置。  
> **离线用法**：亦可复制下方 Markdown 模板手动填写。

> **配套能力**：`InvocationMode`（任务模式）→ `ProtocolProfile`（协议画像）→ `ChannelBinding.mode_profiles`（模型绑定）→ 网关 `resolve_route`。

---

## 必填项一览（产品表单已内置校验）

| 步骤 | 必填字段 | 说明 |
|------|----------|------|
| 概述 | 工单标题 | 简要描述本次接入 |
| 产品模型 | model_code、model_name、category | 对用户暴露的模型 |
| 任务模式 | supported_modes（≥1） | 生文/文生图/图生图/文生视频/图生视频 |
| 渠道 | channel_code；新建时 + channel_name、channel_provider、base_url | 复用或新建 |
| 绑定与协议 | 每条绑定：channel_code、channel_model_id、priority；每个已选 mode 的 profile_id | 可引用内置画像 |
| 官方文档 | official_curl、成功响应 JSON | **仅自定义协议画像时必填** |
| 导出 | 全部必填通过后 | 复制 Markdown 发给 AI |

---

## 管理后台分工（新链路）

| 页面 | 职责 | 日常必配项 |
|------|------|------------|
| **接入工单** | 新模型/渠道一次性接入 | 全量工单 → 导出给 AI |
| **渠道管理** | 基础设施 | base_url、api_key、endpoints（protocol_slot + path） |
| **协议画像** | 路由契约（只读查阅为主） | 内置画像一般无需改；复杂协议走工单 |
| **模型管理** | 产品层 | 模型信息、channel_bindings、**mode_profiles**、降级策略 |

---

| 层级 | 字段 | 含义 | 谁填 |
|------|------|------|------|
| 任务模式 | `invocation_mode` | `text_chat` / `text_to_image` / `image_to_image` / `text_to_video` / `image_to_video` | 系统自动识别，可手动覆盖 |
| 协议槽位 | `protocol_slot` | 协议契约名，如 `openai.images.generations` | 协议画像 |
| 端点兼容键 | `endpoint_type` | 渠道 `endpoints[].type`：`chat`/`image`/`image_edits`/`video`… | 协议画像 |
| 协议画像 | `profile_id` | 全局唯一，如 `apiyi.gpt-image-2-vip.text_to_image` | 协议库 |
| 渠道模型 ID | `channel_model_id` | 渠道侧模型名，可与产品 `model_code` 不同 | 模型绑定 |

**路由优先级**：`binding.mode_profiles[mode]` → `binding.protocol_profile_id` → 内置 model_id 推断 → legacy 兜底。

---

## 二、接入工单模板（复制填写）

```markdown
## 接入工单

### 0. 元信息
- 工单标题：（例：接入 Banana 文生图 @ APIYI）
- 优先级：P0 / P1 / P2
- 期望上线：
- 负责人：

---

### 1. 产品模型（对用户暴露）

| 项 | 值 |
|----|-----|
| model_code | （例：banana-image-1） |
| model_name | （显示名） |
| category | text / image / video |
| description | |
| tags | |
| supported_inputs.image | true / false |
| supported_inputs.video | true / false |
| allow_channel_fallback | true / false（主渠道失败是否降级） |
| sort_order | 数字 |
| status | online / offline |

#### 前端参数 schema（param_schema.fields）
| name | label | field_type | required | default | options/min/max | 说明 |
|------|-------|------------|----------|---------|-----------------|------|
| prompt | 提示词 | textarea | true | | | |
| size | 画幅 | select | false | auto | 见尺寸表 | |
| aspect_ratio | 比例 | select | false | | | |
| resolution | 清晰度 | select | false | 2k | 1k/2k/4k | |

#### 尺寸/画幅表（如有）
| 平台 size 或 aspect_ratio+resolution | 渠道 API 字段值 | 备注 |
|--------------------------------------|-----------------|------|
| 16:9 + 2k | 1280x720 | |

---

### 2. 任务模式矩阵（必填）

勾选本产品需要支持的模式，并说明识别方式：

| invocation_mode | 需要 | 自动识别条件 | 手动覆盖字段 |
|-----------------|------|--------------|--------------|
| text_chat | ☐ | category=text | params.invocation_mode |
| text_to_image | ☐ | image 且无参考图 | |
| image_to_image | ☐ | image 且有 images/image | |
| text_to_video | ☐ | video 且无参考 | |
| image_to_video | ☐ | video 且有参考图/视频 | |

---

### 3. 渠道（基础设施）

#### 3.1 新建 or 复用
- [ ] 复用已有渠道：channel_code = ___________
- [ ] 新建渠道（填下表）

| 项 | 值 |
|----|-----|
| channel_code | |
| channel_name | |
| channel_type | aggregator / direct |
| channel_provider | apiyi / weelinking / volcengine / （其它） |
| base_url | https://... |
| api_key | （密钥管理方式：环境变量名 / 直接提供） |
| status | active |

#### 3.2 渠道 HTTP 端点（endpoints[]）

每个 **protocol_slot** 至少一条（path 相对 base_url）：

| protocol_slot | type(兼容) | endpoint(path) | method | content_type |
|---------------|------------|----------------|--------|--------------|
| openai.chat.completions | chat | chat/completions | POST | application/json |
| openai.images.generations | image | images/generations | POST | application/json |
| openai.images.edits | image_edits | images/edits | POST | multipart/form-data |
| openai.chat.image.text_to_image | chat | chat/completions | POST | application/json |
| openai.chat.image.image_to_image | chat | chat/completions | POST | application/json |
| volcengine.video.multimodal | video | contents/generations/tasks | POST | application/json |

#### 3.2.1 Body 入参（endpoints[].body_params）— 何时填、怎么填

**默认原则：有协议画像 `builder` 的槽位 → `body_params` 留空**（火山视频、APIYI 对话式生图等由适配器构建）。仅当渠道需纯 ConfigEngine 驱动时才配置。

每条入参 **三列语义固定**，不再混用 `value` 列：

| 列 | 字段 | 含义 |
|----|------|------|
| API 字段 | `key` | 写入 HTTP body 的字段名，如 `model`、`prompt`、`content` |
| 取值来源 | `source` | 见下表 |
| 来源配置 | `literal` / `param` / `builtin` | **只填与 source 对应的那一列** |

**取值来源（source）**

| source | 来源配置填什么 | 示例 |
|--------|----------------|------|
| `literal` | `literal` = 固定字面量（可 JSON） | `stream` ← `false` |
| `task_param` | `param` = 任务参数字段名（留空=与 key 同名） | `prompt` ← `prompt`；`generate_audio` ← `audio` |
| `builtin` | `builtin` = `channel_model_id` / `channel_code` / `trace_id` | `model` ← 绑定 ep-xxx |
| `image_urls` | `param` = 图片列表字段（默认 `images`） | CDN URL 列表 |
| `chat_messages` | 无需配置 | 由 `prompt` + `images` 组装 OpenAI messages |

**常见错误（勿再犯）**

- curl 示例里的 JSON 字面量标成 `task_param` → 会去 `params` 里找同名字段，结果 body 为空
- 全选 dynamic 却把示例值写在 `value` 里 → 应改为 `literal` + 字面量，或 `task_param` + 正确字段名

**按 protocol_slot 推荐**

| protocol_slot | body_params |
|---------------|-------------|
| volcengine.video.multimodal | **留空**（推荐） |
| openai.chat.image.* | **留空**（apiyi_chat_image builder） |
| openai.chat.completions | 模板：model→builtin；messages→chat_messages |
| openai.images.generations | 模板：model→builtin；prompt/size→task_param |

渠道管理端点高级区可点 **「套用入参模板」** 自动填充；curl 导入会把示例值标为 `literal`。

#### 3.3 超时与重试
| timeout_sec | max_retries | retry_delay |
|-------------|-------------|-------------|
| 300 | 1 | 2 |

---

### 4. 协议画像（每个 mode × 渠道模型 一条）

> profile_id 命名建议：`{provider}.{channel_model_id}.{invocation_mode}`  
> 例：`apiyi.gpt-image-2-vip.text_to_image`

#### 画像 A
| 项 | 值 |
|----|-----|
| profile_id | |
| name | |
| provider | apiyi / weelinking / volcengine / * |
| invocation_mode | |
| protocol_slot | |
| endpoint_type | chat / image / image_edits / video / video_image |
| http.path | |
| http.method | POST |
| http.content_type | application/json 或 multipart/form-data |
| request.builder | apiyi_chat_image / apiyi_vip_generations / weelink_default / config_engine / （新插件名） |
| request.size_strategy | api_field / prompt_hint / none |
| request.forbidden_fields | 例：quality, n, aspect_ratio |
| response.parser | openai_images / markdown_image / weelink_default / config_engine |

#### 官方请求示例（curl 或 JSON）
```bash
# 粘贴官方文档 curl
```

#### 官方响应示例（成功 / 失败各一份）
```json
{}
```

#### 参数映射说明
| 平台字段 | 渠道字段 | 转换规则 |
|----------|----------|----------|
| prompt | prompt | sanitize_prompt |
| size | size | vip_size_map / prompt_size_hint |
| images[0] | image | cdn_only, multipart |

（画像 B、C… 按 mode 复制本节）

---

### 5. 模型绑定（channel_bindings）

按 priority **降序**尝试（数字越大越优先）：

#### 绑定 1（主）
| 项 | 值 |
|----|-----|
| channel_code | |
| channel_model_id | （渠道侧模型名） |
| priority | 20 |
| status | active |
| supported_modes | text_to_image, image_to_image（逗号分隔） |
| fallback | true / false / 留空沿用模型级 |

**mode_profiles 映射：**
| invocation_mode | profile_id |
|-----------------|------------|
| text_to_image | |
| image_to_image | |

#### 绑定 2（备）
（同上，priority 更低）

---

### 6. 限制与异常

| 项 | 说明 |
|----|------|
| 参考图要求 | 必须 CDN URL / 支持 base64 / 不支持 |
| 最大参考图数量 | |
| 不支持的参数 | 例：quality, n |
| 画幅不支持像素 size | 是 → 写入 prompt |
| 异步任务 | 是 / 否；轮询间隔；完成字段路径 |
| 错误码对照 | 渠道 code → 用户提示 |

---

### 7. 验收

- [ ] 文生图（无参考图）成功，产物 URL 可访问
- [ ] 图生图（有参考图）成功
- [ ] 链路日志含：invocation_mode、profile_id、protocol_slot、endpoint_type
- [ ] 任务详情 channel_request 在 HTTP 发出前已写入
- [ ] 主渠道失败时降级行为符合 allow_channel_fallback
- [ ] 管理端模型卡片参数与线上一致

#### 测试用例
| 用例 | model_code | params | 期望 profile_id | 期望 endpoint |
|------|------------|--------|-----------------|---------------|
| 1 | | `{"prompt":"..."}` | | |
| 2 | | `{"prompt":"...","images":["https://cdn/..."]}` | | |
```

---

## 三、内置 request.builder / response.parser 一览

接入时**优先复用**，只有协议确实特殊才申请新插件。

| builder | 适用场景 |
|---------|----------|
| `apiyi_chat_image` | APIYI gpt-image-2-all 对话式生图/改图 |
| `apiyi_vip_generations` | APIYI gpt-image-2-vip `/images/generations` |
| `weelink_default` | Weelinking OpenAI 兼容默认逻辑 |
| `config_engine` | 完全由渠道 endpoints[].body_params 驱动 |

| parser | 适用场景 |
|--------|----------|
| `markdown_image` | Chat 回复 Markdown `![...](url)` 取图 |
| `openai_images` | `data[].url` / `data[].b64_json` |
| `weelink_default` | Weelinking 适配器默认解析 |
| `config_engine` | endpoints 响应映射配置 |

| size_strategy | 含义 |
|---------------|------|
| `api_field` | size 写入请求体字段（VIP 30 档映射） |
| `prompt_hint` | 画幅写入 prompt（all 模式） |
| `none` | 不传尺寸 |

---

## 四、内置协议画像（可引用，不必重复建）

| profile_id | provider | mode | protocol_slot | endpoint_type |
|------------|----------|------|---------------|---------------|
| apiyi.gpt-image-2-all.text_to_image | apiyi | text_to_image | openai.chat.image.text_to_image | chat |
| apiyi.gpt-image-2-all.image_to_image | apiyi | image_to_image | openai.chat.image.image_to_image | chat |
| apiyi.gpt-image-2-vip.text_to_image | apiyi | text_to_image | openai.chat.image.text_to_image | chat |
| apiyi.gpt-image-2-vip.image_to_image | apiyi | image_to_image | openai.chat.image.image_to_image | chat |
| apiyi.gpt-image-2-vip.generations.text_to_image | apiyi | text_to_image | openai.images.generations | image |
| apiyi.gpt-image-2-vip.edits.image_to_image | apiyi | image_to_image | openai.images.edits | image_edits |
| weelinking.openai-image.text_to_image | weelinking | text_to_image | openai.images.generations | image |
| weelinking.openai-image.image_to_image | weelinking | image_to_image | openai.images.edits | image_edits |
| openai.chat.text_chat | * | text_chat | openai.chat.completions | chat |
| volcengine.video.text_to_video | volcengine | text_to_video | volcengine.video.multimodal | video |
| volcengine.video.image_to_video | volcengine | image_to_video | volcengine.video.multimodal | video |

查询 API：`GET /api/admin/protocol-profiles`

---

## 五、我收到工单后的执行清单

1. **校验**：mode 矩阵与 profile 是否一一对应；endpoints 是否覆盖所有 `protocol_slot`
2. **写协议画像**：`POST /api/admin/protocol-profiles`（或 upsert 内置覆盖）
3. **写/改渠道**：`PUT /api/admin/channels/{id}`，补全 endpoints + protocol_slot
4. **写/改模型**：`PUT /api/admin/models/{id}`，配置 channel_bindings.mode_profiles
5. **冒烟**：按工单 §7 用例走 `/api/tasks/generate`，查 trace_logs
6. **回报**：贴 trace_id、实际 profile_id、HTTP path、产物 URL

---

## 六、常见场景速查

### 6.1 同一产品模型，APIYI VIP 主 + Weelinking 备
```json
"channel_bindings": [
  {
    "channel_code": "apiyi_main",
    "channel_model_id": "gpt-image-2-vip",
    "priority": 20,
    "mode_profiles": {
      "text_to_image": "apiyi.gpt-image-2-vip.text_to_image",
      "image_to_image": "apiyi.gpt-image-2-vip.image_to_image"
    }
  },
  {
    "channel_code": "weelink_backup",
    "channel_model_id": "gpt-image-2",
    "priority": 10,
    "mode_profiles": {
      "text_to_image": "weelinking.openai-image.text_to_image",
      "image_to_image": "weelinking.openai-image.image_to_image"
    }
  }
]
```

### 6.2 只走 VIP、禁止降级
- 模型：`allow_channel_fallback: false`
- 或仅保留 priority 最高的一条 binding

### 6.3 新聚合商（协议同 OpenAI images）
1. 新建渠道 `channel_provider: new_agg`
2. 复用 `weelinking.openai-image.*` 画像，改 `provider` 或复制画像改 path
3. binding 指向新 profile_id

### 6.4 全新协议（需新 builder）
工单 §4 必须提供：**完整 curl + 成功响应 JSON + 字段映射表**；我会评估是 `config_engine` 可配还是加 `request.builder` 插件。

---

## 七、API 索引

| 操作 | 方法 | 路径 |
|------|------|------|
| 协议画像列表 | GET | `/api/admin/protocol-profiles` |
| 按 profile_id 查 | GET | `/api/admin/protocol-profiles/by-id/{profile_id}` |
| 创建画像 | POST | `/api/admin/protocol-profiles` |
| 更新画像 | PUT | `/api/admin/protocol-profiles/{id}` |
| 种子内置画像 | POST | `/api/admin/protocol-profiles/seed-builtin` |
| 渠道 CRUD | * | `/api/admin/channels` |
| 模型 CRUD | * | `/api/admin/models` |
| 链路日志 | GET | `/api/admin/trace-logs` |

---

## 八、版本

- SOP 版本：1.0
- 对应后端：InvocationMode + ProtocolProfile + resolve_route（2026-06）
- 维护：架构变更时同步更新 §三内置表与 §四画像列表
