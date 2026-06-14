# AIGC 创作平台 V1.0

通用 AIGC 创作平台，参考 LiblibAI 模式构建，支持文本/图像/视频三类模型创作，提供管理后台和对话式创作工作台。

## 🚀 快速开始

### 环境要求

- **Python**: 3.10+
- **Node.js**: 18+
- **MongoDB**: 本地部署（默认 `mongodb://localhost:27017`）
- **Redis**: 本地部署（可选，用于限流/缓存）

### 一键启动（Windows）

```bash
# 方式一：一键启动前后端
start-all.bat

# 方式二：分别启动
start-backend.bat      # 后端服务 (http://localhost:8000)
start-frontend.bat     # 前端界面 (http://localhost:3000)
```

### 手动启动（跨平台）

**后端服务:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Windows: copy .env.example .env
# 编辑 .env 配置文件
python scripts/seed_data.py # 初始化示例数据
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**前端界面:**

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

## 📁 项目结构

```
aigc_platform/
├── backend/                         # Python FastAPI 后端
│   ├── app/
│   │   ├── core/                   # 核心配置
│   │   │   ├── config.py           # 全局配置
│   │   │   ├── database.py         # MongoDB 连接
│   │   │   ├── logging_config.py   # 日志配置
│   │   │   ├── redis_client.py     # Redis 连接
│   │   │   ├── security.py         # 加密/脱敏
│   │   │   └── utils.py            # 工具函数
│   │   ├── adapters/               # 渠道适配器层
│   │   │   ├── base.py             # 适配器抽象基类
│   │   │   └── weelinking.py       # Weelink 渠道适配器
│   │   ├── services/               # 业务服务层
│   │   │   ├── gateway_service.py  # 模型网关（路由/校验/限流）
│   │   │   ├── channel_service.py  # 渠道管理
│   │   │   ├── model_service.py    # 模型管理
│   │   │   ├── task_service.py     # 任务管理
│   │   │   ├── session_service.py  # 会话管理
│   │   │   └── storage_service.py  # GitHub + jsDelivr 存储
│   │   ├── schemas/                # Pydantic 数据模型
│   │   │   ├── channel.py
│   │   │   ├── model.py
│   │   │   ├── task.py
│   │   │   └── session.py
│   │   ├── routers/                # API 路由
│   │   │   ├── admin_channels.py   # 后台-渠道管理
│   │   │   ├── admin_models.py     # 后台-模型管理
│   │   │   ├── admin_tasks.py      # 后台-任务监控
│   │   │   ├── user_models.py      # 用户-模型列表
│   │   │   ├── user_tasks.py       # 用户-生成任务
│   │   │   ├── user_sessions.py    # 用户-会话管理
│   │   │   ├── user_upload.py      # 用户-素材上传
│   │   │   └── health.py           # 健康检查
│   │   └── main.py                 # 应用入口
│   ├── scripts/
│   │   └── seed_data.py            # 种子数据初始化
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                        # React + Ant Design 前端
│   ├── src/
│   │   ├── api/                    # API 请求封装
│   │   │   ├── request.ts
│   │   │   └── index.ts
│   │   ├── store/                  # 状态管理 (Zustand)
│   │   │   └── generation.ts
│   │   ├── types/                  # TypeScript 类型
│   │   │   └── index.ts
│   │   ├── pages/                  # 页面
│   │   │   └── Workspace.tsx       # 创作工作台
│   │   ├── components/             # 通用组件
│   │   │   ├── ParamPanel.tsx      # 参数面板
│   │   │   ├── DynamicForm.tsx     # 动态参数表单
│   │   │   └── ChatArea.tsx        # 对话展示区
│   │   ├── main.tsx                # 入口
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── start-all.bat                    # 一键启动
├── start-backend.bat                # 后端启动
├── start-frontend.bat               # 前端启动
└── README.md
```

## ✨ 核心功能

### 1. 管理后台 API

| 功能 | 接口 |
|------|------|
| 渠道增删改查、启停 | `/api/admin/channels/*` |
| 模型增删改查、上下架 | `/api/admin/models/*` |
| 任务列表与详情 | `/api/admin/tasks/*` |
| 调用统计 | `/api/admin/tasks/stats/*` |

### 2. 用户创作工作台

- **三大分类 Tab**: 文本创作 / 图像生成 / 视频生成
- **模型选择器**: 弹窗搜索、标签筛选、默认选中
- **动态参数表单**: 根据模型 `param_schema` 自动渲染控件（支持 textarea/number/slider/select/switch/image_upload）
- **对话式交互**: 用户消息 + AI 回复，支持重新编辑、重新生成
- **结果管理**: 文本复制、图片预览/下载、视频播放、批量下载

### 3. 后端架构亮点

- **适配器模式**: 统一渠道接入抽象，新增渠道仅需实现 `BaseChannelAdapter`
- **模型网关**: 参数校验 → 渠道路由 → 故障自动切换 → 全链路日志
- **GitHub + jsDelivr 存储**: 上传素材和生成结果自动推送到 GitHub，通过 jsDelivr CDN 分发
- **敏感信息加密**: 渠道 API Key 使用 Fernet 加密存储，返回前端自动脱敏

### 4. 预置模型（种子数据）

- **文本**: GPT-3.5 Turbo、GPT-4o Mini
- **图像**: DALL-E 3、SDXL Turbo
- **视频**: Sora 视频生成、Runway Gen-3

## 🔧 配置说明

编辑 `backend/.env` 文件：

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=aigc_platform

# Redis（可选）
REDIS_URL=redis://localhost:6379/0

# GitHub 存储（可选，用于文件上传）
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_USERNAME=your-github-username
GITHUB_REPO=your-storage-repo
GITHUB_BRANCH=main

# 渠道 API Key
# 编辑 MongoDB 中的 channels 文档，修改 auth_config.text_api_key 等字段
```

## 🔌 渠道接入指南

### 添加新渠道

1. 在 `app/adapters/` 下创建新的适配器，继承 `BaseChannelAdapter`
2. 在 `app/adapters/__init__.py` 中注册适配器
3. 通过管理后台 API 或直接在 MongoDB 中添加渠道配置
4. 在模型配置中添加 `channel_bindings` 绑定

### 添加新模型

1. 调用 `POST /api/admin/models` 或在 MongoDB `models` 集合中添加文档
2. 配置 `param_schema.fields` 定义动态参数表单
3. 添加 `channel_bindings` 绑定一个或多个渠道

## 📚 API 文档

启动后端后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔐 安全最佳实践

- 渠道 API Key 加密存储，禁止明文返回
- 文件上传校验格式和大小
- 所有接口做参数校验
- 生产环境修改 `SECRET_KEY` 和 `ENCRYPTION_KEY`

## 🚧 二期规划

- 用户账号/会员/计费系统
- 模型训练 / LoRA 微调
- 工作流编排
- 社区分享 / 评论互动
- 图片局部重绘 / 视频剪辑
- 移动端适配
- LibTV 风格无限画布

---

**如有问题，请查看后端日志 (`backend/logs/`) 进行排查。**
