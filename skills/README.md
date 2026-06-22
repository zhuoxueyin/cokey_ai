# Skill 代码库

每个 Skill 占一个子目录，须满足：

```
skills/
  skill_intake/       # 立项问诊 skill.intake
  skill_concept/      # 创意策划 skill.concept
  skill_character/    # 角色卡 skill.character
  skill_scene/        # 场景设计 skill.scene
  skill_storyboard/   # 分镜 skill.storyboard
  skill_production/   # 生产落地 skill.production
  skill_art_tianshuqitan/  # 示例：风格出图
    SKILL.md      # 标准规范（frontmatter + 八段式 Markdown）
    scripts/      # 关联脚本（必填目录，可仅含 README）
```

`SKILL.md` frontmatter 必填字段：

- `skill_name` / `skill_id` / `version` / `author` / `update_time` / `tag`

正文须包含八个章节：技能简介、适用场景、输入条件、核心执行流程、输出标准、异常兜底、约束禁忌、版本记录。

## 与 Skill 库的关系

- **代码库 `skills/`**：仅用于版本管理、本地编辑、以及通过 Skill 库「从代码库导入」。
- **Skill 库（MongoDB 已发布）**：创作助手运行时**唯一** Skill 来源；未在 Skill 库注册发布的 Skill **不会被加载**。
- 流程：在 `skills/` 编写或更新 → Skill 库导入（或在线新建）→ **发布** → 创作助手可用。
