"""创作助手主链路：阶段 · Skill 串联 · 意图识别 · 下一步引导。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.core.drama.skill_registry import STAGE_SKILL_MAP, STAGES_WITHOUT_SKILL

# 创作助手主链路（与 Skill 库 stage 映射一致）
PIPELINE_STAGES: List[Dict[str, str]] = [
    {"stage": "concept", "label": "创意脑暴", "skill_code": "skill.concept", "goal": "故事方向与 Brief"},
    {"stage": "outline", "label": "大纲", "skill_code": "skill.concept", "goal": "剧集结构与集数弧光"},
    {"stage": "script", "label": "剧本", "skill_code": "skill.script", "goal": "对白与场次脚本"},
    {"stage": "character", "label": "角色", "skill_code": "skill.character", "goal": "角色设计 → 定妆图 → 角色卡"},
    {"stage": "scene", "label": "场景", "skill_code": "skill.scene", "goal": "场景卡与空间氛围"},
    {"stage": "storyboard", "label": "分镜", "skill_code": "skill.storyboard", "goal": "镜头表与分镜描述"},
    {"stage": "production", "label": "生产", "skill_code": "skill.production", "goal": "章节化·格位 prompt 包 → 画布出图/出视频"},
]

STAGE_LABELS_ZH: Dict[str, str] = {s["stage"]: s["label"] for s in PIPELINE_STAGES}
STAGE_LABELS_ZH["init"] = "立项"

_STAGE_RULES: List[Tuple[str, List[str]]] = [
    (
        "character",
        [
            r"角色图",
            r"角色设计",
            r"角色卡",
            r"定妆",
            r"人物设计",
            r"角色设定",
            r"设计角色",
            r"给.{0,16}设计.{0,8}角色",
            r"按流程引导",
            r"角色.{0,6}流程",
            r"character\s*design",
        ],
    ),
    ("storyboard", [r"分镜", r"镜头表", r"storyboard"]),
    ("scene", [r"场景设计", r"场景卡", r"设计场景", r"场景设定"]),
    ("script", [r"写剧本", r"撰写剧本", r"剧本创作", r"对白"]),
    ("outline", [r"大纲", r"剧集大纲"]),
    ("concept", [r"创意脑暴", r"故事方向", r"脑暴", r"brief", r"logline"]),
    ("production", [r"一键出图", r"画布出图", r"开始出图", r"直接出图", r"生成图片", r"生成视频"]),
]

_EXPLICIT_STAGE_RE = re.compile(
    r"(?:进入|切换到|切到|改成|设为)?\s*(创意|大纲|剧本|角色|场景|分镜|生产)\s*阶段"
)
_SUBJECT_PATTERNS = [
    re.compile(r"给[「\"]?([\u4e00-\u9fff·]{2,8}?)[」\"]?(?:设计|出|的|做|画|生成)"),
    re.compile(r"给[「\"]?([\u4e00-\u9fff·]{2,8})[」\"]?"),
    re.compile(r"[「\"]([\u4e00-\u9fff·]{2,8})[」\"]的(?:角色|人设)"),
    re.compile(r"(?:角色|人物)[「\"]?([\u4e00-\u9fff·]{2,8})[」\"]?"),
]
_REFINE_RE = re.compile(
    r"(更[\u4e00-\u9fff]{1,8}一点|加强.+?(?:感|气|味)|强化.+?(?:感|气|味)|"
    r"不要太.+|再.+?一点|偏向.+|走.+?风)"
)
_CONFIRM_RE = re.compile(r"(确认|就这样|可以了|继续产出|定稿|OK|好的)", re.I)
_PIPELINE_ADVANCE_RE = re.compile(
    r"(进入主链路下一环|主链路下一环|进入下一环节|进入下一阶段|"
    r"进入下一环|完成本阶段|本阶段完成|阶段完成|"
    r"进入场景(?:设计|阶段)|进入分镜(?:阶段)?|进入剧本(?:阶段)?|进入大纲(?:阶段)?)",
    re.I,
)
_ADVANCE_RE = re.compile(
    r"(下一步|进入.{0,4}阶段|接着做|继续.{0,4}(?:大纲|剧本|分镜|场景))"
)


@dataclass
class AgentCreationIntent:
    target_stage: Optional[str] = None
    stay_stage: bool = True
    intent_type: str = "continue"  # continue | stage_switch | refine | confirm | advance
    subject: str = ""
    character_substep: str = ""
    refinement_hint: str = ""
    matched_patterns: List[str] = field(default_factory=list)
    skill_code: str = ""
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_stage": self.target_stage,
            "intent_type": self.intent_type,
            "subject": self.subject,
            "character_substep": self.character_substep,
            "refinement_hint": self.refinement_hint,
            "skill_code": self.skill_code,
            "reason": self.reason,
        }


def _match_stage(text: str) -> Tuple[Optional[str], List[str]]:
    explicit = _EXPLICIT_STAGE_RE.search(text)
    if explicit:
        mapping = {
            "创意": "concept",
            "大纲": "outline",
            "剧本": "script",
            "角色": "character",
            "场景": "scene",
            "分镜": "storyboard",
            "生产": "production",
        }
        label = explicit.group(1)
        if label in mapping:
            return mapping[label], [f"explicit:{label}"]
    for stage, patterns in _STAGE_RULES:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                return stage, [pat]
    return None, []


def extract_subject(text: str) -> str:
    for pat in _SUBJECT_PATTERNS:
        m = pat.search(text)
        if m:
            name = (m.group(1) or "").strip("· ")
            if name and len(name) <= 8:
                return name
    return ""


def extract_refinement(text: str) -> str:
    m = _REFINE_RE.search(text)
    return (m.group(0) or "").strip() if m else ""


def infer_stage_from_message(message: str, current_stage: str = "concept") -> Optional[str]:
    """兼容旧接口：仅返回需切换的目标阶段。"""
    intent = analyze_creation_intent(message, current_stage)
    if intent.target_stage and intent.target_stage != current_stage:
        return intent.target_stage
    return None


def stage_switch_reason(message: str, from_stage: str, to_stage: str) -> str:
    from_label = STAGE_LABELS_ZH.get(from_stage, from_stage)
    to_label = STAGE_LABELS_ZH.get(to_stage, to_stage)
    skill = STAGE_SKILL_MAP.get(to_stage, "")
    skill_part = f"，加载 {skill}" if skill else ""
    return f"检测到「{message[:40]}…」与当前阶段「{from_label}」不匹配，已切换到「{to_label}」{skill_part}。"


def next_pipeline_stage(current_stage: str) -> Optional[str]:
    idx = pipeline_index(current_stage)
    if idx < 0 or idx + 1 >= len(PIPELINE_STAGES):
        return None
    return PIPELINE_STAGES[idx + 1]["stage"]


def analyze_creation_intent(message: str, current_stage: str = "concept") -> AgentCreationIntent:
    text = (message or "").strip()
    intent = AgentCreationIntent()
    if not text:
        intent.reason = "空消息"
        return intent

    matched_stage, patterns = _match_stage(text)
    intent.matched_patterns = patterns
    intent.subject = extract_subject(text)
    intent.refinement_hint = extract_refinement(text)

    # 用户明确要求进入主链路下一环 / 下一阶段 → 切到 pipeline 下一 stage
    if _PIPELINE_ADVANCE_RE.search(text):
        nxt = next_pipeline_stage(current_stage)
        if nxt and nxt != current_stage:
            intent.intent_type = "stage_switch"
            intent.target_stage = nxt
            intent.stay_stage = False
            stage_for_skill = nxt
            intent.skill_code = STAGE_SKILL_MAP.get(stage_for_skill, "")
            intent.reason = (
                f"类型=stage_switch · 主链路推进 → "
                f"{STAGE_LABELS_ZH.get(nxt, nxt)}（自 {STAGE_LABELS_ZH.get(current_stage, current_stage)}）"
            )
            return intent

    if _CONFIRM_RE.search(text):
        intent.intent_type = "confirm"
    elif intent.refinement_hint and not matched_stage:
        intent.intent_type = "refine"
    elif _ADVANCE_RE.search(text):
        intent.intent_type = "advance"
    elif matched_stage and matched_stage != current_stage:
        intent.intent_type = "stage_switch"
        intent.target_stage = matched_stage
    elif matched_stage:
        intent.intent_type = "continue"
        intent.target_stage = matched_stage
    else:
        intent.intent_type = "continue"

    # 弱「出图」信号不打断创作 Skill 阶段
    if (
        matched_stage == "production"
        and current_stage not in ("production",)
        and current_stage in ("concept", "outline", "script", "character", "scene", "storyboard")
    ):
        intent.target_stage = current_stage
        intent.intent_type = "continue"
        intent.stay_stage = True

    # production 下谈创作流程 → 切 Skill 阶段
    if current_stage == "production" and matched_stage and matched_stage != "production":
        intent.intent_type = "stage_switch"
        intent.target_stage = matched_stage
        intent.stay_stage = False

    if intent.target_stage is None and intent.intent_type in ("continue", "refine", "confirm", "advance"):
        intent.target_stage = current_stage
        intent.stay_stage = True
    elif intent.target_stage and intent.target_stage != current_stage:
        intent.stay_stage = False

    stage_for_skill = intent.target_stage or current_stage
    intent.skill_code = STAGE_SKILL_MAP.get(stage_for_skill, "")
    intent.reason = _build_intent_reason(intent, current_stage)
    return intent


def _build_intent_reason(intent: AgentCreationIntent, current_stage: str) -> str:
    parts = [f"类型={intent.intent_type}"]
    if intent.subject:
        parts.append(f"主体={intent.subject}")
    if intent.refinement_hint:
        parts.append(f"调整={intent.refinement_hint}")
    if intent.target_stage and intent.target_stage != current_stage:
        parts.append(f"阶段→{STAGE_LABELS_ZH.get(intent.target_stage, intent.target_stage)}")
    if intent.skill_code:
        parts.append(f"Skill={intent.skill_code}")
    return " · ".join(parts)


def pipeline_index(stage: str) -> int:
    for i, s in enumerate(PIPELINE_STAGES):
        if s["stage"] == stage:
            return i
    return -1


def format_pipeline_overview(current_stage: str, *, skill_version: str = "") -> str:
    idx = pipeline_index(current_stage)
    lines = ["【创作主链路 · Skill 串联】"]
    if idx >= 0:
        step = PIPELINE_STAGES[idx]
        ver = f" v{skill_version}" if skill_version else ""
        skill = step["skill_code"] or "（无限画布，无 LLM Skill）"
        lines.append(
            f"当前：{idx + 1}/{len(PIPELINE_STAGES)} · {step['label']} · {skill}{ver}"
        )
        lines.append(f"本阶段目标：{step['goal']}")
    chain = " → ".join(
        f"**{s['label']}**" if s["stage"] == current_stage else s["label"]
        for s in PIPELINE_STAGES
    )
    lines.append(f"主链路：{chain}")
    if idx >= 0 and idx + 1 < len(PIPELINE_STAGES):
        nxt = PIPELINE_STAGES[idx + 1]
        lines.append(f"主链路下一环：{nxt['label']}（{nxt['goal']}）")
    return "\n".join(lines)


def build_reply_guidance_block(
    *,
    stage: str,
    intent: AgentCreationIntent,
    style_name: Optional[str] = None,
    subject: str = "",
    mode_name: Optional[str] = None,
    user_message: str = "",
    character_substep: str = "",
) -> str:
    """注入 Prompt：要求模型在回复末尾给出强关联编号引导。"""
    subj = subject or intent.subject or "当前方案"
    style = style_name or "已绑定风格"
    effective_stage = intent.target_stage or stage
    stage_label = STAGE_LABELS_ZH.get(effective_stage, effective_stage)
    mode = mode_name or "当前创作类型"
    user_hint = (user_message or "").strip()[:120] or "（见用户最新消息）"
    substep = character_substep or intent.character_substep or ""

    stage_switch_note = ""
    if intent.intent_type == "stage_switch" and intent.target_stage:
        new_label = STAGE_LABELS_ZH.get(intent.target_stage, intent.target_stage)
        stage_switch_note = (
            f"\n**【阶段切换 · 最高优先级】** 用户已要求进入「{new_label}」。"
            f"开头须明确宣布已进入 {new_label}，**禁止**继续上一阶段（如角色卡/定妆）的交付；"
            f"正文按新阶段 Skill 引导用户协作。\n"
        )

    examples = _guidance_examples(
        effective_stage,
        subj,
        style,
        intent.intent_type,
        character_substep=substep,
    )
    example_text = "\n".join(f"  {i + 1}. {line}" for i, line in enumerate(examples))
    stage_constraints = _stage_reply_constraints(
        effective_stage,
        mode=mode,
        user_hint=user_hint,
        style=style,
        active_character=subj if subj != "当前方案" else "",
        character_substep=substep,
    )

    return f"""【回复结构 · 强关联引导（必须遵守）】
{stage_switch_note}1. **开头 1~2 句**：点明当前阶段「{STAGE_LABELS_ZH.get(intent.target_stage or stage, stage_label)}」、用户意图、正在帮用户完成什么（引用用户原话或主体「{subj}」）。
2. **正文**：严格按已加载 Skill 执行；与绑定风格「{style}」保持一致。
{stage_constraints}
3. **结尾**：必须包含 `### 下一步可选`，给出 **3~4 条**编号选项，与用户当前进度/角色/风格强相关；用户可直接回复编号或加粗关键词继续。
   选项应覆盖：确认定稿 / 风格微调（如更滑稽/清秀/落魄）/ 进入主链路下一环（若本阶段已完成）。
   参考格式（请按实际内容改写，勿照抄）：
{example_text}"""


def _stage_reply_constraints(
    stage: str,
    *,
    mode: str = "当前创作类型",
    user_hint: str = "",
    style: str = "已绑定风格",
    active_character: str = "",
    character_substep: str = "",
) -> str:
    if stage == "character":
        from app.core.drama.agent_character_focus import CHARACTER_SUBSTEPS

        char_line = (
            f"   - **活跃角色**：{active_character}；用户未点名时 **必须** 继续该角色，"
            f"**禁止** 跳回更早角色（如已完成的白小檀）或默认第一个角色。"
            if active_character
            else "   - 用户未点名角色：须从上轮「下一步可选」/对话摘要锁定当前角色，禁止默认第一个角色。"
        )
        substep_line = ""
        if character_substep:
            label = CHARACTER_SUBSTEPS.get(character_substep, character_substep)
            substep_line = f"   - **本轮子步骤**：{label}（{character_substep}）；单轮只交付该步，勿混出其他角色或其他步骤。"
        return f"""2.1 **角色阶段专用（高优先级，冲突以本条为准）**：
{char_line}
{substep_line}
   - 用户原话「{user_hint}」须映射到上述角色与子步骤；开头须写出角色全名。
   - 「下一步可选」选项须全部围绕同一活跃角色，勿切换到其他待设计角色（除非用户明确要求）。"""
    if stage == "production":
        return f"""2.1 **生产落地专用（高优先级，冲突以本条为准）**：
   - 路径内化：剧本→场景→分镜→**本阶段按章节×格号出 prompt**→画布出图/出视频。
   - 每轮 **只做一步**：P0 盘点 / P1 章节规划 / P2 单格包（默认）/ P3 章确认；**禁止**一轮堆叠多步。
   - **禁止**重复开场、禁止每轮重贴全表；已规划章节仅一行进度摘要。
   - P2 须含 `image-prompt` + `video-prompt` + `production-tasks`；对齐风格「{style}」与用户「{user_hint}」。"""
    if stage != "concept":
        return ""
    return f"""2.1 **创意脑暴专用（高优先级，冲突以本条为准）**：
   - 使命：收敛为 **1 个定稿方向 + 剧本大纲**，理想 2~3 轮完成；**禁止**多轮重复 ABC 比选。
   - 融合输入：用户「{user_hint}」+ 风格「{style}」+ 类型「{mode}」+ Tool 知识/经典热梗参照。
   - 按进度只做一个子步骤：**3A** 三案九项风格包 → **3B** 用户选定后深化（不再列另两案）→ **3C** 定稿方向 + 剧本大纲。
   - 风格包九项：故事概念、剧情结构、剧情梗概、视觉风格、核心人物、配乐气质、对白风格、建议时长、创意亮点。
   - 禁止 JSON/YAML/代码块；禁止 Brief 就绪度/六维打分等拖沓内容。"""


def _guidance_examples(
    stage: str,
    subject: str,
    style: str,
    intent_type: str,
    *,
    character_substep: str = "",
) -> List[str]:
    subj = subject or "该角色"
    if stage == "character":
        if intent_type == "stage_switch":
            return [
                f"**确认进入{STAGE_LABELS_ZH.get('scene', '场景')}**，从核心场景开始设计。",
                "**回到角色阶段**，补完队列中下一位角色。",
                f"**先定稿当前角色卡**，再进入场景（若仍有待设计角色）。",
            ]
        if character_substep == "look_design":
            return [
                f"**确认{subj}定妆方向**，我继续产出 look-prompt 与出图任务。",
                f"**更阴冷压迫一点**，强化{subj}契约反派气场，仍保持{style}。",
                f"**更滑稽诡异一点**，加强纸偶丑角感，仍保持{style}。",
                f"**确认后进入{subj}角色卡**，产出 16:9 八维设定卡。",
            ]
        if character_substep == "character_card":
            return [
                f"**确认{subj}角色卡方向**，锁定八维设定与 16:9 card-prompt。",
                f"**加强{subj}道具细节**，补婚书/纸折冠等识别点。",
                f"**更阴冷一点**，调整表情与动作气质，仍保持{style}。",
                f"**进入下一位角色**，继续角色阶段流水线。",
            ]
        return [
            f"**确认{subj}角色设计**，我继续进入他的定妆图设计。",
            f"**更滑稽一点**，加强《天书奇谭》丑角喜感，仍保持{style}。",
            f"**更阴冷压迫一点**，强化礼貌空心契约感，仍保持{style}。",
            f"**先补下一位角色**，把与{subj}的关系一起细化。",
        ]
    if stage == "concept":
        if intent_type == "confirm":
            return [
                "**确认定稿**，输出完整剧本大纲并进入大纲阶段。",
                "**最后一处微调**（说明要改的点），我修订后定稿。",
                "**补充分集节拍**，把前 5 集钩子写细。",
            ]
        if intent_type == "advance":
            return [
                "**进入大纲阶段**，按定稿方向展开剧集结构。",
                "**先定稿当前方向**，再进入大纲。",
                "**加强首集爆点**，微调后再定稿。",
            ]
        return [
            "**选方向 A**，我据此深化人物与分集节拍。",
            "**选方向 B**，我据此深化人物与分集节拍。",
            "**选方向 C**，我据此深化人物与分集节拍。",
            f"**换一批风格包**，仍保持{style}与「{subject or '当前题材'}」。",
        ]
    if stage == "outline":
        return [
            "**确认本集大纲**，进入剧本撰写。",
            "**加强首集爆点**，微调冲突节奏。",
            "**补充配角线**，再出一版大纲。",
        ]
    if stage == "script":
        return [
            "**确认本场剧本**，进入角色/场景设计。",
            "**加强对白张力**，再改一版。",
            "**拆分为分场**，标注情绪曲线。",
        ]
    if stage == "scene":
        return [
            f"**确认{subj}场景方向**，输出主图 scene-prompt 与六宫格 prompt。",
            f"**一键六宫格生图**，同场景六机位探索图。",
            f"**加强{style}氛围**，调整光影与色调后重新出 prompt。",
            "**进入分镜**，按场景拆分镜头。",
        ]
    if stage == "storyboard":
        return [
            "**确认分镜表**，进入提示词工程或推到画布出图。",
            f"**加强{style}镜头运动**，补特写与转场。",
            "**调整时长节奏**，适配单集时长。",
            "**深化 S01 画面描述**，补场面调度。",
        ]
    if stage == "production":
        return [
            "**继续下一格 G0X**，产出 image/video prompt 包。",
            f"**微调当前格光色/运镜**，仍保持{style}。",
            "**确认本章完成**，进入下一章节规划。",
            "**在画布一键出图/出视频**（使用 production-tasks）。",
        ]
    return [
        "**继续完善当前阶段**产出。",
        "**确认定稿**，进入主链路下一环。",
        "**按你的意见微调**，我出一版修订。",
    ]


def suggest_next_options(
    stage: str,
    *,
    intent: Optional[AgentCreationIntent] = None,
    subject: str = "",
    style_name: Optional[str] = None,
    recent_user_messages: Optional[Sequence[str]] = None,
    character_substep: str = "",
    recent_assistant_messages: Optional[Sequence[str]] = None,
) -> List[str]:
    """API/前端「建议下一步」— 与 Prompt 引导同源。"""
    subj = subject or (intent.subject if intent else "") or ""
    substep = character_substep or (intent.character_substep if intent else "") or ""
    if not subj and recent_assistant_messages:
        from app.core.drama.agent_character_focus import extract_character_from_assistant

        for msg in reversed(list(recent_assistant_messages)[-3:]):
            subj = extract_character_from_assistant(msg)
            if subj:
                break
    if not subj and recent_user_messages:
        for msg in reversed(list(recent_user_messages)[-5:]):
            subj = extract_subject(msg)
            if subj:
                break
    intent_type = intent.intent_type if intent else "continue"
    raw = _guidance_examples(
        stage, subj, style_name or "绑定风格", intent_type, character_substep=substep
    )
    # 去掉 Markdown 加粗标记，供 UI 展示
    return [re.sub(r"\*\*([^*]+)\*\*", r"\1", line) for line in raw[:4]]


def resolve_effective_stage(current_stage: str, intent: AgentCreationIntent) -> str:
    if intent.target_stage and not intent.stay_stage:
        return intent.target_stage
    return current_stage
