# 可米幻工坊

**专业短视频 AI 创作工作室** — 面向短剧、漫剧、MV 与营销内容的端到端生产平台。

可米幻工坊将多模型生成能力、可视化工作流与智能创作助手整合于同一工作台：运营侧可灵活接入渠道与模型，创作侧可在对话、画布与 Agent 协作中完成从创意到成片素材的全流程产出。

---

## 产品能力总览

| 模块 | 路径 | 适用角色 | 核心价值 |
|------|------|----------|----------|
| 创作工作台 | `/` | 创作者 | 文 / 图 / 视频一站式生成，对话式交互与参数动态表单 |
| 创作助手 | `/drama` | 编剧 / 导演 | 阶段化智能体：脑暴 → 剧本 → 分镜 → 角色 → 场景 → 生产 |
| 无限画布 | `/canvas` | 视觉创作者 | 节点化工作流，串联生文、生图、生视频与资源标记 |
| 我的空间 | `/my-space` | 创作者 | 统一管理助手对话线程与画布项目 |
| 风格广场 | `/styles` | 创作者 / 运营 | 可视化风格预设，绑定模型协议与提示词模板 |
| 资源仓库 | `/assets` | 创作者 | 上传素材、管理生成结果，全链路 CDN 校验 |
| Prompt 管理 | `/prompts` | 运营 | 版本化提示词模板，支持发布与回滚 |
| Skill 库 | `/skills` | 运营 | Agent 技能注册、草稿发布，与代码库 `skills/` 同步对比 |
| 知识库 | `/knowledge` | 运营 | 分类知识条目，供创作助手检索注入 |
| 系统管理 | `/admin/*` | 运维 / 运营 | 模型、渠道、任务、链路、协议画像与接入工单 |

---

## 核心功能

### 创作工作台

面向日常 AIGC 生产的统一入口，覆盖文本对话、图像生成与视频生成三类能力。

- **多模态分类**：按文本 / 图像 / 视频 Tab 切换，模型列表支持搜索、标签筛选与管理员排序
- **动态参数表单**：依据模型 `param_schema` 自动渲染控件（文本域、滑块、选择器、开关、参考图上传等）
- **对话式生产**：用户消息与 AI 回复流式展示，支持重新编辑、重新生成与历史会话恢复
- **结果处置**：文本复制、图片预览与下载、视频播放；生成资源自动入库并可推送 CDN
- **长任务支持**：视频类任务支持外部轮询、状态同步与中断恢复（`external_task_id` 持久化）

### 创作助手（Super Creative Agent）

以对话驱动的短剧创作智能体，覆盖从灵感发散到结构化产出的完整链路。

- **阶段化创作流程**：创意脑暴 → 剧本 → 分镜 → 角色定妆 → 场景 → 生产出图，支持按用户意图自动推断阶段切换
- **多种创作模式**：创意短剧、AIGC 漫剧、MV、营销广告等模式，对应不同 Skill 链与阶段权重
- **线程级记忆**：MongoDB 持久化对话历史、项目确认快照与风格锁定，支持多轮连续创作
- **能力增强**：集成 Skill 调用、知识库检索、风格库解析、用户 @ 资源引用与过程追踪（Process Trace）
- **画布联动**：对话中可将角色卡、分镜等结构化产出推送到无限画布节点；画布右下角亦可唤起嵌入式 Agent 面板
- **运行可观测**：每次对话写入任务与链路日志，可在运行记录中追溯模型调用与失败原因

脑暴阶段输出规范为 **Markdown 四段式**（剧本草稿 / 选题方向 / 创作主题 / 表现形式），避免 JSON 结构直接外露，提升可读性。

### 无限画布

基于 `@xyflow/react` 的可视化创作工作区，将资源、文本、图像、视频抽象为可连线节点。

- **节点类型**：资源（上传图/视频）、文本、图像、视频、标题、分组；上下游连线自动注入参数
- **节点运行**：单节点或子图执行生文 / 生图 / 生视频，运行态实时展示，支持运行记录抽屉查询历史
- **资源标记**：上传图支持画笔、形状、文字等标记编辑，合并导出后上传 CDN，可反复再编辑
- **交互体验**：Space + 拖拽框选、Ctrl 多选、复制粘贴、连线流动动画；模型选择器与配置面板适配站点主题
- **创作助手嵌入**：画布工作区右下角 FAB 展开右侧 Agent 面板，与当前 `canvas_project_id` 绑定，宽度可拖拽调节

### 我的空间

创作者个人工作台，集中管理两类核心资产：

- **助手对话**：按线程列出创作助手会话，支持搜索、继续对话与删除
- **画布项目**：列出无限画布项目，快速进入编辑或清理废弃草稿

### 风格广场与风格管理

- **风格广场**（`/styles`）：宫格浏览、创建与编辑风格预设；每条风格包含封面、描述、`model_protocol` 协议与分层提示词
- **风格管理**（`/admin/drama/styles`）：运营侧维护 `drama_style_presets` 种子数据，支持批量导入脚本

风格在创作助手与画布节点中均可选用，贯穿角色定妆与生产出图环节，保证视觉一致性。

### 资源仓库与 Prompt / Skill / 知识库

| 能力 | 说明 |
|------|------|
| **资源仓库** | 上传图片/视频至 GitHub 仓库，经 jsDelivr 镜像分发；前后端统一 CDN 白名单校验 |
| **Prompt 管理** | 提示词模板版本化管理，支持草稿、发布、回滚 |
| **Skill 库** | 在线 Skill 与 `skills/` 代码库双向同步；列表展示「有更新」Tag，提示运营拉取发布 |
| **知识库** | 按分类维护 Markdown 知识条目，创作助手按阶段与模式自动检索注入上下文 |

### 系统管理（运营后台）

面向平台运维与模型接入人员的完整管控面：

| 功能 | 说明 |
|------|------|
| **模型管理** | `param_schema`、渠道绑定、`mode_profiles` 多模态路由配置 |
| **渠道管理** | 端点配置、`body_params` 入参模板、cURL 导入、联调抽屉 |
| **协议画像** | 内置与自定义 `ProtocolProfile`，统一描述各 invocation 模式的 HTTP 契约 |
| **接入工单** | 新模型 / 渠道一站式接入向导，可导出 Markdown 文档 |
| **任务管理** | 全平台任务监控，支持 `task_id` / `trace_id` 检索与渠道入参出参查看 |
| **链路日志** | 全链路步骤记录，含 `channel_http_request`、渠道尝试与故障切换轨迹 |

---

## 技术架构

### 整体分层

```
┌─────────────────────────────────────────────────────────────┐
│  前端  React 18 + TypeScript + Ant Design + Zustand         │
│  路由：工作台 / 助手 / 画布 / 风格 / 管理后台                  │
└────────────────────────────┬────────────────────────────────┘
                             │ REST API（/api）
┌────────────────────────────▼────────────────────────────────┐
│  后端  FastAPI + Motor（MongoDB 异步驱动）+ Loguru           │
│  服务层：网关 / 任务 / 画布 / 短剧 Agent / 知识 / 风格       │
└────────────────────────────┬────────────────────────────────┘
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
    ┌──────────┐    ┌──────────────┐    ┌─────────────────┐
    │ MongoDB  │    │ GitHub+CDN   │    │ 外部 AI 渠道     │
    │ （必需）  │    │ 素材/结果存储 │    │ Weelink/APIYI/  │
    └──────────┘    └──────────────┘    │ 火山引擎等       │
                                        └─────────────────┘
```

### 模型网关与渠道适配

生成请求统一经 **ModelGateway** 调度，核心链路为：

参数校验 → 解析 `InvocationMode` → 协议画像路由 → 渠道优先级选择 → 适配器执行 → 链路日志落库

已接入适配器：

| 渠道提供方 | 适配器 | 典型能力 |
|-----------|--------|----------|
| `weelinking` | `WeelinkingAdapter` | OpenAI 兼容文本 / 图像 / 视频 |
| `apiyi` | `ApiyiAdapter` | 对话式生图、Images API 双路径 |
| `volcengine` | `VolcengineAdapter` | 视频异步任务（创建 + 轮询） |

新增渠道只需实现 `BaseChannelAdapter` 并在 `adapters/__init__.py` 注册，配合管理后台绑定即可上线。

### 数据与存储

- **主库**：MongoDB（用户、模型、渠道、任务、画布、Agent 线程、风格、Skill、知识库等）
- **KV 缓存**：`kv_service` 基于 MongoDB 实现，无 Redis 依赖
- **文件存储**：可选 GitHub 仓库 + jsDelivr CDN；参考图与生成结果强制 CDN URL，拒绝 `data:` / `blob:` 透传
- **安全**：渠道 API Key Fernet 加密存储，接口返回自动脱敏

### 前端技术栈

- **框架**：React 18 + Vite 5 + TypeScript
- **UI**：Ant Design 5，支持亮/暗主题切换（`SiteThemeProvider`）
- **状态**：Zustand（生成任务、用户信息）
- **画布**：`@xyflow/react` 节点编辑器
- **代理**：开发环境 `/api` 代理至 `localhost:8001`，长任务超时 600s

---

## 快速开始

### 一、环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.10+ | 后端运行时 |
| **Node.js** | 18+ | 前端开发与构建（需加入 PATH） |
| **MongoDB** | 本地部署 | 默认 `mongodb://localhost:27017`，**必须启动** |

### 二、端口与服务规范（固定，禁止自动换端口）

| 端口 | 用途 | 配置位置 |
|------|------|---------|
| **8001** | 后端 FastAPI | `backend/.env` → `APP_PORT`（默认 8001） |
| **3001** | 前端 Vite 开发服 | `frontend/vite.config.ts`（`strictPort: true`） |
| **27017** | MongoDB | 系统服务 / 自行安装 |

**默认访问地址：**

- 前端界面：http://localhost:3001
- 后端 API：http://localhost:8001/api
- 健康检查：http://localhost:8001/api/health
- API 文档：http://localhost:8001/docs

> 端口被占用时服务会**直接报错终止**，不会自动切换到其他端口。请先停止旧进程再启动。

---

### 三、启动前准备（首次使用必做）

按顺序完成以下步骤，后续日常启动可跳过 ①②④。

#### ① 克隆仓库并进入项目根目录

```bash
cd cokey_ai   # 项目根目录，含 launcher.py / start-all.bat
```

#### ② 后端：虚拟环境、依赖与配置

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env        # Windows: copy .env.example .env
```

编辑 `backend/.env`，至少确认：

- `MONGODB_URL` / `MONGODB_DB_NAME` — 与本地 MongoDB 一致
- `WEELINK_API_KEY` — 文本/图像/视频模型调用（或在管理后台配置渠道）
- `GITHUB_TOKEN` / `GITHUB_REPO` — 可选，用于素材与生成结果 CDN 存储

#### ③ 初始化示例数据（可选，首次搭建建议执行）

```bash
# 在 backend/ 目录、虚拟环境已激活
python scripts/seed_data.py
```

写入预置渠道、模型等种子数据。已有数据时请谨慎执行（脚本会清理部分集合）。

#### ④ 前端：安装依赖

```bash
cd frontend
npm install
```

#### ⑤ 确认外部服务已启动

- MongoDB 已运行（`27017` 可连接）
- `node`、`python` 在命令行可用

---

### 四、Windows 启动（推荐）

项目提供 **无黑窗后台启动器** `launcher.py` 与批处理封装，适合日常开发与 Trae/Cursor 等 IDE 环境（子进程脱离沙箱，不会被 IDE 命令结束后一并杀掉）。

#### 方式 A：一键启动（推荐）

| 操作 | 脚本 | 说明 |
|------|------|------|
| **启动全部** | 双击 `start-all.bat` 或 `start_services.pyw` | 后端(8001) + 前端(3001)，无窗口后台运行 |
| **停止全部** | 双击 `stop-all.bat` 或 `stop_services.pyw` | 按 PID / 端口终止进程 |
| **重启全部** | 双击 `restart-all.bat` 或 `restart_services.pyw` | 先 stop 再 start |
| **查看状态** | 双击 `status.bat` | PID、端口、HTTP 健康检查 |
| **查看日志** | `log_backend.bat` / `log_frontend.bat` | 日志末尾摘要 |

`start_services.pyw` / `stop_services.pyw` / `restart_services.pyw` 通过弹窗显示结果，**不弹出黑色 cmd 窗口**。

#### 方式 B：命令行启动器

在项目根目录执行（使用已安装依赖的 Python，建议先激活 `backend/.venv`）：

```bash
python launcher.py start      # 启动后端 + 前端
python launcher.py stop       # 停止全部
python launcher.py restart    # 重启（改代码后常用）
python launcher.py status     # 运行状态
python launcher.py log backend    # 后端日志末尾
python launcher.py log frontend   # 前端日志末尾
python launcher.py log all        # 两端日志
```

**启动流程（`launcher.py start`）：**

```
launcher.py start
  ├── [backend] python -u backend/run_server.py
  │     ├── 工作目录 backend/，PYTHONPATH=backend/
  │     ├── 日志 → .runtime/backend.log，PID → .runtime/backend.pid
  │     └── 健康检查 GET /api/health（超时 15s）
  └── [frontend] node npm-cli.js run dev
        ├── 工作目录 frontend/
        ├── 日志 → .runtime/frontend.log，PID → .runtime/frontend.pid
        └── 健康检查 GET http://127.0.0.1:3001/（超时 45s）
```

#### 方式 C：分窗口调试启动（可看实时日志）

适合排查启动错误，会弹出独立命令行窗口：

| 脚本 | 说明 |
|------|------|
| `start-backend.bat` | 自动创建 `.venv`、安装依赖、复制 `.env`，运行 `run_server.py` |
| `start-frontend.bat` | 自动 `npm install`，运行 `npm run dev` |

---

### 五、跨平台手动启动（macOS / Linux / Windows 通用）

适用于非 Windows 环境，或需要在前台查看日志时。

**终端 1 — 后端：**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
# 按需编辑 .env
python scripts/seed_data.py        # 可选：首次初始化
python run_server.py               # 或: uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**终端 2 — 前端：**

```bash
cd frontend
npm install
npm run dev                        # http://localhost:3001，/api 代理到 8001
```

> `launcher.py` 依赖 Windows 的 `taskkill` / `CREATE_NO_WINDOW`，**完整启停能力以 Windows 为准**；macOS/Linux 请用手动方式或自行管理进程。

---

### 六、验证启动成功

| 检查项 | 地址 | 预期 |
|--------|------|------|
| 后端健康 | http://localhost:8001/api/health | `{"code":"success",...}` |
| API 文档 | http://localhost:8001/docs | Swagger UI |
| 前端页面 | http://localhost:3001 | 登录 / 工作台 |

命令行快速检查：

```bash
python launcher.py status    # Windows
curl http://localhost:8001/api/health
```

---

### 七、常见问题

| 现象 | 处理 |
|------|------|
| 端口 8001/3001 被占用 | 运行 `stop-all.bat` 或 `python launcher.py stop`，再启动 |
| `ModuleNotFoundError: No module named 'app'` | 必须从 `backend/` 启动，或执行 `python run_server.py` |
| 前端 500 / 接口失败 | `python launcher.py log backend` 查后端日志；确认 MongoDB 已启动 |
| IDE 内启动后立刻退出 | 勿在 IDE 沙箱里直接跑长驻进程；用 `start-all.bat` 或 `launcher.py` |
| 首次启动较慢 | `start-backend.bat` / `start-frontend.bat` 会自动装依赖，约 1–3 分钟 |

**运行时文件目录：**

```
.runtime/
├── backend.pid / frontend.pid   # 进程记录
├── backend.log / frontend.log   # 服务 stdout/stderr
```

---

## 项目结构

```
cokey_ai/
├── backend/                              # Python FastAPI 后端
│   ├── app/
│   │   ├── core/                         # 配置、数据库、CDN、协议解析、安全
│   │   ├── adapters/                     # 渠道适配器（weelinking / apiyi / volcengine）
│   │   ├── core/drama/                   # 创作助手：阶段推断、Skill、风格、提示组装
│   │   ├── services/                     # 业务服务（网关、任务、画布、Agent、知识、风格）
│   │   ├── schemas/                      # Pydantic 请求/响应模型
│   │   ├── routers/                      # API 路由（用户端 + 管理端 + 短剧 + 画布）
│   │   └── main.py                       # 应用入口
│   ├── scripts/                          # 种子数据、风格导入、迁移脚本
│   ├── tests/                            # 单元测试
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                             # React + Ant Design 前端
│   ├── src/
│   │   ├── api/                          # API 封装（canvas / drama / knowledge 等）
│   │   ├── pages/                        # 页面（工作台、助手、画布、管理后台）
│   │   ├── components/                   # 通用与画布、助手组件
│   │   ├── store/                        # Zustand 状态
│   │   ├── types/                        # TypeScript 类型定义
│   │   └── utils/                        # CDN、Agent 发送、画布导航等工具
│   ├── package.json
│   └── vite.config.ts
│
├── skills/                               # Skill 代码库（与 Skill 库管理端同步）
├── docs/                                 # 设计文档与迭代记录
│   ├── DRAMA_SUPER_AGENT.md
│   ├── ONBOARDING_SOP.md（接入 SOP）
│   └── iterations/                       # 每日迭代摘要
├── agent.md                              # 技术方案与运维手册（详细版）
├── launcher.py                           # Windows 服务启动器
├── start-all.bat / stop-all.bat          # 一键启停
└── README.md
```

---

## 配置说明

编辑 `backend/.env`：

```env
# MongoDB（必需）
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=aigc_platform

# GitHub 存储（可选，用于素材上传与生成结果 CDN）
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_REPO=owner/repo
GITHUB_BRANCH=main
GITHUB_CDN_PREFIX=https://cdn.jsdmirror.com/gh

# 渠道 API Key（也可在管理后台渠道配置中维护）
WEELINK_API_KEY=your-weelink-api-key

# 安全（生产环境务必更换）
SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_KEY=your-32bytes-encryption-key-here!
JWT_SECRET_KEY=your-jwt-secret-key-must-be-at-least-32-characters-long
```

---

## 渠道与模型接入

### 添加新渠道

1. 在 `backend/app/adapters/` 下创建适配器，继承 `BaseChannelAdapter`
2. 在 `backend/app/adapters/__init__.py` 中注册
3. 通过管理后台「渠道管理」或 MongoDB `channels` 集合添加配置
4. 配置 `body_params` 入参模板（推荐 `source` 分离取值来源）

### 添加新模型

1. 管理后台「模型管理」创建模型，或写入 MongoDB `models` 集合
2. 配置 `param_schema.fields` 定义前端动态表单
3. 添加 `channel_bindings`，按需配置 `mode_profiles` 与 `protocol_profile_id`

详细接入流程见 `docs/ONBOARDING_SOP.md` 与 `PROTOCOL_SPEC.md`。

---

## API 文档

启动后端后访问：

- Swagger UI：http://localhost:8001/docs
- ReDoc：http://localhost:8001/redoc

常用接口前缀：

| 前缀 | 说明 |
|------|------|
| `/api/tasks` | 生成任务、状态查询、恢复 |
| `/api/canvas` | 画布项目、节点、运行记录 |
| `/api/drama` | 创作助手线程、消息、风格 |
| `/api/admin` | 模型、渠道、任务、链路日志等管理接口 |

---

## 相关文档

| 文档 | 内容 |
|------|------|
| [`agent.md`](agent.md) | 技术方案、架构细节、排查手册 |
| [`docs/DRAMA_SUPER_AGENT.md`](docs/DRAMA_SUPER_AGENT.md) | 创作助手设计说明 |
| [`docs/ONBOARDING_SOP.md`](docs/ONBOARDING_SOP.md) | 新模型/渠道接入 SOP |
| [`PROTOCOL_SPEC.md`](PROTOCOL_SPEC.md) | 渠道协议与 body_params 规范 |
| [`docs/iterations/`](docs/iterations/) | 每日迭代记录 |

---

## 安全最佳实践

- 渠道 API Key 加密存储，禁止明文返回前端
- 参考图与生成资源强制 CDN URL，前后端白名单一致
- 文件上传校验格式与大小
- 生产环境更换 `SECRET_KEY`、`ENCRYPTION_KEY`、`JWT_SECRET_KEY`
- 用户接口逐步统一 JWT 鉴权（部分历史路由仍在加固中）

---

## 演进方向

| 方向 | 说明 |
|------|------|
| 异步任务架构 | `generate` 长任务改为创建后异步轮询，降低 HTTP 阻塞 |
| Agent 能力扩展 | Skill 链编排、画布批量导出、多剧集项目管理 |
| 知识检索增强 | 向量检索与混合搜索（当前以 MongoDB + 关键词为主） |
| 商业化 | 会员体系、计费与用量统计 |
| 创作工具链 | 局部重绘、视频剪辑、工作流模板市场 |

---

**排查问题时**，优先查看：

- 启动器日志：`.runtime/backend.log`、`.runtime/frontend.log`
- 后端结构化日志：`backend/logs/`
- 链路日志管理端：`/admin/trace-logs`
