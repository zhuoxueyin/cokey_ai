# 厂商+模型调用协议规范

> 版本：v1.0  
> 日期：2026-06-17  
> 适用范围：cokey_ai 平台渠道适配器

---

## 一、厂商协议总览

| 厂商 | 渠道类型 | 支持模型 | 协议类型 | 主要接口 |
|------|----------|----------|----------|----------|
| **Weelink** | 聚合渠道 | GPT-4、GPT-Image-2、Claude | OpenAI 兼容 | `/v1/chat/completions` `/v1/images/generations` |
| **APIYi** | 聚合渠道 | GPT-4、GPT-Image-2 | OpenAI 兼容 | `/v1/chat/completions` `/v1/images/generations` |
| **火山引擎** | 直连渠道 | Seedancer（视频生成） | 火山引擎私有协议 | `/api/v3/contents/generations/tasks` |

---

## 二、Weelink 聚合渠道协议

### 2.1 基础配置

```json
{
  "channel_code": "weelink_text",
  "channel_name": "Weelink 文本渠道",
  "channel_type": "aggregator",
  "category": "text",
  "base_url": "https://api.weelink.ai",
  "auth_config": {
    "api_key": "sk-xxxxxxxxxxxx"
  },
  "api_config": {
    "text_path": "/v1/chat/completions",
    "image_path": "/v1/images/generations",
    "text_stream": true
  }
}
```

### 2.2 文本生成 `/v1/chat/completions`

**请求格式：**
```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "你是一个有帮助的助手"},
    {"role": "user", "content": [
      {"type": "text", "text": "描述图中的内容"},
      {"type": "image_url", "image_url": {"url": "https://cdn.example.com/img.png"}}
    ]}
  ],
  "temperature": 0.7,
  "max_tokens": 4096,
  "stream": true,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "seed": 12345,
  "stop": [],
  "user": "user_001"
}
```

**入参协议详解：**

| 参数 | 类型 | 必填 | 默认值 | 范围/枚举 | 说明 |
|------|------|------|--------|-----------|------|
| model | string | ✅ | - | - | 模型标识：`gpt-4`, `gpt-4-turbo`, `gpt-5.5`, `claude-3-sonnet`, `claude-3-opus` |
| messages | array | ✅ | - | - | 消息列表，每个元素为消息对象 |
| messages[].role | string | ✅ | - | `system`, `user`, `assistant`, `tool` | 消息角色 |
| messages[].content | string/array | ✅ | - | - | 消息内容，支持纯文本或多模态内容数组 |
| messages[].content[].type | string | ❌ | text | `text`, `image_url` | 内容类型 |
| messages[].content[].text | string | ❌ | - | - | 文本内容（当 type=text 时） |
| messages[].content[].image_url.url | string | ❌ | - | - | 图片 URL（当 type=image_url 时） |
| temperature | float | ❌ | 0.7 | 0~2 | 温度系数，越高越随机 |
| max_tokens | int | ❌ | 4096 | 1~16384 | 最大输出 token 数 |
| top_p | float | ❌ | 1.0 | 0~1 | 核采样概率阈值 |
| frequency_penalty | float | ❌ | 0.0 | -2~2 | 频率惩罚，降低重复token概率 |
| presence_penalty | float | ❌ | 0.0 | -2~2 | 出现惩罚，增加新主题概率 |
| stream | bool | ❌ | true | - | 是否流式响应 |
| seed | int | ❌ | - | - | 随机种子，相同种子产生相同输出 |
| stop | array | ❌ | [] | - | 停止词列表 |
| user | string | ❌ | - | - | 用户标识（风控/计费） |
| images | array | ❌ | [] | - | 简化的图片输入（兼容旧格式） |

**响应格式（流式）：**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion.chunk",
  "created": 1718612345,
  "model": "gpt-4",
  "choices": [{
    "index": 0,
    "delta": {"content": "你好！"},
    "finish_reason": null
  }]
}
```

### 2.3 图片生成 `/v1/images/generations`（GPT Image-2 规范）

**请求格式：**
```json
{
  "model": "gpt-image-2",
  "prompt": "将图1人物改成赛博朋克机甲，保留五官特征，霓虹灯光，雨夜城市背景",
  "negative_prompt": "模糊，变形，多手，畸形五官，低画质，文字，水印",
  "image": [
    "https://cdn.example.com/ref1.png",
    "https://cdn.example.com/ref2.png"
  ],
  "input_fidelity": 0.9,
  "n": 4,
  "size": "1536x1536",
  "aspect_ratio": "1:1",
  "quality": "high",
  "output_format": "png",
  "response_format": "url",
  "thinking": "high",
  "stream": false,
  "background": "auto",
  "user": "user_001",
  "seed": 123456
}
```

**入参协议详解：**

| 参数 | 类型 | 必填 | 默认值 | 范围/枚举 | 说明 |
|------|------|------|--------|-----------|------|
| model | string | ✅ | - | - | 固定值：`gpt-image-2` |
| prompt | string | ✅ | - | 最大32000字符 | 生成指令，可通过「图1/图2」指代参考图 |
| negative_prompt | string | ❌ | "" | - | 反向提示词，禁止出现的元素 |
| image | string[] | ❌ | [] | 1~16项 | 参考图数组，支持 HTTP URL 或 Base64 DataURL |
| images | string[] | ❌ | [] | 1~16项 | 兼容旧格式，与 image 等效 |
| input_fidelity | float | ❌ | 0.7 | 0~1 | 参考图保真度：人像建议 0.85~0.95，风格参考 0.4~0.6 |
| n | int | ❌ | 1 | 1~10 | 生成图片数量 |
| size | string/object | ❌ | auto | - | 尺寸：`auto`(跟随参考图) / `"1024x1024"` / `{"width":1920,"height":1080}` |
| width | int | ❌ | - | 16倍数 | 宽度（与height配合使用） |
| height | int | ❌ | - | 16倍数 | 高度（与width配合使用） |
| aspect_ratio | string | ❌ | auto | `auto`, `1:1`, `16:9`, `9:16`, `4:3`, `3:4` | 比例简写，覆盖 size |
| quality | string | ❌ | high | `low`, `medium`, `high` | 输出质量，高清输出选 high |
| output_format | string | ❌ | png | `png`, `jpeg`, `webp` | 输出图片格式 |
| response_format | string | ❌ | url | `url`, `b64_json` | 返回格式：URL 或 Base64 |
| thinking | string | ❌ | medium | `off`, `low`, `medium`, `high` | 推理深度，细节还原开 high |
| stream | bool | ❌ | false | - | 是否流式分片返回图片片段 |
| background | string | ❌ | auto | `auto`, `transparent`, `opaque` | 背景处理方式 |
| user | string | ❌ | - | - | 用户唯一标识，用于风控/计费统计 |
| seed | int | ❌ | - | - | 随机种子，固定种子产生相同输出 |

**响应格式：**
```json
{
  "created": 1718612345,
  "data": [
    {"url": "https://cdn.example.com/output1.png", "revised_prompt": "..."}
  ]
}
```

---

## 三、APIYi 聚合渠道协议

### 3.1 基础配置

```json
{
  "channel_code": "apiyi_text",
  "channel_name": "APIYi 文本渠道",
  "channel_type": "aggregator",
  "category": "text",
  "base_url": "https://api.apiyi.com",
  "auth_config": {
    "api_key": "sk-xxxxxxxxxxxx"
  },
  "api_config": {
    "text_path": "/v1/chat/completions",
    "image_path": "/v1/images/generations",
    "text_stream": true
  }
}
```

### 3.2 文本生成 `/v1/chat/completions`

**请求格式：**
```json
{
  "model": "gpt-4-turbo",
  "messages": [
    {"role": "system", "content": "你是一个有帮助的助手"},
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 8192,
  "top_p": 1.0,
  "stream": true,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "stop": [],
  "user": "user_001"
}
```

**入参协议详解：**

| 参数 | 类型 | 必填 | 默认值 | 范围/枚举 | 说明 |
|------|------|------|--------|-----------|------|
| model | string | ✅ | - | `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo` | 模型标识 |
| messages | array | ✅ | - | - | 消息列表 |
| messages[].role | string | ✅ | - | `system`, `user`, `assistant` | 消息角色 |
| messages[].content | string | ✅ | - | - | 消息内容（纯文本） |
| temperature | float | ❌ | 0.7 | 0~2 | 温度系数 |
| max_tokens | int | ❌ | 8192 | 1~16384 | 最大输出长度 |
| top_p | float | ❌ | 1.0 | 0~1 | 核采样概率阈值 |
| frequency_penalty | float | ❌ | 0.0 | -2~2 | 频率惩罚 |
| presence_penalty | float | ❌ | 0.0 | -2~2 | 出现惩罚 |
| stream | bool | ❌ | true | - | 流式响应 |
| stop | array | ❌ | [] | - | 停止词列表 |
| user | string | ❌ | - | - | 用户标识 |

### 3.3 图片生成 `/v1/images/generations`

**请求格式：**
```json
{
  "model": "dall-e-3",
  "prompt": "一只可爱的小猫在草地上玩耍，阳光明媚，卡通风格",
  "negative_prompt": "低质量，模糊，失真，文字，水印",
  "n": 4,
  "size": "1024x1024",
  "quality": "hd",
  "response_format": "url",
  "style": "natural"
}
```

**入参协议详解：**

| 参数 | 类型 | 必填 | 默认值 | 范围/枚举 | 说明 |
|------|------|------|--------|-----------|------|
| model | string | ✅ | - | `dall-e-3`, `dall-e-2` | 模型标识 |
| prompt | string | ✅ | - | 最大4000字符 | 生成指令 |
| negative_prompt | string | ❌ | "" | - | 反向提示词 |
| n | int | ❌ | 1 | 1~4 | 生成数量 |
| size | string | ❌ | 1024x1024 | `1024x1024`, `1792x1024`, `1024x1792` | 输出尺寸 |
| quality | string | ❌ | standard | `standard`, `hd` | 输出质量 |
| response_format | string | ❌ | url | `url`, `b64_json` | 返回格式 |
| style | string | ❌ | vivid | `vivid`, `natural` | 风格：生动/自然 |

---

## 四、火山引擎直连渠道协议（Seedancer 视频）

### 4.1 基础配置

```json
{
  "channel_code": "volcengine_video",
  "channel_name": "火山引擎视频渠道",
  "channel_type": "direct",
  "category": "video",
  "base_url": "https://ark.cn-beijing.volces.com",
  "auth_config": {
    "api_key": "ve-xxxxxxxxxxxx"
  },
  "api_config": {
    "video_path": "/api/v3/contents/generations/tasks",
    "text_stream": false
  },
  "retry_config": {
    "timeout": 120,
    "max_retries": 1,
    "poll_interval": 5,
    "max_poll_attempts": 240
  }
}
```

### 4.2 视频生成 `/api/v3/contents/generations/tasks`（异步模式）

**请求格式：**
```json
{
  "model": "seedancer",
  "content": [
    {"type": "text", "text": "一只可爱的小猫在草地上玩耍，阳光明媚，卡通风格动画"},
    {"type": "image_url", "image_url": {"url": "https://cdn.example.com/ref1.png"}},
    {"type": "image_url", "image_url": {"url": "https://cdn.example.com/ref2.png"}},
    {"type": "video_url", "video_url": {"url": "https://cdn.example.com/ref_video.mp4"}},
    {"type": "audio_url", "audio_url": {"url": "https://cdn.example.com/ref_audio.mp3"}}
  ],
  "generate_audio": true,
  "ratio": "16:9",
  "duration": 15,
  "watermark": false,
  "video_quality": "high",
  "style_preset": "animation",
  "motion_scale": 1.0,
  "loop": false,
  "user_prompt": "用户自定义提示词"
}
```

**入参协议详解：**

| 参数 | 类型 | 必填 | 默认值 | 范围/枚举 | 说明 |
|------|------|------|--------|-----------|------|
| model | string | ✅ | - | `seedancer` | 固定值：Seedancer 视频生成模型 |
| content | array | ✅ | - | 1~50项 | 内容列表，支持多种类型混合 |
| generate_audio | bool | ❌ | true | - | 是否自动生成背景音乐 |
| ratio | string | ❌ | adaptive | `adaptive`, `16:9`, `9:16`, `1:1`, `4:3`, `3:4` | 视频宽高比 |
| duration | int | ❌ | 5 | 3~30 | 视频时长（秒） |
| watermark | bool | ❌ | false | - | 是否添加平台水印 |
| video_quality | string | ❌ | medium | `low`, `medium`, `high`, `ultra` | 视频输出质量 |
| style_preset | string | ❌ | - | `animation`, `realistic`, `cartoon`, `cinematic`, `abstract` | 风格预设 |
| motion_scale | float | ❌ | 1.0 | 0~3 | 运动幅度缩放，越大动作越剧烈 |
| loop | bool | ❌ | false | - | 是否生成循环视频 |
| user_prompt | string | ❌ | - | 最大2000字符 | 用户自定义提示词（附加） |

**content 字段支持类型详解：**

| 类型 | 格式 | 最大数量 | 说明 |
|------|------|----------|------|
| text | `{"type": "text", "text": "..."}` | 1 | 文本提示词，描述视频内容 |
| image_url | `{"type": "image_url", "image_url": {"url": "..."}}` | 10 | 参考图片，用于风格参考或场景引导 |
| video_url | `{"type": "video_url", "video_url": {"url": "..."}}` | 3 | 参考视频，学习动作或场景 |
| audio_url | `{"type": "audio_url", "audio_url": {"url": "..."}}` | 1 | 参考音频，生成匹配的视频 |

**content 字段约束：**
- 必须至少包含一个 `text` 类型或一个 `image_url` 类型
- `text` 类型最多 1 个
- `image_url` 类型最多 10 个
- `video_url` 类型最多 3 个
- `audio_url` 类型最多 1 个
- 总内容项数不超过 50 个

**创建任务响应：**
```json
{
  "id": "task-xxx",
  "status": "queued",
  "created_at": "2026-06-17T10:00:00Z"
}
```

**查询任务状态 `/api/v3/contents/generations/tasks/{task_id}`：**

**进行中：**
```json
{
  "id": "task-xxx",
  "status": "running",
  "progress": 50
}
```

**成功：**
```json
{
  "id": "task-xxx",
  "status": "succeeded",
  "content": {
    "video_url": "https://volcengine-copilot.bytedance.net/xxx.mp4"
  },
  "duration": 11,
  "width": 1920,
  "height": 1080
}
```

**失败：**
```json
{
  "id": "task-xxx",
  "status": "failed",
  "error": {
    "code": "xxx",
    "message": "任务失败原因"
  }
}
```

---

## 五、协议适配原则

### 5.1 适配器职责

| 职责 | 说明 |
|------|------|
| 参数映射 | 统一平台参数 → 渠道专属参数 |
| 格式转换 | 参考图 URL 必须转为 CDN 地址 |
| 错误统一 | 渠道异常 → 平台统一错误码 |
| 结果归一 | 渠道返回 → 统一格式（text/image/video） |

### 5.2 错误码规范

| 错误码 | 含义 | 触发场景 |
|--------|------|----------|
| `success` | 成功 | 调用成功 |
| `channel_error` | 渠道错误 | API Key 无效、模型不存在 |
| `service_unavailable` | 服务不可用 | 429 限流、5xx 服务端错误 |
| `timeout` | 超时 | 请求超时 |
| `content_violation` | 内容违规 | 安全策略拦截 |
| `internal_error` | 内部错误 | 未知异常 |

### 5.3 重试策略

| 参数 | 默认值 | 说明 |
|------|--------|------|
| timeout | 60s（文本/图片）/ 120s（视频） | 请求超时时间 |
| max_retries | 1 | 最大重试次数 |
| retry_delay | 2s | 重试间隔 |
| poll_interval | 5s | 异步任务轮询间隔 |
| max_poll_attempts | 240（20分钟） | 最大轮询次数 |

---

## 六、调用链路

```
用户请求 → gateway_service.execute()
           → model_service.get_by_code(model_code)
           → 获取 channel_bindings
           → 选择最高优先级 active 渠道
           → channel_service.get_by_code(channel_code)
           → create_adapter(channel_config, trace_id)
           → adapter.get_api_key_for_category(category)
           → adapter.convert_params(model_config, params)
           → adapter.call_api()
           → adapter.parse_result()
           → 返回统一格式结果
```

---

## 七、渠道类型与适配器映射

| channel_type | channel_code 匹配 | 适配器 |
|--------------|-------------------|--------|
| `aggregator` | 任意 | `WeelinkingAdapter` |
| `direct` | 非 volcengine | `WeelinkingAdapter` |
| `direct` | volcengine* | `VolcengineAdapter` |
| `weelinking` | 任意 | `WeelinkingAdapter` |
| `volcengine` | 任意 | `VolcengineAdapter` |

> **说明**：channel_code 匹配优先级高于 channel_type。如果 channel_code 包含 "volcengine"，即使 channel_type 为其他值，也会使用 `VolcengineAdapter`。

---

## 八、新增渠道接入指南

### 8.1 步骤

1. **创建适配器类**：继承 `BaseChannelAdapter`，实现以下方法：
   - `convert_params()`: 参数转换
   - `call_api()`: API 调用
   - `parse_result()`: 结果解析
   - `parse_error()`: 错误处理

2. **注册适配器**：在 `adapters/__init__.py` 中注册

3. **配置渠道**：在数据库 `channels` 集合中添加记录

4. **配置模型绑定**：在数据库 `models` 集合中添加 `channel_bindings`

### 8.2 适配器模板

```python
class NewChannelAdapter(BaseChannelAdapter):
    def __init__(self, channel_config, trace_id):
        super().__init__(channel_config, trace_id)
        # 自定义初始化
    
    async def convert_params(self, model_config, params):
        # 参数转换逻辑
        return channel_params
    
    async def call_api(self, category, channel_params, channel_model_id, api_key):
        # API 调用逻辑
        return raw_result
    
    async def parse_result(self, category, raw_result):
        # 结果解析逻辑
        return unified_result
    
    def parse_error(self, exception):
        # 错误处理逻辑
        return error_code, error_message
```

---

## 九、参考图处理规范

### 9.1 格式支持

| 格式 | 支持 | 说明 |
|------|------|------|
| HTTP URL | ✅ | 必须是 CDN 地址 |
| Base64 DataURL | ✅ | 会自动上传到 CDN |
| blob: URL | ❌ | 需要先上传 |

### 9.2 图片限制

| 限制项 | 值 |
|--------|------|
| 单次最大数量 | 16 张 |
| 单图最大大小（Base64） | 20MB |
| 单图最大大小（文件上传） | 50MB |
| 分辨率要求 | 宽高均为 16 的倍数 |
| 长边最大 | 3840 |
| 总像素范围 | 655360 ~ 8294400 |
| 长宽比限制 | ≤3:1 |

---

## 十、CDN URL 规范

### 10.1 支持的 CDN 前缀

| CDN | 前缀 |
|-----|------|
| jsDelivr | `https://cdn.jsdelivr.net/gh/` |
| Fastly jsDelivr | `https://fastly.jsdelivr.net/gh/` |
| jsdmirror | `https://cdn.jsdmirror.com/gh/` |
| ghproxy | `https://ghproxy.net/https://raw.githubusercontent.com/` |
| GitHub Raw | `https://raw.githubusercontent.com/` |

### 10.2 URL 转换流程

```
原始 URL → is_cdn_url() 检查
           ├─ 是 CDN → 直接使用
           └─ 不是 CDN → 上传到 GitHub → 获取 CDN URL
```
