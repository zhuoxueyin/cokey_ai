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

### 11.4 渠道 API 调用规范

#### 11.4.1 HTTP 请求标准

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

#### 11.4.2 错误码映射规范

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

#### 11.4.3 结果解析统一格式

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

### 11.5 已实现渠道清单

#### Weelink 渠道（聚合平台）

| 项目 | 说明 |
|------|------|
| **适配器文件** | `backend/app/adapters/weelinking.py` |
| **支持分类** | text / image / video |
| **API 兼容** | OpenAI 兼容格式 |
| **流式支持** | ✅ 文本支持 SSE 流式响应 |
| **认证方式** | Bearer Token (`Authorization: Bearer {api_key}`) |
| **关键特性** | - 文本生成强制启用 `stream=True`<br>- 支持多张图片输入（vision）<br>- 自动收集 SSE 数据流组装完整响应 |
| **配置示例** | ```json<br>{<br>  "channel_code": "weelink_text",<br>  "base_url": "https://api.weelink.ai/v1",<br>  "auth_config": {"api_key": "encrypted_key"},<br>  "api_config": {<br>    "text_path": "/chat/completions",<br>    "image_path": "/images/generations",<br>    "video_path": "/videos/generations",<br>    "text_stream": true<br>  }<br>}<br>``` |

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
| **配置示例** | ```json<br>{<br>  "channel_code": "volcengine_video",<br>  "channel_name": "火山引擎视频生成",<br>  "channel_type": "direct",<br>  "base_url": "https://ark.cn-beijing.volces.com",<br>  "auth_config": {"api_key": "encrypted_key"},<br>  "api_config": {<br>    "video_path": "/api/v3/contents/generations/tasks",<br>    "text_stream": false<br>  },<br>  "retry_config": {<br>    "timeout": 120,<br>    "poll_interval": 5,<br>    "max_poll_attempts": 60<br>  }<br>}<br>``` |
| **迁移说明** | 旧版渠道配置中 `channel_type: "volcengine"` 仍兼容，但建议改为 `"direct"` 以符合规范。系统会在日志中输出警告提示。<br><br>**迁移步骤**：<br>1. 执行迁移脚本：`cd backend && python scripts/migrate_volcengine_to_direct.py`<br>2. 确认迁移（输入 yes）<br>3. 重启后端服务：`python launcher.py restart`<br>4. 验证日志无警告信息 |

---

### 11.6 调试与排查指南

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

### 11.7 交付验收清单

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

*文档结束 - AIGC Platform Agent v1.0*
