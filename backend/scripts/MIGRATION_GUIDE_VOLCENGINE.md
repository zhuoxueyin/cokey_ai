# Volcengine 渠道迁移指南

## 📌 变更概述

将 Volcengine 渠道从独立的 `channel_type: "volcengine"` 改为标准的 `channel_type: "direct"`（平台直连模式）。

### 为什么需要迁移？

1. **统一渠道类型规范**：所有直接连接官方 API 的渠道应使用 `direct` 类型
2. **简化适配器注册逻辑**：避免为每个直连渠道创建独立的类型标识
3. **符合架构设计原则**：`aggregator`（聚合平台）vs `direct`（平台直连）二分法更清晰

---

## 🔄 迁移影响

### ✅ 兼容性保证

- **旧配置仍可用**：`channel_type: "volcengine"` 的渠道仍能正常工作
- **自动日志警告**：系统会在日志中提示建议改为 `direct` 类型
- **零停机迁移**：适配器注册逻辑已兼容两种类型

### ⚠️ 需要注意的场景

| 场景 | 影响 | 处理方式 |
|------|------|---------|
| 新建 Volcengine 渠道 | 必须使用 `channel_type: "direct"` | 按新规范配置即可 |
| 现有 Volcengine 渠道 | 继续工作，但日志有警告 | 执行迁移脚本消除警告 |
| 通过 API 查询渠道 | `channel_type` 字段值变化 | 前端需适配新值 |
| 管理界面编辑渠道 | 下拉选项更新 | 刷新页面后生效 |

---

## 🚀 迁移步骤

### 方式一：自动迁移（推荐）

```bash
# 1. 进入 backend 目录
cd backend

# 2. 执行迁移脚本
python scripts/migrate_volcengine_to_direct.py

# 3. 确认迁移（输入 yes）

# 4. 重启后端服务
python launcher.py restart
```

### 方式二：手动迁移

如果数据库中只有少量 Volcengine 渠道，可以手动修改：

```javascript
// MongoDB Shell
db.channels.updateMany(
  { channel_type: "volcengine" },
  { $set: { channel_type: "direct" } }
)
```

或通过管理界面逐个编辑渠道，将类型改为 `direct`。

---

## ✅ 验证清单

迁移完成后，请确认以下项：

- [ ] 执行迁移脚本无错误
- [ ] 后端服务正常启动
- [ ] 日志中无 "检测到旧版 volcengine 渠道类型" 警告
- [ ] Volcengine 渠道生成任务正常
- [ ] 管理界面显示渠道类型为 `direct`

### 快速验证命令

```bash
# 1. 检查后端日志
python launcher.py log backend | grep -i volcengine

# 2. 测试生成任务
curl -X POST http://localhost:8000/api/tasks/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model_code": "your-volcengine-model",
    "category": "video",
    "params": {"prompt": "测试"}
  }'

# 3. 查询渠道列表
curl http://localhost:8000/api/admin/channels | jq '.data[] | select(.channel_code | test("volcengine"))'
```

---

## 🔍 技术细节

### 适配器注册逻辑变更

**修改前**：
```python
if channel_type == "volcengine":
    return VolcengineAdapter(channel_config, trace_id)
```

**修改后**：
```python
# 优先匹配 direct 类型 + volcengine 关键词
if channel_type == "direct" and "volcengine" in channel_code.lower():
    return VolcengineAdapter(channel_config, trace_id)

# 兼容旧配置
if channel_type == "volcengine":
    logger.warning("检测到旧版 volcengine 渠道类型，建议改为 direct 类型")
    return VolcengineAdapter(channel_config, trace_id)
```

### 渠道配置示例对比

**旧配置**（不推荐）：
```json
{
  "channel_code": "volcengine_video",
  "channel_type": "volcengine",  // ❌ 旧类型
  "base_url": "https://ark.cn-beijing.volces.com",
  ...
}
```

**新配置**（推荐）：
```json
{
  "channel_code": "volcengine_video",
  "channel_type": "direct",  // ✅ 标准直连类型
  "base_url": "https://ark.cn-beijing.volces.com",
  ...
}
```

---

## ❓ 常见问题

### Q1: 不迁移会有什么后果？

A: 功能不受影响，但每次调用 Volcengine 渠道时，后端日志会输出警告信息。长期来看，建议完成迁移以保持代码整洁。

### Q2: 迁移后原有的 API Key 会失效吗？

A: 不会。迁移仅修改 `channel_type` 字段，其他配置（包括加密存储的 API Key）保持不变。

### Q3: 如果迁移失败怎么办？

A: 迁移脚本是幂等的，可以多次执行。如果遇到问题：
1. 检查 MongoDB 连接是否正常
2. 查看脚本输出的错误信息
3. 手动回滚：`db.channels.updateMany({channel_type: "direct"}, {$set: {channel_type: "volcengine"}})`

### Q4: 其他直连渠道（如 OpenRouter）也需要迁移吗？

A: 是的，未来新增的任何直连渠道都应使用 `channel_type: "direct"`，并在适配器注册逻辑中添加对应的判断条件。

---

## 📞 技术支持

如遇问题，请提供以下信息：
1. 后端日志（`python launcher.py log backend`）
2. 渠道配置截图
3. 迁移脚本输出内容

---

*最后更新：2026-06-16*
