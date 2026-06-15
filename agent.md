# AIGC 创作平台 - 技术方案与运维手册

> 版本: v1.0.0 | 最后更新: 2026-06-15
> 通用 AIGC 创作平台 - 支持多模型、多渠道的 AI 内容生成系统

---

## 一、项目概述

### 1.1 系统定位

通用 AIGC 创作平台是一个支持多模型、多渠道的 AI 内容生成系统，提供统一的前端界面和后端 API 网关，将不同 AI 服务提供商的能力抽象为一致的调用接口。

### 1.2 核心功能

| 功能模块 | 说明 |
|---------|------|
| 文本生成 | 支持 gpt-5.5 等大语言模型的文本创作 |
| 模型管理 | 管理员界面配置可用模型及其参数 |
| 渠道管理 | 配置不同 AI 服务提供商（如 Weelink） |
| 任务管理 | 查看和管理用户生成任务记录 |
| 文件上传 | 支持图片等资源上传（后端接口） |

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
     ┌──────────┐       ┌──────────┐       ┌──────────┐
     │  MongoDB │       │  Redis   │       │  OpenAI  │
     │ (必需)   │       │ (可选)   │       │  聚合API │
     └──────────┘       └──────────┘       └──────────┘
```

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
│   ├── main.py                 # FastAPI 应用入口，CORS 配置，路由注册
│   ├── routers/                # API 路由层 (RESTful endpoints)
│   │   ├── health.py           # 健康检查 GET /api/health
│   │   ├── user_models.py      # 用户端: 模型列表 / 默认模型 / 详情
│   │   ├── user_tasks.py       # 用户端: 创建任务 / 执行生成 / 查询状态
│   │   ├── user_sessions.py    # 用户端: 会话管理
│   │   ├── user_upload.py      # 用户端: 文件上传
│   │   ├── admin_models.py     # 管理员: 模型 CRUD
│   │   ├── admin_channels.py   # 管理员: 渠道 CRUD
│   │   └── admin_tasks.py      # 管理员: 任务查询 / 统计
│   ├── services/               # 业务服务层
│   │   ├── model_service.py    # 模型管理（含渠道绑定逻辑）
│   │   ├── task_service.py     # 任务生命周期管理
│   │   └── gateway_service.py  # ← 核心: 模型请求路由 / 渠道选择 / 执行网关
│   ├── adapters/               # 渠道适配器层
│   │   ├── base.py             # 抽象基类 BaseChannelAdapter
│   │   └── weelinking.py       # Weelink 渠道: OpenAI 兼容 API 调用
│   ├── schemas/                # Pydantic 请求/响应模型
│   └── core/                   # 基础设施
│       ├── config.py           # 环境变量配置（.env → Settings）
│       ├── database.py         # MongoDB 连接 (Motor 异步驱动)
│       ├── redis_client.py     # Redis 连接（可选依赖）
│       ├── response.py         # 统一响应格式 {code, message, data}
│       ├── logging_config.py   # Loguru 日志配置
│       ├── security.py         # Fernet 加密（API Key 存储加密）
│       └── utils.py            # 工具函数
```

### 3.2 模型网关 (Model Gateway) - 核心机制

**文件**: `backend/app/services/gateway_service.py`

#### 职责
1. 接收模型执行请求（model_code + category + params）
2. 从 MongoDB 查找模型配置，验证模型状态
3. **选择最优渠道**: 按 `priority` 排序，选择第一个 `active` 的渠道绑定
4. 创建渠道适配器，调用渠道 API
5. 主渠道失败时，自动切换到备用渠道
6. 统一返回格式

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

1. **流式响应强制启用**: `stream=True`
   - Weelink 的 gpt-5.5 模型要求必须使用流式调用
   - 非流式请求会被上游拒绝（返回 400 bad_response_status_code）

2. **SSE 解析**:
   ```python
   # 收集 SSE (Server-Sent Events) 数据流
   full_text = ""
   async for chunk in await client.chat.completions.create(model=..., messages=..., stream=True):
       if chunk.choices and chunk.choices[0].delta.content:
           full_text += chunk.choices[0].delta.content
   # 最终组装成标准的 chat.completion 响应格式返回
   ```

3. **参数转换**:
   - 前端 params.prompt → 构造成 messages=[{role:"user", content:prompt}]
   - 支持 temperature、max_tokens、seed 等参数透传

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
| POST | `/api/tasks/generate` | **核心**: 立即执行生成（前端主要调用此接口） |
| POST | `/api/tasks` | 创建任务记录（不执行） |
| POST | `/api/tasks/{task_id}/execute` | 执行已创建的任务 |
| GET | `/api/tasks/{task_id}` | 查询任务状态 |
| GET | `/api/tasks/session/{session_id}` | 会话下的任务列表 |

#### 用户端 - 其他
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/sessions` | 创建会话 |
| POST | `/api/upload` | 文件上传（multipart/form-data） |

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

### 3.7 安全机制 - API Key 加密存储

**文件**: `backend/app/core/security.py`

渠道配置中的 API Key **不以明文**存储在 MongoDB，而是使用 `cryptography.Fernet` 对称加密：

```
存储前: Fernet.encrypt(plaintext_api_key.encode()) → bytes (base64 字符串)
读取时: Fernet.decrypt(stored_ciphertext.encode()) → 原始 API Key
```

加密密钥从环境变量 `SECRET_KEY` 读取（默认值在 `config.py` 中，生产环境需覆盖）。

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
│   ├── components/
│   │   └── ParamPanel.tsx       # 参数面板（模型选择 + prompt 输入 + 图片上传）
│   ├── pages/
│   │   ├── ModelAdmin.tsx       # 模型管理页面（含渠道绑定编辑）
│   │   ├── ChannelAdmin.tsx     # 渠道管理页面
│   │   └── TaskAdmin.tsx        # 任务管理页面
│   ├── services/
│   │   └── api.ts              # Axios 封装（baseURL=/api）
│   └── App.tsx
├── vite.config.ts               # Vite 配置（端口 3001 + API 代理到 8000）
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

#### `tasks` - 任务记录

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务唯一 ID |
| `session_id` | string | 会话 ID |
| `model_code` | string | 使用的模型 |
| `category` | string | 分类 |
| `params` | object | 用户输入参数 |
| `status` | string | `"pending"` / `"processing"` / `"success"` / `"failed"` |
| `result` | object | 生成结果 |
| `error_message` | string | 失败原因 |
| `channel_code` | string | 实际使用的渠道 |
| `duration_ms` | number | 耗时（毫秒） |
| `created_at` | datetime | 创建时间 |

#### `sessions` - 会话记录

| 字段 | 类型 | 说明 |
|------|------|------|
| `session_id` | string | 会话 ID |
| `category` | string | 分类 |
| `created_at` | datetime | 创建时间 |

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

*文档结束 - AIGC Platform Agent v1.0*
