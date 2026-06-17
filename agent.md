# AIGC 创作平台 - 技术方案与运维手册

> 版本: v1.1.0 | 最后更新: 2026-06-17（以代码为基准同步）
> 通用 AIGC 创作平台 - 支持多模型、多渠道的 AI 内容生成系统
> 关联文档: `README.md`（快速开始）、`PROTOCOL_SPEC.md`（渠道协议规范）

---

## 一、项目概述

### 1.1 系统定位

通用 AIGC 创作平台是一个支持多模型、多渠道的 AI 内容生成系统，提供统一的前端界面和后端 API 网关，将不同 AI 服务提供商的能力抽象为一致的调用接口。

### 1.2 核心功能

| 功能模块 | 说明 | 主要代码 |
|---------|------|---------|
| 文本生成 | 大语言模型对话/创作，支持多模态图片输入 | `WeelinkingAdapter._call_text_api` |
| 图像生成 | 文生图 / 图生图（gpt-image-2 等），参考图 CDN 全链路 | `ComposerArea` → `gateway` → `image_edits` |
| 视频生成 | 文生视频 / 图生视频，火山引擎异步轮询 | `VolcengineAdapter._call_video_async` |
| 创作工作台 | 对话式任务流、会话管理、乐观 UI | `Workspace` + `ChatArea` + `ComposerArea` |
| 资源管理 | 上传/生成资源入库，GitHub + jsDelivr CDN | `storage_service` + `assets` |
| Prompt 管理 | 版本化 Prompt 模板，发布/回滚 | `prompt_service` + `PromptManager` |
| 模型管理 | 模型 CRUD、`param_schema`、渠道绑定 | `ModelAdmin` + `model_service` |
| 渠道管理 | 多渠道配置、`endpoints` + `body_params`、cURL 导入 | `ChannelAdmin` + `config_engine` |
| 任务管理 | 任务监控、渠道请求/响应追溯、`trace_id` | `TaskAdmin` + `task_service` |
| 用户认证 | JWT 注册/登录，路由守卫 | `auth.py` + `Login.tsx` |
| 文件上传 | 图片/文件上传至 GitHub CDN | `user_upload` + `cdnUrl.ts` |

### 1.3 技术栈总览

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (Web UI)                       │
│  React 18 + TypeScript + Ant Design + Zustand + Vite    │
│                运行端口: http://localhost:3001           │
└─────────────────────────────┬───────────────────────────┘
                              │ HTTP / JSON
                              ▼
┌─────────────────────────────────────────────────────────┐
│                     后端 (API Server)                   │
│    FastAPI + Python 3.11 + Motor(MongoDB) + Loguru      │
│                运行端口: http://localhost:8000           │
└─────────────────────────────┬───────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
     ┌──────────┐       ┌──────────┐       ┌──────────────────┐
     │  MongoDB │       │  Redis   │       │ Weelink / 火山等  │
     │ (必需)   │       │ (可选)   │       │ 外部 AI API      │
     └──────────┘       └──────────┘       └──────────────────┘
                              │
                     ┌────────┴────────┐
                     │ GitHub + CDN    │
                     │ (参考图/资源)    │
                     └─────────────────┘
```

### 1.4 系统架构总览（以代码为准）

#### 1.4.1 分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│ 前端 React 18 + Zustand + Ant Design (localhost:3001)            │
│  Workspace / ComposerArea / ChatArea / 管理后台页面               │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP JSON (/api → Vite proxy → 8000)
┌────────────────────────────▼────────────────────────────────────┐
│ Router 层 (backend/app/routers/)                                 │
│  user_tasks / user_models / user_upload / assets / auth / admin* │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ Service 层 (backend/app/services/)                               │
│  task_service / model_service / channel_service / session_service│
│  asset_service / storage_service / auth_service / prompt_service │
│  gateway_service (ModelGateway) ← 核心路由与故障切换              │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ Adapter 层 (backend/app/adapters/)                                 │
│  BaseChannelAdapter.execute() → convert_params → call_api        │
│  WeelinkingAdapter (OpenAI 兼容) | VolcengineAdapter (直连)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ Core 基础设施 (backend/app/core/)                                │
│  config / database / config_engine / cdn / security / middleware │
└─────────────────────────────────────────────────────────────────┘
```

#### 1.4.2 生成任务全链路

```
用户输入 (ComposerArea)
  → 上传参考图 → POST /api/assets/upload → GitHubStorageService → CDN URL
  → pickCdnUrl / extractCdnUrls 校验 (frontend/src/utils/cdnUrl.ts)
  → POST /api/tasks/generate
       → validate_reference_images (backend/app/core/cdn.py)
       → TaskService.create + update_status(processing)
       → ModelGateway.execute
            → param_schema 校验
            → _select_channel (priority 降序)
            → _determine_endpoint_type (chat/image/image_edits/video/...)
            → create_adapter → adapter.execute(endpoint_type)
            → 失败时 _try_fallback_channels
       → TaskService.update_status(success/failed)
       → 生成图/视频写入 assets（可选）
  → 前端替换 tempTask，ChatArea 展示结果
```

#### 1.4.3 端点自动路由规则（Gateway）

**文件**: `backend/app/services/gateway_service.py` → `_determine_endpoint_type`

| 优先级 | 条件 | 端点类型 |
|--------|------|---------|
| 1 | 渠道 `endpoints` 含 `type=chat` | `chat`（所有任务优先） |
| 2 | category=image 且无参考图 | `image`（文生图） |
| 3 | category=image 且有 `image`/`images` | `image_edits`（图生图） |
| 4 | category=video 且无参考图 | `video` |
| 5 | category=video 且有参考图 | `video_image` |
| 6 | 其他 | 等同 category |

#### 1.4.4 适配器注册规则

**文件**: `backend/app/adapters/__init__.py` → `create_adapter`

| 匹配优先级 | 条件 | 适配器 |
|-----------|------|--------|
| 1 | `channel_provider=weelinking` | WeelinkingAdapter |
| 2 | `channel_provider=apiyi` | WeelinkingAdapter |
| 3 | `channel_provider=volcengine` | VolcengineAdapter |
| 4 | channel_code 含 weelink/apiyi/volcengine 等 | 对应适配器 |
| 5 | `channel_type=direct` | VolcengineAdapter（默认） |
| 6 | 其他 | WeelinkingAdapter（默认） |

#### 1.4.5 CDN 全链路约束

| 层级 | 文件 | 行为 |
|------|------|------|
| 前端上传 | `cdnUrl.ts` | `pickCdnUrl` 白名单校验，拒绝 data:/blob: |
| 前端提交 | `ComposerArea` / `DynamicForm` | `extractCdnUrls` → `params.images` 为字符串数组 |
| 后端入口 | `user_tasks.py` | `validate_reference_images` 拒绝非 CDN |
| 适配器 | `weelinking.py` / `volcengine.py` | `require_cdn_url`，不再 silent fallback |

白名单域名（前后端一致）: `cdn.jsdmirror.com`、`cdn.jsdelivr.net`、`fastly.jsdelivr.net`、`ghproxy.net`、`raw.githubusercontent.com`

#### 1.4.6 MongoDB 集合一览

| 集合 | 服务 | 用途 |
|------|------|------|
| `tasks` | TaskService | 任务记录、渠道请求/响应、external_task_id |
| `models` | ModelService | 模型配置、param_schema、channel_bindings |
| `channels` | ChannelService | 渠道配置、endpoints、auth_config |
| `sessions` | SessionService | 创作会话 |
| `assets` | AssetService | 上传/生成资源元数据 |
| `users` | UserService | 用户账户 |
| `prompts` / `prompt_versions` | PromptService | Prompt 版本管理 |

---

## 二、启动流程与运维规范

### 2.1 问题根源分析

#### ⚠️ 关键问题 1: Trae IDE 沙箱进程终止

**现象**: 在 Trae IDE 中通过 `RunCommand` 启动的服务，在命令执行完毕后会被沙箱自动终止所有子进程。

**原因**: Trae IDE 的命令执行环境（trae-sandbox）会在每个命令完成后清理其启动的子进程树，导致 `python -m uvicorn` 和 `npm run dev` 等长驻进程被强制杀死。

**解决**: 必须使用 `start` 命令或 `Start-Process` 在**独立窗口**中启动服务，脱离沙箱的进程树。

#### ⚠️ 关键问题 2: 端口占用

**现象**: `OSError: [WinError 10048] 通常每个套接字地址(协议/网络地址/端口)只允许使用一次。`

**原因**: 上一次启动的进程未正常终止，端口 8000/3001 仍被占用。

**解决**: 运行 `stop-all.bat` 通过端口查找并终止占用进程。

#### ⚠️ 关键问题 3: Python 模块路径

**现象**: `ModuleNotFoundError: No module named 'app'`

**原因**: Uvicorn 需要从 `backend/` 目录启动，且 `PYTHONPATH` 需正确指向该目录。

**解决**: 通过 `backend/_run_server.py` 脚本统一设置工作目录和路径。

---

### 2.2 固化的启动方式

> ✅ **推荐方式**：双击运行批处理脚本

| 操作 | 脚本文件 | 说明 |
|------|---------|------|
| **一键启动全部** | `start-all.bat` | 先后启动后端(8000) + 前端(3001)，各自在独立窗口运行 |
| **停止全部** | `stop-all.bat` | 查找占用 8000/3001 端口的进程并终止 |
| **重启全部** | `restart-all.bat` | 等价于 `stop-all.bat` → `start-all.bat` |
| **仅启动后端** | `_start_backend.bat` | 单启动后端 API 服务 |
| **仅启动前端** | `_start_frontend.bat` | 单启动前端开发服务器 |

### 2.3 启动步骤详解

#### 标准启动流程

```
双击 start-all.bat
    │
    ├──► 检查 8000/3001 端口是否被占用
    │       ├── 若被占用 → 提示先运行 stop-all.bat
    │       └── 空闲 → 继续
    │
    ├──► 弹出新窗口 "AIGC Backend :8000"
    │       └── 调用 backend/_run_server.py
    │           ├── 切换工作目录到 backend/
    │           ├── 设置 PYTHONPATH=backend/
    │           └── uvicorn.run("app.main:app", port=8000)
    │
    ├──► 等待 5 秒让后端就绪
    │
    ├──► 弹出新窗口 "AIGC Frontend :3001"
    │       └── 进入 frontend/ 目录
    │           └── 执行 npm run dev (Vite, port=3001)
    │
    └──► 主窗口显示访问地址后 10 秒自动关闭
```

#### 验证启动成功

启动后分别访问以下地址验证：

| 服务 | 地址 | 预期返回 |
|------|------|---------|
| 后端健康检查 | http://localhost:8000/api/health | `{"code":"success", "data":{"status":"ok"}}` |
| 后端 API 文档 | http://localhost:8000/docs | Swagger UI 页面 |
| 前端界面 | http://localhost:3001 | 登录/主页面 |

### 2.4 端口规范

| 端口 | 用途 | 配置位置 | 占用策略 |
|------|------|---------|---------|
| **8000** | 后端 FastAPI | `backend/_run_server.py` | 端口冲突时提示需先停止 |
| **3001** | 前端 Vite Dev Server | `frontend/vite.config.ts` | strictPort=true，占用即报错 |
| **27017** | MongoDB | 外部依赖 | 需自行安装启动 |
| **6379** | Redis | 外部依赖（可选） | 未启动时仅告警，不影响核心功能 |

### 2.5 启动排查清单

遇到 "Request failed with status code 500" 或服务启动失败时，按以下顺序排查：

```
□ 独立窗口中查看后端日志 - 检查是否有导入错误
□ 独立窗口中查看前端日志 - 检查 Vite 是否正常启动
□ 运行 netstat -ano | findstr ":8000" 检查端口占用
□ 运行 netstat -ano | findstr ":3001" 检查端口占用
□ 确认 MongoDB 服务正在运行
□ 查看 backend/ 目录下是否有 loguru 输出的日志
□ 双击运行 stop-all.bat，然后重新双击 start-all.bat
```

---

### 2.6 Python 启动器 launcher.py（推荐无窗口方式）

**核心原理**：`launcher.py` 是一个自包含的 Python 命令行工具，使用 Windows 的 `CREATE_NO_WINDOW | DETACHED_PROCESS` 标志启动子进程，**完全脱离调用者的进程树**，从根本上解决了以下问题：

| 旧方案问题 | launcher.py 解决方案 |
|-----------|-------------------|
| Trae IDE 沙箱在命令结束后终止子进程 | 子进程以 DETACHED_PROCESS 方式启动，不属于沙箱进程树 |
| 启动时弹出多个黑色 cmd 窗口 | CREATE_NO_WINDOW 标志，完全无窗口运行 |
| npm.cmd 在无环境变量时找不到 | 直接调用 `node.exe` + `npm-cli.js`，绕过 cmd 解析 |
| 端口/进程状态不透明 | PID 文件记录 + HTTP 健康检查，自动检测僵尸进程 |
| 中文编码导致的 cmd 语法错误 | 内部全部 Python 处理，无 bat 文件中文编码问题 |

#### 子命令一览

| 命令 | 作用 | 输出 |
|------|------|------|
| `python launcher.py start` | 启动后端(8000) + 前端(3001) | 启动成功后显示访问地址 |
| `python launcher.py stop` | 停止所有服务（按 PID 文件精准终止） | 显示停止结果 |
| `python launcher.py restart` | stop → start | 同上 |
| `python launcher.py status` | 查看运行状态 / PID / 端口 / HTTP 健康检查 | 表格形式展示 |
| `python launcher.py log backend` | 查看后端日志末尾 80 行 | 文本输出 |
| `python launcher.py log frontend` | 查看前端日志末尾 80 行 | 文本输出 |
| `python launcher.py log all` | 同时查看两端日志末尾 | 文本输出 |

#### 启动流程详解（launcher.py start）

```
启动: python launcher.py start
  │
  ├──► [backend] 构造命令 = [python.exe, "-u", "backend/_run_server.py"]
  │       ├── 工作目录 = backend/
  │       ├── 环境变量 = PYTHONPATH=backend/
  │       ├── 进程标志 = CREATE_NO_WINDOW | DETACHED_PROCESS
  │       ├── stdout → 重定向到 .runtime/backend.log
  │       ├── 写入 PID → .runtime/backend.pid
  │       └── 健康检查: 轮询 GET http://127.0.0.1:8000/api/health (15s 超时)
  │
  └──► [frontend] 构造命令 = [node.exe, "node_modules/npm/bin/npm-cli.js", "run", "dev"]
          ├── 工作目录 = frontend/
          ├── 环境变量 = 继承 (PATH 中需包含 node.exe)
          ├── 进程标志 = CREATE_NO_WINDOW | DETACHED_PROCESS
          ├── stdout → 重定向到 .runtime/frontend.log
          ├── 写入 PID → .runtime/frontend.pid
          └── 健康检查: 轮询 GET http://127.0.0.1:3001/ (45s 超时)

完成: 显示 "全部服务启动成功" + 访问地址
```

#### 停止流程详解（launcher.py stop）

```
停止: python launcher.py stop
  │
  ├──► 读取 .runtime/backend.pid → 用 taskkill /F /T /PID <pid> 终止进程树
  │       └── 成功后删除 PID 文件
  │
  ├──► 读取 .runtime/frontend.pid → 同样终止
  │
  └──► 兜底检查: 如果端口 8000/3001 仍被占用
          └── 用 netstat -ano 查找占用进程并强制终止
```

#### 运行时目录结构

```
.runtime/
├── backend.pid       # JSON: {"pid": 38800, "started_at": 1234567890}
├── frontend.pid      # JSON: {"pid": 34048, "started_at": 1234567890}
├── backend.log       # 后端 stdout/stderr (含 uvicorn 日志 + loguru 输出)
└── frontend.log      # 前端 stdout/stderr (含 Vite 编译输出)
```

#### 典型使用场景

| 场景 | 命令 | 预期输出 |
|------|------|---------|
| 首次使用 | `python launcher.py start` | backend就绪 → frontend就绪 → 全部启动成功 |
| 修改前端代码后 | `python launcher.py restart` | 先停止 → 再启动（比逐个重启可靠） |
| 查看是否正常 | `python launcher.py status` | [OK] backend / [OK] frontend |
| 500 错误排查 | `python launcher.py log backend` | 末尾显示最近的 API 调用日志 |
| 前端白屏 | `python launcher.py log frontend` | 查看 Vite 编译错误/警告 |

#### 健康检查端点

服务运行时可通过以下方式独立验证：

```bash
# 后端健康检查
curl http://localhost:8000/api/health
# → {"code":"success","data":{"status":"ok"}}

# 前端页面
curl -I http://localhost:3001/
# → HTTP/1.1 200 OK
```

#### 环境要求与兼容策略

| 依赖 | 要求 | 查找方式 |
|------|------|---------|
| Python 3.11+ | 已在虚拟环境中 | `sys.executable`（使用当前解释器） |
| Node.js | 已安装 | `shutil.which("node.exe")`（从系统 PATH 查找） |
| npm | 随 Node.js 安装 | `<node_dir>/node_modules/npm/bin/npm-cli.js` |

**策略**：
- 后端：始终使用启动 launcher.py 的同一个 Python 解释器，确保依赖包一致
- 前端：通过 `node.exe npm-cli.js run dev` 直接调用，不依赖 cmd.exe 解析路径

---

## 三、后端核心技术方案

### 3.1 架构分层

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口，路由注册，MongoDB/Redis 初始化
│   ├── routers/                # API 路由层
│   │   ├── health.py           # GET /api/health
│   │   ├── auth.py             # POST /api/auth/login|register|logout
│   │   ├── user.py             # GET/PUT /api/user/profile|pwd
│   │   ├── user_models.py      # GET /api/models
│   │   ├── user_tasks.py       # POST /api/tasks/generate（核心）
│   │   ├── user_sessions.py    # /api/sessions
│   │   ├── user_upload.py      # POST /api/upload/image|file
│   │   ├── assets.py           # /api/assets 资源库 CRUD + upload
│   │   ├── prompts.py          # /api/prompts 版本管理
│   │   ├── admin_models.py     # /api/admin/models
│   │   ├── admin_channels.py   # /api/admin/channels
│   │   ├── admin_tasks.py      # /api/admin/tasks
│   │   └── admin_users.py      # /api/admin/users
│   ├── services/
│   │   ├── gateway_service.py  # ← ModelGateway：路由、端点选择、故障切换
│   │   ├── task_service.py     # 任务生命周期、大字段截断
│   │   ├── model_service.py    # 模型 CRUD、channel_bindings
│   │   ├── channel_service.py  # 渠道 CRUD（内部明文 auth）
│   │   ├── session_service.py  # 会话管理
│   │   ├── storage_service.py  # GitHubStorageService + CDN
│   │   ├── asset_service.py    # assets 集合
│   │   ├── auth_service.py     # JWT
│   │   ├── user_service.py     # 用户
│   │   └── prompt_service.py   # Prompt 版本
│   ├── adapters/
│   │   ├── base.py             # BaseChannelAdapter + ConfigEngine 集成
│   │   ├── weelinking.py       # Weelink/APIYi OpenAI 兼容
│   │   ├── volcengine.py       # 火山引擎直连（视频异步轮询）
│   │   └── __init__.py         # create_adapter 路由
│   ├── schemas/                # Pydantic 模型（channel/model/task/...）
│   ├── utils/url_utils.py      # join_url 等
│   └── core/
│       ├── config.py           # Settings（.env）
│       ├── database.py         # Motor MongoDB
│       ├── config_engine.py    # body_params 配置化请求/响应解析
│       ├── cdn.py              # CDN URL 白名单校验
│       ├── security.py         # Fernet 加解密（迁移脚本用）
│       ├── middleware.py       # JWT 中间件
│       ├── redis_client.py     # Redis（可选）
│       ├── response.py         # 统一响应格式
│       ├── logging_config.py   # Loguru
│       └── utils.py            # task_id / trace_id
├── scripts/                    # 种子数据、迁移、调试脚本
└── tests/                      # 流式、图生图、全链路测试
```

### 3.2 模型网关 (Model Gateway) - 核心机制

**文件**: `backend/app/services/gateway_service.py`

#### 职责
1. 接收模型执行请求（model_code + category + params）
2. 从 MongoDB 查找模型配置，验证模型状态与 `param_schema`
3. **选择最优渠道**: 按 `priority` 排序，选择第一个 `active` 的渠道绑定
4. **确定端点类型**: `_determine_endpoint_type`（chat / image / image_edits / video / video_image）
5. 创建渠道适配器，传入 `endpoint_type` 调用 `adapter.execute()`
6. 主渠道失败时，自动切换到备用渠道（保留相同 endpoint_type）
7. 记录 `channel_request`（含 `http_request`）与 `channel_response`，统一返回格式

#### 配置化引擎（ConfigEngine）

**文件**: `backend/app/core/config_engine.py`

当渠道 `endpoints[]` 配置了 `body_params` / `response_mappings` 时：
- 请求体由 `ConfigEngine.build_request_body()` 按 `value_type`（fixed/dynamic/image）构建
- 响应由 `ConfigEngine.parse_response()` 按端点类型自动提取
- 未配置时回退到适配器内置 `convert_params` / `parse_result`（如 `weelinking.py` 硬编码逻辑）

`BaseChannelAdapter.execute()` 在 `backend/app/adapters/base.py` 中统一编排上述流程。

#### 渠道选择算法

```python
# 伪代码说明
bindings = model_config["channel_bindings"]  # 模型绑定的渠道列表
active_bindings = [b for b in bindings if b["status"] == "active"]
active_bindings.sort(key=lambda b: b["priority"], reverse=True)  # 优先级降序

for binding in active_bindings:
    channel = db.channels.find_one({"channel_code": binding["channel_code"]})
    if channel and channel["status"] == "active":
        # 选中此渠道，执行请求
        return execute_with_adapter(channel, binding, params)

# 所有渠道均不可用 → 返回 channel_error
return {"success": False, "error_code": "channel_error", "error_message": "没有可用的渠道绑定"}
```

> **重要**: 每个模型必须至少绑定一个 `active` 状态的渠道，且该渠道本身也必须是 `active` 状态。
> 渠道绑定在「管理页面 → 模型管理 → 编辑模型」中配置。

### 3.3 渠道适配器模式

**文件**: `backend/app/adapters/`

采用**适配器模式**抽象不同 AI 服务提供商的差异：

```
              ┌─────────────────────────────┐
              │   BaseChannelAdapter (抽象)  │
              ├─────────────────────────────┤
              │ ・ convert_params()          │
              │ ・ call_api()                │
              │ ・ parse_result()            │
              │ ・ get_api_key_for_category()│
              └──────────────┬──────────────┘
                             │ 继承
              ┌──────────────┴──────────────┐
              ▼                             ▼
      ┌────────────────┐           ┌────────────────┐
      │ WeelinkingAdap │           │   ...更多渠道   │
      │ ter (OpenAI兼容)│           │   适配器       │
      └────────────────┘           └────────────────┘
```

#### Weelink 适配器 - 关键实现点

**文件**: `backend/app/adapters/weelinking.py`

1. **双模式运行**:
   - **配置驱动**: 渠道配置了 `endpoints` + `body_params` 时，由 ConfigEngine 构建请求
   - **内置逻辑**: 未配置端点时，走 `_call_text_api` / `_call_image_api` / `_call_video_api`

2. **文本流式**: `api_config.text_stream=true` 时 `_http_post_stream` 聚合 SSE

3. **图像生成 (gpt-image-2)**:
   - 路径: `POST {base_url}/images/generations`（或 `image_edits` 端点）
   - 请求体核心字段: `model`, `prompt`, `image`（CDN URL 字符串数组）, `n`, `size`, `quality`, `output_format`, `input_fidelity`
   - 参考图必须通过 `require_cdn_url` 校验

4. **多模态文本**: messages 中 `image_url` 类型，参考图同样要求 CDN URL

#### Volcengine 适配器

**文件**: `backend/app/adapters/volcengine.py`

- 视频: 异步 `POST .../tasks` + 轮询 `GET .../tasks/{id}`
- 支持服务器重启后 `query_task` / `POST /api/tasks/{id}/recover` 恢复
- 参考图走 `content[].image_url`，需 CDN URL

### 3.4 异步编程规范

所有涉及 I/O 的操作必须使用 `async/await`：

```python
# ✅ 正确: 异步方法调用前加 await
channel = await self.channel_service.get_by_code(channel_code)
result = await adapter.execute(...)

# ❌ 错误: 省略 await 导致返回 coroutine 对象
# channel = self.channel_service.get_by_code(...)  # 返回 <coroutine object>
# channel.get("status")  # 抛出: 'coroutine' object has no attribute 'get'
```

### 3.5 API 路由一览

#### 健康检查
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/` | 服务信息 |

#### 用户端 - 模型
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models?category=text` | 模型列表（按分类筛选） |
| GET | `/api/models/default?category=text` | 获取分类下默认模型 |
| GET | `/api/models/{model_code}` | 模型详情 |

#### 用户端 - 任务/生成
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/tasks/generate` | **核心**: 同步执行生成（前端主入口） |
| POST | `/api/tasks` | 仅创建任务记录 |
| POST | `/api/tasks/{task_id}/execute` | 执行已创建任务 |
| POST | `/api/tasks/{task_id}/retry` | 重试失败任务 |
| POST | `/api/tasks/{task_id}/recover` | 恢复 processing 状态（视频轮询） |
| GET | `/api/tasks/{task_id}` | 查询任务 |
| GET | `/api/tasks/session/{session_id}` | 会话任务列表（升序） |
| GET | `/api/tasks` | 任务列表（分页/筛选） |

#### 用户端 - 上传与资源
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload/image` | 图片上传 → GitHub CDN |
| POST | `/api/upload/file` | 通用文件上传 |
| GET/POST/DELETE | `/api/assets` | 资源库列表/上传/删除 |

#### 用户端 - 认证与会话
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 注册 |
| POST | `/api/auth/login` | 登录（返回 JWT） |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/user/profile` | 用户信息 |
| POST | `/api/sessions` | 创建会话 |
| GET | `/api/sessions/{session_id}` | 会话详情 |

#### 用户端 - Prompt
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/prompts/published/list` | 已发布 Prompt（创作台选用） |
| CRUD | `/api/prompts/*` | Prompt 版本管理 |

#### 管理端 - 模型
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/models` | 模型列表 |
| POST | `/api/admin/models` | 创建模型（含 channel_bindings 数组） |
| GET | `/api/admin/models/{id}` | 模型详情 |
| PUT | `/api/admin/models/{id}` | 更新模型（保留原 channel_bindings 除非显式传入） |

#### 管理端 - 渠道
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/channels` | 渠道列表 |
| POST | `/api/admin/channels` | 创建渠道（base_url / auth_config / api_key 等） |
| GET | `/api/admin/channels/{id}` | 渠道详情 |
| PUT | `/api/admin/channels/{id}` | 更新渠道 |

#### 管理端 - 任务
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/tasks` | 任务列表（支持分页、筛选） |
| GET | `/api/admin/tasks/{id}` | 任务详情 |
| GET | `/api/admin/tasks/stats/overview` | 任务统计 |

### 3.6 统一响应格式

所有 API 返回统一格式：

```json
{
  "code": "success",      // "success" | 错误代码如 "model_not_found" | "channel_error"
  "message": "操作成功",   // 人类可读的提示
  "data": { ... }         // 返回的业务数据（对象/数组/字符串等）
}
```

`code !== "success"` 时，前端应展示 `message` 作为错误提示。

### 3.7 安全机制

**JWT 认证** (`auth_service.py` + `middleware.py` + 前端 `request.ts` 拦截器)

**API Key 存储**:
- 当前 `channel_service._to_internal_response` 对网关返回**明文** `auth_config`（运行时使用）
- `security.py` 提供 Fernet 加解密，供 `scripts/migrate_channel_plaintext.py` 迁移历史加密数据
- 环境变量兜底: `WEELINK_API_KEY`（`settings.weelink_api_key`）

### 3.8 依赖管理

**文件**: `backend/requirements.txt`

```
fastapi>=0.110.0,<0.116.0        # Web 框架
uvicorn[standard]>=0.27.0         # ASGI 服务器
pydantic>=2.5.0                   # 数据验证 (FastAPI 依赖)
motor>=3.4.0                      # MongoDB 异步驱动
aiohttp>=3.9.0                    # 异步 HTTP 客户端
httpx>=0.27.0                     # HTTP/2 客户端（渠道调用）
openai>=1.30.0                    # OpenAI 官方 SDK（渠道适配器）
redis>=5.0.0                      # Redis（可选，缓存）
python-dotenv>=1.0.0              # .env 文件加载
cryptography>=42.0.0              # Fernet 加密
loguru>=0.7.0                     # 结构化日志
tenacity>=8.0.0                   # 重试装饰器
```

安装命令:
```bash
cd backend
pip install -r requirements.txt
```

---

## 四、前端核心技术方案

### 4.1 项目结构

```
frontend/
├── src/
│   ├── App.tsx                  # 路由、JWT 守卫、侧边栏、启动时 syncTasksFromBackend
│   ├── main.tsx
│   ├── pages/
│   │   ├── Workspace.tsx        # 创作工作台（ComposerArea + ChatArea）
│   │   ├── AssetManager.tsx     # 资源管理
│   │   ├── PromptManager.tsx    # Prompt 管理
│   │   ├── ModelAdmin.tsx       # 模型管理
│   │   ├── ChannelAdmin.tsx     # 渠道管理（cURL 导入）
│   │   ├── TaskAdmin.tsx        # 任务监控（含 channel_request 展示）
│   │   └── Login.tsx
│   ├── components/
│   │   ├── ComposerArea.tsx     # 输入区、上传、参数、generate 调用
│   │   ├── ChatArea.tsx         # 对话式结果展示
│   │   ├── ParamPanel.tsx       # 模型选择 + 参数 + 图片上传
│   │   ├── DynamicForm.tsx      # param_schema 动态表单
│   │   └── AssetPicker.tsx      # 资源库选择器
│   ├── store/
│   │   └── generation.ts        # Zustand：tasks/session/model/params/sync
│   ├── api/
│   │   ├── request.ts           # Axios（普通 5min + 长任务 30min 超时）
│   │   ├── index.ts             # 全部 API
│   │   └── prompt.ts
│   ├── types/                   # ModelItem / TaskItem / AssetItem 等
│   └── utils/
│       ├── cdnUrl.ts            # CDN 白名单（与后端 cdn.py 对齐）
│       └── curlParser.ts        # 渠道 cURL 解析
├── vite.config.ts               # port 3001, proxy /api → 8000
└── package.json
```

### 4.2 Vite 配置

**文件**: `frontend/vite.config.ts`

```typescript
server: {
  port: 3001,           // 固定端口
  strictPort: true,     // ⚠️ 端口被占用时报错，而不是自动 +1
  host: true,           // 允许外部访问（局域网调试）
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 所有 /api/** 请求代理到后端
      changeOrigin: true,
    },
  },
}
```

**为什么代理很重要**: 前端代码直接请求 `/api/models`，由 Vite 开发服务器在本地转发到 `localhost:8000/api/models`，避免了跨域问题（CORS）。

### 4.3 前端依赖

| 依赖 | 用途 |
|------|------|
| `react@18` / `react-dom@18` | UI 框架 |
| `typescript@5.2` | 类型安全 |
| `antd@5.17` | UI 组件库（表格、表单、模态框等） |
| `@ant-design/icons` | 图标库 |
| `axios@1.7` | HTTP 客户端 |
| `zustand@4.5` | 轻量级状态管理（替代 Redux） |
| `react-router-dom@6.23` | 路由 |
| `dayjs` | 日期处理 |
| `vite@5.2` | 构建工具 + 开发服务器 |

---

## 五、数据模型与数据库设计

### 5.1 集合（Collections）

```
MongoDB 数据库名: aigc_platform
```

#### `channels` - 渠道配置

| 字段 | 类型 | 说明 |
|------|------|------|
| `channel_code` | string | 渠道唯一标识，如 `"weelink_text"` |
| `channel_name` | string | 显示名 |
| `channel_type` | string | `"aggregator"` 或 `"direct"` |
| `base_url` | string | API 根地址，如 `"https://api.weelinking.com/v1"` |
| `auth_config` | object | `{api_key: <Fernet 加密字符串>}` |
| `retry_config` | object | `{timeout, max_retries, retry_delay}` |
| `rate_limit_config` | object | `{requests_per_minute, ...}` |
| `status` | string | `"active"` / `"inactive"` |
| `description` | string | 备注 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

#### `models` - 模型配置

| 字段 | 类型 | 说明 |
|------|------|------|
| `model_code` | string | 模型唯一标识，如 `"gpt-5.5"` |
| `model_name` | string | 显示名 |
| `category` | string | `"text"` / `"image"` / `"video"` |
| `cover` | string | 封面图 URL（可选） |
| `description` | string | 模型描述 |
| `tags` | string[] | 标签数组 |
| `param_schema` | object | 参数字段定义（前端用） |
| `channel_bindings` | object[] | **关键**: 绑定的渠道列表 `[{channel_code, channel_model_id, priority, status}]` |
| `status` | string | `"online"` / `"offline"` |
| `is_default` | boolean | 是否为该分类默认模型 |
| `sort_order` | number | 排序权重 |
| `created_at` / `updated_at` | datetime | 时间戳 |

> **channel_bindings 字段解释**:
> - `channel_code`: 引用 `channels.channel_code`
> - `channel_model_id`: 该渠道上实际使用的模型名（可能与 `model_code` 不同）
> - `priority`: 优先级（数字越大越优先被选中）
> - `status`: `"active"` / `"inactive"`

#### `channels` - 渠道配置

| 字段 | 类型 | 说明 |
|------|------|------|
| `channel_code` | string | 唯一标识 |
| `channel_name` | string | 显示名 |
| `channel_type` | string | `aggregator` / `direct` |
| `channel_provider` | string | `weelinking` / `apiyi` / `volcengine` |
| `base_url` | string | API 根地址 |
| `auth_config` | object | `{api_key}` |
| `endpoints` | array | **推荐**: 端点配置（type/endpoint/body_params） |
| `api_config` | object | **兼容旧版**: text_path/image_path 等 |
| `retry_config` | object | timeout/max_retries/poll_interval 等 |
| `status` | string | `active` / `inactive` |

#### `tasks` - 任务记录

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务唯一 ID |
| `session_id` / `user_id` | string | 会话与用户隔离 |
| `model_code` / `category` | string | 模型与类型 |
| `params` | object | 用户入参（images 为 CDN URL 数组） |
| `status` | string | pending/processing/success/failed |
| `result` | object | 生成结果 |
| `error_message` | string | 失败原因 |
| `channel_code` | string | 实际使用渠道 |
| `trace_id` | string | 全链路追踪 |
| `channel_request` / `channel_response` | object | 渠道入参/出参（管理端可查） |
| `external_task_id` | string | 外部异步任务 ID（视频恢复用） |
| `duration_ms` | number | 耗时 |

#### `assets` - 资源元数据

| 字段 | 类型 | 说明 |
|------|------|------|
| `url` | string | 主 CDN URL |
| `cdn_urls` | string[] | 多 CDN 回退地址 |
| `file_path` | string | GitHub 仓库内路径 |
| `category` | string | image/video/file |
| `source_type` | string | upload / generated |

#### `users` / `prompts` / `prompt_versions`

用户账户与 Prompt 版本化管理，详见 `user_service.py` / `prompt_service.py`。

---

## 六、API 调用示例

### 6.1 文本生成（前端主要调用）

**请求**:
```http
POST /api/tasks/generate
Content-Type: application/json

{
  "model_code": "gpt-5.5",
  "category": "text",
  "params": {
    "prompt": "你好，请用一句话介绍你自己"
  }
}
```

**响应**（成功，约 3-10 秒）:
```json
{
  "code": "success",
  "message": "操作成功",
  "data": {
    "task_id": "task_xxxxxx",
    "status": "success",
    "result": {
      "type": "text",
      "text": "你好，我是 Codex，一个能帮你阅读、修改、调试和解释代码的 AI 编程助手。",
      "choices": [...]
    },
    "duration_ms": 5584,
    "created_at": "2026-06-15T13:53:47.870097"
  }
}
```

**响应**（失败，如无可用渠道）:
```json
{
  "code": "channel_error",
  "message": "没有可用的渠道绑定",
  "data": null
}
```

### 6.2 模型列表

**请求**:
```http
GET /api/models?category=text
```

**响应**:
```json
{
  "code": "success",
  "message": "操作成功",
  "data": [
    {
      "id": "6a2ea2bb...",
      "model_code": "gpt-5.5",
      "model_name": "gpt-5.5",
      "category": "text",
      "is_default": true
    },
    {
      "id": "6a2eba33...",
      "model_code": "gemini-2.5-flash",
      "model_name": "gemini-2.5-flash",
      "category": "text",
      "is_default": false
    }
  ]
}
```

---

## 七、常见问题排查 (FAQ)

### Q1: 前端提示 "Request failed with status code 500"

**可能原因**:
- 后端服务未启动或已终止
- 后端启动在 IDE 沙箱中被自动终止
- MongoDB 未连接

**排查**:
1. 打开 `http://localhost:8000/api/health` 看是否返回 JSON
2. 如果无法访问，说明后端没启动 → 双击 `stop-all.bat` → 双击 `start-all.bat`
3. 检查后端窗口日志是否有 `MongoDB 初始化失败` 字样 → 启动本地 MongoDB

### Q2: 生成失败: "没有可用的渠道绑定"

**原因**: 该模型的 `channel_bindings` 为空，或绑定的渠道均为 `inactive`，或渠道本身为 `inactive`

**解决**:
1. 登录管理页面（前端导航菜单）
2. 进入「模型管理」→ 找到该模型 → 点击「编辑」
3. 在「渠道绑定」区域添加/激活至少一条渠道绑定
4. 确认绑定的渠道（如 `weelink_text`）在「渠道管理」中状态为 `active`
5. 保存后重试生成

### Q3: 生成失败: "渠道鉴权失败，请检查API密钥" / "openai_error"

**原因**: 渠道配置中的 API Key 无效或已过期

**解决**:
1. 进入「渠道管理」→ 找到对应渠道 → 「编辑」
2. 重新输入正确的 API Key（如 Weelink 平台获取的 key）
3. 保存后后端会自动用新 Key 加密存储

### Q4: 端口 8000 / 3001 被占用

**现象**: 启动时提示端口占用或启动后无法访问

**解决**:
```bash
# 查找占用进程
netstat -ano | findstr ":8000"
# 或直接双击运行
stop-all.bat
```

### Q5: 前端页面空白 / 白屏

**原因**: 前端依赖未安装，或 Vite 编译错误

**解决**:
1. 查看前端窗口中是否有 `node_modules missing` 之类的提示
2. 进入 `frontend/` 目录，运行 `npm install` 安装依赖
3. 重新启动前端

### Q6: 文本生成很慢 / 超时

**原因**: Weelink API 有时响应较慢（尤其是复杂请求）

**当前配置**:
- 后端超时: 60 秒
- 前端 axios 默认超时

如果持续超时，可考虑:
1. 检查网络到 `api.weelinking.com` 的连通性
2. 在渠道配置中调整 `timeout` 参数

---

## 八、脚本文件说明

| 文件 | 类型 | 作用 |
|------|------|------|
| `start-all.bat` | 启动脚本 | 一键启动全部服务（用户首选） |
| `stop-all.bat` | 停止脚本 | 终止占用 8000/3001 的进程 |
| `restart-all.bat` | 重启脚本 | stop → start 组合 |
| `_start_backend.bat` | 单项启动 | 仅启动后端 |
| `_start_frontend.bat` | 单项启动 | 仅启动前端 |
| `backend/_run_server.py` | Python 启动器 | 统一设置工作目录和 PYTHONPATH，调用 uvicorn |

### 脚本调用关系

```
start-all.bat
    ├──► start "" cmd /k _start_backend.bat
    │       └──► python backend/_run_server.py
    │           └──► uvicorn.run(app.main:app, port=8000)
    │
    └──► start "" cmd /k _start_frontend.bat
            └──► cd frontend && npm run dev
```

---

## 九、关键配置文件清单

| 文件 | 配置项 |
|------|--------|
| `backend/app/main.py` | CORS 允许所有来源 /api 路由前缀 |
| `backend/app/core/config.py` | MongoDB 连接串 / Redis 地址 / 端口 / 加密密钥 |
| `backend/_run_server.py` | 固定端口 8000，工作目录切换 |
| `frontend/vite.config.ts` | 固定端口 3001，strictPort=true，/api 代理到 8000 |
| `frontend/package.json` | npm run dev → vite |

---

## 十、部署规范总结

### 开发环境快速启动（3 步）

```
1. 确认本地 MongoDB 已启动（默认 mongodb://localhost:27017）
2. 安装依赖（首次）:
   ├── backend: cd backend && pip install -r requirements.txt
   └── frontend: cd frontend && npm install
3. 双击运行: start-all.bat
   → 自动弹出两个窗口（后端日志 / 前端日志）
   → 浏览器访问 http://localhost:3001
```

### 日常操作

| 场景 | 操作 |
|------|------|
| 开始开发 | 双击 `start-all.bat` |
| 切换代码分支后 | 双击 `restart-all.bat` |
| 结束开发 | 双击 `stop-all.bat` |
| 查看服务日志 | 查看独立的两个 cmd 窗口输出 |
| 修改后端代码 | 后端未启用 hot-reload，修改后需 `stop-all.bat` → `start-all.bat` |
| 修改前端代码 | Vite 自带 HMR，保存即刷新 |

### 不推荐的做法

❌ 不要在 Trae IDE 的 Terminal 中直接运行 `uvicorn` 或 `npm run dev`（会被沙箱终止）

❌ 不要用 `taskkill /F /IM python.exe` 这种 blanket kill（可能误杀其他 Python 进程）

❌ 不要修改 `backend/_run_server.py` 的端口号而不同步修改 `frontend/vite.config.ts` 的代理配置

---

---

## 十一、模型与渠道接入开发规范（强制）

### 11.1 核心架构原则

#### 11.1.1 适配器模式总览

系统采用**适配器模式（Adapter Pattern）**实现多渠道统一接入，所有 AI 服务提供商必须通过适配器层抽象为一致的调用接口。

```
┌──────────────────────────────────────────────┐
│          Model Gateway (模型网关)             │
│  - 参数校验 → 渠道路由 → 故障切换 → 日志追踪   │
└──────────────────┬───────────────────────────┘
                   │ 调用
                   ▼
┌──────────────────────────────────────────────┐
│      BaseChannelAdapter (抽象基类)            │
│  - convert_params()    参数转换               │
│  - call_api()          渠道 API 调用          │
│  - parse_result()      结果解析               │
│  - parse_error()       错误处理               │
│  - get_api_key_for_category()  API Key 获取   │
└──────────────┬───────────────────────────────┘
               │ 继承实现
     ┌─────────┼─────────┐
     ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│Weelink │ │Volceng │ │ 更多... │
│Adapter │ │ Adapter│ │ Adapter│
└────────┘ └────────┘ └────────┘
```

#### 11.1.2 强制分层约束

| 层级 | 职责 | 禁止行为 |
|------|------|----------|
| **Model Gateway** | 路由选择、参数校验、故障切换 | 不直接调用外部 API |
| **Channel Adapter** | 协议转换、HTTP 调用、结果解析 | 不包含业务逻辑、不操作数据库 |
| **Channel Service** | 渠道 CRUD、API Key 加密/解密 | 不执行 HTTP 请求 |
| **Model Service** | 模型 CRUD、渠道绑定管理 | 不执行生成任务 |

**跨层调用禁令**：
- ❌ Adapter 不得直接调用 Service 层
- ❌ Gateway 不得绕过 Adapter 直接调用 HTTP
- ❌ Router 不得直接操作 MongoDB

---

### 11.2 新增渠道适配器开发流程

#### 步骤 1: 创建适配器文件

在 `backend/app/adapters/` 下创建新适配器文件，命名规范：`{channel_name}.py`（小写下划线）

**示例**：新增 OpenRouter 渠道 → 创建 `backend/app/adapters/openrouter.py`

#### 步骤 2: 实现适配器类

```python
from __future__ import annotations
from typing import Any, Dict
import httpx
from app.adapters.base import BaseChannelAdapter
from app.core.logging_config import get_logger

logger = get_logger()


class OpenRouterAdapter(BaseChannelAdapter):
    """OpenRouter 渠道适配器"""

    def __init__(self, channel_config: Dict[str, Any], trace_id: str):
        super().__init__(channel_config, trace_id)
        self.timeout = self.retry_config.get("timeout", 60)
        self.api_config = channel_config.get("api_config", {
            "text_path": "/chat/completions",
            "image_path": "/images/generations",
            "video_path": "/videos/generations",
            "text_stream": True,
        })

    async def convert_params(self, model_config: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """将平台通用参数转换为渠道专属格式"""
        # TODO: 根据渠道 API 文档实现参数转换逻辑
        return params

    async def call_api(self, category: str, channel_params: Dict[str, Any], 
                       channel_model_id: str, api_key: str) -> Dict[str, Any]:
        """调用渠道 HTTP API"""
        # TODO: 实现 HTTP 请求逻辑（参考 weelinking.py 的 _http_post 方法）
        pass

    async def parse_result(self, category: str, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """将渠道原始响应解析为平台统一格式"""
        # TODO: 根据渠道响应格式实现解析逻辑
        pass

    def parse_error(self, exception: Exception) -> tuple[str, str]:
        """将异常转换为统一错误码和消息"""
        err_msg = str(exception).lower()
        if "401" in err_msg or "unauthorized" in err_msg:
            return "channel_error", "渠道鉴权失败，请检查 API 密钥"
        elif "429" in err_msg or "rate limit" in err_msg:
            return "service_unavailable", "模型服务繁忙，请稍后再试"
        else:
            return "internal_error", f"生成失败: {str(exception)[:200]}"
```

#### 步骤 3: 注册适配器

在 `backend/app/adapters/__init__.py` 中注册新适配器：

```python
from app.adapters.openrouter import OpenRouterAdapter

# 在 create_adapter 函数中添加判断逻辑
def create_adapter(channel_config: Dict[str, Any], trace_id: str) -> Optional[BaseChannelAdapter]:
    channel_type = channel_config.get("channel_type", "")
    channel_code = channel_config.get("channel_code", "")

    if channel_type == "aggregator" or channel_code.startswith("weelink"):
        return WeelinkingAdapter(channel_config, trace_id)
    
    if channel_type == "volcengine" or channel_code.startswith("volcengine"):
        return VolcengineAdapter(channel_config, trace_id)
    
    # ✅ 新增：OpenRouter 渠道
    if channel_type == "openrouter" or channel_code.startswith("openrouter"):
        return OpenRouterAdapter(channel_config, trace_id)

    logger.warning(f"[{trace_id}] 未找到适配的渠道适配器: {channel_code}")
    return WeelinkingAdapter(channel_config, trace_id)  # 默认降级

# 在 ChannelAdapterRegistry 中注册
ChannelAdapterRegistry.register("openrouter", OpenRouterAdapter)
```

#### 步骤 4: 编写单元测试脚本

在 `backend/scripts/` 下创建测试脚本 `test_{channel_name}_adapter.py`：

```python
"""测试 OpenRouter 适配器"""
import asyncio
from app.adapters.openrouter import OpenRouterAdapter

async def test_openrouter():
    channel_config = {
        "channel_code": "openrouter_test",
        "base_url": "https://openrouter.ai/api/v1",
        "auth_config": {"api_key": "your-test-key"},
        "retry_config": {"timeout": 30, "max_retries": 1, "retry_delay": 1},
        "api_config": {
            "text_path": "/chat/completions",
            "text_stream": False,
        }
    }
    
    adapter = OpenRouterAdapter(channel_config, "test_trace_001")
    
    # 测试文本生成
    result = await adapter.execute(
        category="text",
        model_config={"model_code": "gpt-3.5-turbo"},
        params={"prompt": "你好"},
        channel_model_id="gpt-3.5-turbo",
        api_key="your-test-key"
    )
    
    print(f"测试结果: {result}")
    assert result["success"] == True, f"测试失败: {result.get('error_message')}"

if __name__ == "__main__":
    asyncio.run(test_openrouter())
```

#### 步骤 5: 更新 agent.md

在本文档的「11.5 已实现渠道清单」章节中新增渠道记录。

---

### 11.3 新增模型配置流程

#### 前置条件

1. 目标渠道已在 `channels` 集合中配置且状态为 `active`
2. 渠道适配器已实现并注册
3. 渠道 API Key 已正确配置（通过管理界面或环境变量）

#### 步骤 1: 定义模型参数 Schema

根据渠道 API 文档，定义模型的 `param_schema.fields`：

```json
{
  "fields": [
    {
      "name": "prompt",
      "label": "提示词",
      "field_type": "textarea",
      "required": true,
      "placeholder": "请输入描述..."
    },
    {
      "name": "temperature",
      "label": "温度",
      "field_type": "slider",
      "required": false,
      "default": 0.7,
      "min": 0,
      "max": 2,
      "step": 0.1,
      "help_text": "控制生成内容的随机性"
    },
    {
      "name": "size",
      "label": "尺寸",
      "field_type": "select",
      "required": false,
      "default": "1024x1024",
      "options": [
        {"label": "1:1", "value": "1024x1024"},
        {"label": "16:9", "value": "1792x1024"}
      ]
    }
  ]
}
```

**支持的 field_type**：
- `text`: 单行文本输入
- `textarea`: 多行文本输入
- `number`: 数字输入框
- `slider`: 滑块控件
- `select`: 下拉选择框
- `switch`: 开关按钮
- `image_upload`: 图片上传控件

#### 步骤 2: 配置渠道绑定

在 `channel_bindings` 数组中绑定至少一个渠道：

```json
{
  "channel_bindings": [
    {
      "channel_code": "weelink_image",
      "channel_model_id": "dall-e-3",
      "priority": 1,
      "status": "active"
    },
    {
      "channel_code": "openrouter_image",
      "channel_model_id": "stable-diffusion-xl",
      "priority": 2,
      "status": "active"
    }
  ]
}
```

**字段说明**：
- `channel_code`: 引用 `channels.channel_code`
- `channel_model_id`: 渠道侧实际的模型 ID（可能与平台 `model_code` 不同）
- `priority`: 优先级（数字越大越优先被选中）
- `status`: `"active"` / `"inactive"`

#### 步骤 3: 通过管理界面或 API 创建模型

**方式 A: 管理界面**
1. 访问前端「系统管理 → 模型管理」
2. 点击「新建模型」
3. 填写模型信息、参数 Schema、渠道绑定
4. 保存后自动写入 MongoDB

**方式 B: API 调用**
```bash
curl -X POST http://localhost:8000/api/admin/models \
  -H "Content-Type: application/json" \
  -d '{
    "model_code": "my-new-model",
    "model_name": "我的新模型",
    "category": "text",
    "channel_bindings": [
      {
        "channel_code": "weelink_text",
        "channel_model_id": "gpt-4o",
        "priority": 1,
        "status": "active"
      }
    ],
    "param_schema": {
      "fields": [
        {
          "name": "prompt",
          "label": "提示词",
          "field_type": "textarea",
          "required": true
        }
      ]
    },
    "status": "online",
    "is_default": false
  }'
```

#### 步骤 4: 验证模型可用性

```bash
# 1. 查询模型列表
curl http://localhost:8000/api/models?category=text

# 2. 执行生成测试
curl -X POST http://localhost:8000/api/tasks/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model_code": "my-new-model",
    "category": "text",
    "params": {"prompt": "测试提示词"}
  }'
```

---

### 11.4 API 端点配置规范

#### 11.4.1 核心设计目标

| 目标 | 说明 |
|------|------|
| 配置分离 | 基础域名版本、业务端点分开维护，不硬编码完整 URL |
| 拼接规范 | 无重复斜杠、无重复 /v1，规避 //、/v1/v1 错误 |
| 多服务兼容 | 支持 OpenAI 原生、中转代理、GPT Image2、对话、图像编辑等多种服务 |
| 统一工具 | 代码侧通用拼接工具，统一规则，业务代码无需手动字符串拼接 |
| 可序列化 | 配置可序列化为 JSON/YAML，前后端、配置文件通用 |

#### 11.4.2 术语定义（强制统一命名）

| 字段名 | 说明 | 规范格式 |
|--------|------|----------|
| `base_url` | 服务基础根地址，包含协议 + 域名 + API 版本 /v1 | 结尾禁止带斜杠 `/` |
| `endpoint` | 接口子路径，/v1 之后的资源路径 | 开头禁止带斜杠，全小写、路径用 `/` 分隔 |
| `full_url` | 运行时动态拼接生成完整请求地址 | 业务代码只读，不存入配置 |

**正确示例**：
- `base_url`: `https://api.openai.com/v1`
- `endpoint`: `chat/completions`

**错误示例**：
- `base_url`: `https://api.openai.com/v1/`（结尾带斜杠）
- `endpoint`: `/chat/completions`（开头带斜杠）

#### 11.4.3 拼接规则

```python
# 核心拼接公式
full_url = trimEnd(base_url, "/") + "/" + trimStart(endpoint, "/")

# 统一工具函数
from app.utils.url_utils import join_url

# 使用示例
base_url = "https://api.openai.com/v1"
endpoint = "chat/completions"
full_url = join_url(base_url, endpoint)  # => "https://api.openai.com/v1/chat/completions"
```

**拼接工具函数位置**：`backend/app/utils/url_utils.py`

#### 11.4.4 渠道 API 端点配置标准（推荐方式）

**推荐配置方式：** 使用 `endpoints` 数组 + `body_params` 参数表，无需硬编码请求体结构。

```json
{
  "endpoints": [
    {
      "type": "chat",
      "endpoint": "chat/completions",
      "method": "POST",
      "content_type": "application/json",
      "body_params": [
        {"key": "model", "value_type": "dynamic", "value": "model"},
        {"key": "messages", "value_type": "dynamic", "value": "messages"},
        {"key": "stream", "value_type": "fixed", "value": "true"}
      ]
    },
    {
      "type": "image",
      "endpoint": "images/generations",
      "method": "POST",
      "content_type": "application/json",
      "body_params": [
        {"key": "model", "value_type": "dynamic", "value": "model"},
        {"key": "prompt", "value_type": "dynamic", "value": "prompt"},
        {"key": "n", "value_type": "dynamic", "value": "n"},
        {"key": "size", "value_type": "dynamic", "value": "size"}
      ]
    },
    {
      "type": "image_edits",
      "endpoint": "images/edits",
      "method": "POST",
      "content_type": "multipart/form-data",
      "body_params": [
        {"key": "images[]", "value_type": "image", "value": "images"},
        {"key": "prompt", "value_type": "dynamic", "value": "prompt"},
        {"key": "model", "value_type": "dynamic", "value": "model"}
      ]
    },
    {
      "type": "video",
      "endpoint": "videos/generations",
      "method": "POST",
      "content_type": "application/json",
      "body_params": [
        {"key": "model", "value_type": "dynamic", "value": "model"},
        {"key": "prompt", "value_type": "dynamic", "value": "prompt"},
        {"key": "duration", "value_type": "dynamic", "value": "duration"}
      ]
    }
  ]
}
```

**端点类型枚举**：

| 类型 | 说明 | 触发条件 |
|------|------|---------|
| `text` | 文生文 | 纯文本任务 |
| `chat` | 对话式 | 优先使用，支持多轮对话 |
| `image` | 文生图 | 图片任务，无参考图 |
| `image_edits` | 图生图/图片编辑 | 图片任务，含参考图 |
| `video` | 文生视频 | 视频任务，无参考图 |
| `video_image` | 图生视频 | 视频任务，含参考图 |
| `audio` | 音频生成 | 音频任务 |

**body_params 值类型**：

| value_type | 说明 | value 含义 |
|------------|------|-----------|
| `dynamic` | 业务字段，从任务参数中取值 | 业务字段名，如 `prompt`、`model` |
| `fixed` | 固定值，直接写入请求体 | 固定值文本，如 `true`、`1024x1024` |
| `image` | 图片资源，自动 CDN 化处理 | 图片字段名，如 `images`、`image` |

**响应自动识别**：无需配置响应字段，系统按端点类型自动提取内容（text/choices、image/data、video/data 等）。

#### 11.4.5 兼容旧格式（不推荐）

旧配置仍兼容，仅当未配置 `endpoints` 时生效，自动回退到硬编码逻辑：

```json
{
  "api_config": {
    "text_path": "chat/completions",
    "image_path": "images/generations",
    "image_edits_path": "images/edits",
    "video_path": "videos/generations"
  }
}
```

#### 11.4.6 URL 工具函数 API

| 函数名 | 说明 | 参数 | 返回值 |
|--------|------|------|--------|
| `join_url(base_url, endpoint)` | 拼接 URL，自动消除多余斜杠 | `base_url`: str, `endpoint`: str | 完整 URL |
| `trim_end_slash(value)` | 移除末尾斜杠 | `value`: str | 处理后的字符串 |
| `trim_start_slash(value)` | 移除开头斜杠 | `value`: str | 处理后的字符串 |
| `validate_base_url(base_url)` | 验证 base_url 格式 | `base_url`: str | 错误信息或 None |
| `validate_endpoint(endpoint)` | 验证 endpoint 格式 | `endpoint`: str | 错误信息或 None |

---

### 11.5 渠道 API 调用规范

#### 11.5.1 HTTP 请求标准

所有渠道适配器必须遵循以下 HTTP 调用规范：

```python
async def _http_post(self, url: str, body: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """统一 HTTP POST 请求，带重试和日志"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = None
    max_retries = self.retry_config.get("max_retries", 1)

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=body, headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                # 记录错误日志
                logger.error(f"[{self.trace_id}] HTTP {response.status_code}: {response.text[:500]}")
                
                # 根据状态码抛出具体异常
                if response.status_code == 401:
                    raise Exception(f"401 Unauthorized - API Key 无效")
                elif response.status_code == 429:
                    raise Exception(f"429 Too Many Requests - 超出频率限制")
                elif response.status_code >= 500:
                    raise Exception(f"{response.status_code} Server Error")
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")
                    
        except Exception as e:
            last_error = e
            logger.warning(f"[{self.trace_id}] 请求失败 (attempt {attempt+1}): {e}")
            if attempt < max_retries - 1:
                wait_time = self.retry_config.get("retry_delay", 2)
                time.sleep(wait_time)

    raise last_error or Exception("HTTP 请求失败")
```

#### 11.5.2 错误码映射规范

适配器必须在 `parse_error()` 中将渠道异常映射为统一错误码：

| 渠道异常特征 | 统一错误码 | 用户提示文案 |
|------------|-----------|-------------|
| 401 / Unauthorized / Invalid Key | `channel_error` | 渠道鉴权失败，请检查 API 密钥 |
| 429 / Rate Limit / Quota Exceeded | `service_unavailable` | 模型服务繁忙，请稍后再试 |
| Timeout / Timed Out | `timeout` | 生成超时，请稍后重试 |
| Content Policy / Safety Violation | `content_violation` | 内容不符合规范，请调整提示词 |
| 404 / Not Found | `channel_error` | 模型不存在或已下线 |
| 500 / 502 / 503 / Server Error | `service_unavailable` | 服务暂不可用 |
| 其他未知异常 | `internal_error` | 生成失败: {异常信息前200字符} |

#### 11.5.3 结果解析统一格式

适配器必须在 `parse_result()` 中将渠道响应转换为平台统一格式：

**文本生成**：
```python
{
    "type": "text",
    "text": "生成的文本内容",
    "choices": [...],  # 原始 choices 数组（可选）
    "usage": {...}     # Token 用量统计（可选）
}
```

**图像生成**：
```python
{
    "type": "image",
    "images": [
        {
            "url": "https://cdn.example.com/image.png",
            "revised_prompt": "优化后的提示词"  # 可选
        }
    ],
    "count": 1
}
```

**视频生成**：
```python
{
    "type": "video",
    "videos": [
        {
            "url": "https://cdn.example.com/video.mp4",
            "revised_prompt": "优化后的提示词"  # 可选
        }
    ],
    "count": 1
}
```

---

### 11.6 已实现渠道清单

#### WeeLink 渠道（聚合平台）

| 项目 | 说明 |
|------|------|
| **适配器文件** | `backend/app/adapters/weelinking.py` |
| **支持分类** | text / image / video |
| **API 兼容** | OpenAI 兼容格式 |
| **流式支持** | ✅ 文本支持 SSE 流式响应 |
| **认证方式** | Bearer Token (`Authorization: Bearer {api_key}`) |
| **关键特性** | - body_params 配置化构建请求体<br>- 支持 multipart/form-data（图生图）<br>- 端点按 type 路由，响应自动识别 |
| **配置示例** | ```json<br>{<br>  "channel_code": "weelink_text",<br>  "channel_name": "WeeLink 文本模型",<br>  "channel_provider": "weelinking",<br>  "base_url": "https://api.weelink.ai/v1",<br>  "auth_config": {"api_key": "encrypted_key"},<br>  "endpoints": [<br>    {<br>      "type": "chat",<br>      "endpoint": "chat/completions",<br>      "method": "POST",<br>      "content_type": "application/json",<br>      "body_params": [<br>        {"key": "model", "value_type": "dynamic", "value": "model"},<br>        {"key": "messages", "value_type": "dynamic", "value": "messages"},<br>        {"key": "stream", "value_type": "fixed", "value": "true"}<br>      ]<br>    }<br>  ],<br>  "retry_config": {"timeout": 60, "max_retries": 3, "retry_delay": 2},<br>  "rate_limit_config": {"requests_per_minute": 60},<br>  "status": "active"<br>}<br>``` |

#### Volcengine 渠道（平台直连）

| 项目 | 说明 |
|------|------|
| **适配器文件** | `backend/app/adapters/volcengine.py` |
| **渠道类型** | `direct`（平台直连模式） |
| **支持分类** | video（主要）/ text / image |
| **API 格式** | 异步任务模式（创建任务 + 轮询状态） |
| **流式支持** | ❌ 不支持流式 |
| **认证方式** | Bearer Token |
| **关键特性** | - 视频生成使用异步任务模式<br>- 自动轮询任务状态（默认 60 次，间隔 5 秒）<br>- 支持多图/多视频/多音频参考输入<br>- **直连火山引擎官方 API，非聚合平台中转** |
| **content 参数规范** | `content` 数组中每个非文本元素必须包含 `role` 字段：<br>- `image_url` 类型 → `role: "reference_image"`<br>- `video_url` 类型 → `role: "reference_video"`<br>- `audio_url` 类型 → `role: "reference_audio"` |
| **配置示例** | ```json<br>{<br>  "channel_code": "volcengine_video",<br>  "channel_name": "火山引擎视频生成",<br>  "channel_type": "direct",<br>  "channel_provider": "volcengine",<br>  "base_url": "https://ark.cn-beijing.volces.com",<br>  "auth_config": {"api_key": "encrypted_key"},<br>  "endpoints": [<br>    {<br>      "type": "video",<br>      "endpoint": "api/v3/contents/generations/tasks",<br>      "method": "POST",<br>      "content_type": "application/json",<br>      "body_params": [<br>        {"key": "model", "value_type": "dynamic", "value": "model"},<br>        {"key": "prompt", "value_type": "dynamic", "value": "prompt"}<br>      ]<br>    }<br>  ],<br>  "retry_config": {<br>    "timeout": 120,<br>    "poll_interval": 5,<br>    "max_poll_attempts": 60<br>  },<br>  "status": "active"<br>}<br>``` |
| **迁移说明** | 旧版渠道配置中 `channel_type: "volcengine"` 仍兼容，但建议改为 `"direct"` 以符合规范。系统会在日志中输出警告提示。<br><br>**迁移步骤**：<br>1. 执行迁移脚本：`cd backend && python scripts/migrate_volcengine_to_direct.py`<br>2. 确认迁移（输入 yes）<br>3. 重启后端服务：`python launcher.py restart`<br>4. 验证日志无警告信息 |

---

### 11.7 调试与排查指南

#### 问题 1: 渠道调用返回 "没有可用的渠道绑定"

**排查步骤**：
1. 检查模型的 `channel_bindings` 是否为空
   ```bash
   # MongoDB 查询
   db.models.findOne({model_code: "gpt-5.5"}, {channel_bindings: 1})
   ```
2. 确认绑定的渠道状态为 `"active"`
3. 确认渠道本身状态为 `"active"`
   ```bash
   db.channels.findOne({channel_code: "weelink_text"}, {status: 1})
   ```
4. 检查渠道优先级排序是否正确

#### 问题 2: 渠道鉴权失败（401）

**排查步骤**：
1. 查看后端日志中的 Trace ID
   ```bash
   python launcher.py log backend | grep "trace_xxx"
   ```
2. 确认渠道配置中的 `auth_config.api_key` 已正确加密存储
3. 测试 API Key 是否有效
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://api.weelink.ai/v1/chat/completions \
        -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "hi"}]}'
   ```
4. 如 API Key 过期，在管理界面重新配置

#### 问题 3: 适配器未被调用

**排查步骤**：
1. 确认 `backend/app/adapters/__init__.py` 中已注册新适配器
2. 检查 `create_adapter()` 函数的判断逻辑是否匹配 `channel_code` 或 `channel_type`
3. 查看日志中是否有 `未找到适配的渠道适配器` 警告
4. 重启后端服务使注册生效
   ```bash
   python launcher.py restart
   ```

#### 问题 4: 参数转换错误

**排查步骤**：
1. 在适配器的 `convert_params()` 方法中添加日志
   ```python
   logger.info(f"[{self.trace_id}] 原始参数: {params}")
   logger.info(f"[{self.trace_id}] 转换后参数: {channel_params}")
   ```
2. 对比渠道 API 文档，确认参数格式是否正确
3. 检查必填参数是否遗漏
4. 使用测试脚本单独验证参数转换逻辑

---

### 11.8 交付验收清单

新增渠道或模型后，必须完成以下验收项：

- [ ] 适配器文件已创建并实现所有抽象方法
- [ ] 适配器已在 `__init__.py` 中注册
- [ ] 渠道配置已写入 MongoDB（或通过管理界面创建）
- [ ] API Key 已正确配置（加密存储）
- [ ] 模型 `param_schema` 已定义且字段类型正确
- [ ] 模型 `channel_bindings` 已配置至少一个 active 渠道
- [ ] 单元测试脚本已编写并通过
- [ ] 端到端生成测试成功（前端 → 后端 → 渠道 → 返回结果）
- [ ] 错误场景已测试（401、429、超时等）
- [ ] agent.md 已更新（新增渠道记录、配置示例）
- [ ] 日志输出清晰，包含 Trace ID 便于排查

---

## 十二、当前已知问题与技术债（2026-06-17）

> 以代码审查为准，按优先级排列。修复状态随版本迭代更新。

### 12.1 P0 — 影响核心生图/生视频

| # | 问题 | 现象 | 根因（代码层） | 建议 |
|---|------|------|---------------|------|
| 1 | **同步 generate 阻塞** | 生图/视频请求长时间无响应，前端像「没返回」 | `POST /api/tasks/generate` 在单请求内同步等待渠道完成（含视频轮询最长约 20min） | 改为异步任务队列 + 轮询/WebSocket；或前端已用 30min 超时但仍体验差 |
| 2 | **chat 端点抢占路由** | 图生图走了 chat 而非 image_edits | `_determine_endpoint_type` 若渠道配了 `chat` 端点则**所有任务**走 chat | 仅 text 类任务优先 chat；image/video 应按参考图路由 |
| 3 | **双套适配逻辑并存** | 同一渠道行为不一致 | `endpoints`+ConfigEngine 与 `weelinking.py` 内置 `_call_*_api` 两套路径 | 统一为 ConfigEngine 或明确何时 fallback |
| 4 | **GitHub 存储未启用** | 上传成功但无 CDN / 生图报 validation_error | `storage_service.enabled=false` 时上传应失败，历史数据可能有非 CDN URL | 启动时强校验 GITHUB_TOKEN；管理端展示存储状态 |

### 12.2 P1 — 功能完整性 / 一致性

| # | 问题 | 说明 |
|---|------|------|
| 5 | **API Key 明文存储** | `channel_service` 内部/管理端返回明文；Fernet 仅迁移脚本使用，与文档旧描述不一致 |
| 6 | **userId 默认值** | `generation.ts` 默认 `userId: 'default_user'`，多用户隔离未完全落地 |
| 7 | **JWT 与部分接口** | 部分 user API 可能未强制鉴权，需核对 `middleware.py` 白名单 |
| 8 | **生成结果 CDN** | 渠道返回 `b64_json` 时 `_upload_base64_image` 失败会 fallback 为 data URL，与「全链路 CDN」目标冲突 |
| 9 | **Volcengine 默认适配器** | `channel_type=direct` 默认走 VolcengineAdapter，非火山渠道易误路由 |
| 10 | **任务列表双入口** | `ComposerArea` 乐观 UI + `Workspace` 会话加载，曾出现顺序覆盖（见 `FIX_AI_CHAT_ORDER.md`，已部分修复） |

### 12.3 P2 — 体验与运维

| # | 问题 | 说明 |
|---|------|------|
| 11 | **错误信息截断** | `parse_error` 仅保留 200 字符，TaskAdmin 排查困难 |
| 12 | **MongoDB 文档膨胀** | `task_service._truncate_large_data` 截断 channel_response，极端情况仍可能触 16MB 限制 |
| 13 | **Redis 未深度使用** | 已初始化但限流/队列未接入网关 |
| 14 | **测试与脚本分散** | `backend/tests/` 与 `backend/scripts/` 大量手工脚本，缺 CI 集成 |
| 15 | **agent.md 与 PROTOCOL_SPEC.md** | 两处协议说明需保持同步（gpt-image-2 字段以 PROTOCOL_SPEC 为准） |

### 12.4 已修复 / 已落地（v1.1）

| 项 | 说明 |
|----|------|
| CDN 全链路 | `cdnUrl.ts` + `cdn.py` + 上传校验 + 适配器 `require_cdn_url` |
| gpt-image-2 请求体精简 | 移除默认 `response_format`/`thinking`/`stream` 等多余字段 |
| 会话任务排序 | `Workspace` 首次加载标记，避免覆盖乐观任务 |
| 渠道 endpoints 配置化 | ConfigEngine + ChannelAdmin cURL 导入 |
| Volcengine 视频恢复 | `external_task_id` + `recover` 接口 |

### 12.5 排查生图失败快速路径

```
1. TaskAdmin 查看 task_id → error_message / channel_request / channel_response
2. 后端日志 grep trace_id 或 task_id
3. 确认 channel_request.http_request.body 中 image 是否为 CDN 短 URL
4. 确认 endpoint_type 是否为 image_edits（有参考图时）
5. curl 渠道 base_url + api_key 独立验证连通性
6. python launcher.py status && python launcher.py log backend
```

---

*文档结束 - AIGC Platform Agent v1.1（代码基准 2026-06-17）*
