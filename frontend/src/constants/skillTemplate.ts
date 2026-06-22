/** Skill 标准 SKILL.md 空模板（与 backend skill_spec_template 对齐） */
export function buildSkillContentTemplate(opts?: {
  skillName?: string
  skillId?: string
  author?: string
  tag?: string
}): string {
  const skillName = opts?.skillName || '技能名称'
  const skillId = opts?.skillId || 'skill.example'
  const author = opts?.author || 'xxx'
  const tag = opts?.tag || '标签'
  const today = new Date().toISOString().slice(0, 10)

  return `---
skill_name: ${skillName}
skill_id: ${skillId}
version: 1.0.0
author: ${author}
update_time: ${today}
tag: ${tag}
---

# 一、技能简介
（一段话描述技能目标与产出标准）

# 二、适用场景
1. 适用场景一
2. 适用场景二
不适用场景：xxx

# 三、输入条件
1. 输入项一
2. 输入项二

# 四、核心执行流程
1. 步骤一
2. 步骤二
3. 步骤三

# 五、输出标准
1. 输出标准一
2. 输出标准二

# 六、异常兜底
1. 异常情况及处理方式

# 七、约束禁忌
禁止 xxx

# 八、版本记录
| 版本 | 更新时间 | 更新内容 | 更新人 |
| ---- | -------- | -------- | ------ |
| 1.0.0 | ${today} | 首次定稿 | ${author} |
`
}
