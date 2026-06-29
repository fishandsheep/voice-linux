from html import escape
from uuid import uuid4

import gradio as gr

from src.i18n.i18n import get_active_language


ENGINE_SOURCES = {
    "f5": {
        "name": {
            "en": "SWivid/F5-TTS official repository",
            "zh": "SWivid/F5-TTS 官方仓库",
        },
        "url": "https://github.com/SWivid/F5-TTS",
    },
    "voxcpm": {
        "name": {
            "en": "VoxCPM official usage guide",
            "zh": "VoxCPM 官方使用文档",
        },
        "url": "https://voxcpm.readthedocs.io/en/latest/usage_guide.html",
    },
    "index_tts": {
        "name": {
            "en": "IndexTTS official repository",
            "zh": "IndexTTS 官方仓库",
        },
        "url": "https://github.com/index-tts/index-tts",
    },
}

FIELD_LABEL_MODES = {
    "Choose Model": "choice",
    "Speech rate": "range",
    "Audio Format": "choice",
    "Mode": "choice",
    "Voice Description": "text",
    "CFG Value": "range",
    "Inference Steps": "range",
    "Normalize Text": "boolean",
    "Denoise Reference": "boolean",
    "Emotion Reference Audio": "reference",
    "Enable Emotion Audio": "boolean",
    "Emotion Strength": "range",
}


TTS_HELP = {
    "f5": {
        "Choose Model": {
            "en": {
                "title": "Choose Model",
                "purpose": "Select which official F5 checkpoint handles cloning and synthesis stability.",
                "recommended": "Use `SWivid/F5-TTS_v1` first. It is the main v1 base line from the official project.",
                "higher": "Newer or larger checkpoints may improve naturalness or robustness, but can load slower and use more VRAM.",
                "lower": "Older or lighter checkpoints can start faster, but similarity and stability may drop.",
            },
            "zh": {
                "title": "选择模型",
                "purpose": "选择哪个官方 F5 权重负责音色克隆与合成稳定性。",
                "recommended": "优先用 `SWivid/F5-TTS_v1`。这是官方项目当前主推的 v1 基线。",
                "higher": "更新或更大的权重可能提升自然度与稳健性，但加载更慢、更吃显存。",
                "lower": "更旧或更轻的权重启动更快，但相似度和稳定性可能下降。",
            },
        },
        "Speech rate": {
            "en": {
                "title": "Speech rate",
                "purpose": "Control target speaking speed. F5 official inference code uses `speed` when estimating generation duration.",
                "recommended": "Keep `0.9` to `1.1` for most dubbing jobs.",
                "higher": "Higher values shorten target duration and sound faster, useful when subtitles are tight, but speech can feel rushed.",
                "lower": "Lower values lengthen target duration and sound slower, usually clearer, but easier to overflow subtitle timing.",
            },
            "zh": {
                "title": "语速",
                "purpose": "控制目标说话速度。F5 官方推理代码会用 `speed` 参与目标时长估算。",
                "recommended": "大多数配音先放在 `0.9` 到 `1.1`。",
                "higher": "值越大，目标时长越短、听感越快，适合字幕时轴很紧时使用，但可能显得赶。",
                "lower": "值越小，目标时长越长、听感越慢，通常更清楚，但更容易超出字幕时长。",
            },
        },
        "Audio Format": {
            "en": {
                "title": "Audio Format",
                "purpose": "Choose exported audio container for the generated clip.",
                "recommended": "`mp3` for preview and delivery, `wav` for editing and remuxing.",
                "higher": "Less-compressed formats preserve detail better, but files get larger.",
                "lower": "More-compressed formats save space and transfer faster, but may lose detail.",
            },
            "zh": {
                "title": "音频格式",
                "purpose": "选择生成结果导出的音频封装格式。",
                "recommended": "预览或交付优先 `mp3`，后期编辑或混流优先 `wav`。",
                "higher": "压缩更少的格式更保细节，但文件更大。",
                "lower": "压缩更多的格式更省空间、传输更快，但会损失一些细节。",
            },
        },
    },
    "voxcpm": {
        "Mode": {
            "en": {
                "title": "Mode",
                "purpose": "Select VoxCPM generation mode. Official docs define Voice Design, Controllable Voice Cloning, and Hi-Fi Cloning with different input requirements.",
                "recommended": "Start with `Voice Clone`. Use `Ultimate Clone` only when reference transcript is trustworthy.",
                "higher": "Moving to stricter cloning modes usually improves speaker fidelity, but requires cleaner and more complete reference inputs.",
                "lower": "Simpler modes are easier to run and more forgiving, but identity control becomes weaker.",
            },
            "zh": {
                "title": "模式",
                "purpose": "选择 VoxCPM 生成模式。官方文档定义了 Voice Design、Controllable Voice Cloning、Hi-Fi Cloning 三类模式，输入要求不同。",
                "recommended": "先用 `Voice Clone`。只有参考转写可靠时再上 `Ultimate Clone`。",
                "higher": "越偏严格克隆模式，通常越像原说话人，但要求更干净、更完整的参考输入。",
                "lower": "越简单的模式越容易跑通、容错更高，但身份控制更弱。",
            },
        },
        "Voice Description": {
            "en": {
                "title": "Voice Description",
                "purpose": "Provide natural-language style instruction. Official docs use parenthesized control instructions to steer age, tone, emotion, pace, and style.",
                "recommended": "Keep it short and concrete, such as `warm calm female narrator`.",
                "higher": "Stronger or longer descriptions push style harder, but can override the reference timbre.",
                "lower": "Shorter descriptions preserve more of the reference speaker identity.",
            },
            "zh": {
                "title": "音色描述",
                "purpose": "提供自然语言风格指令。官方文档用括号控制词来引导年龄、语气、情绪、节奏和风格。",
                "recommended": "尽量短且具体，比如 `温暖 平静 女旁白`。",
                "higher": "描述越强或越长，风格牵引越明显，但也更容易盖过参考音色。",
                "lower": "描述越短，通常越能保住参考说话人的身份特征。",
            },
        },
        "CFG Value": {
            "en": {
                "title": "CFG Value",
                "purpose": "Guidance scale. Official VoxCPM docs say higher values follow conditioning more strictly and lower values allow more variation.",
                "recommended": "Typical official range is `1.0` to `3.0`; `2.0` is solid default.",
                "higher": "Higher values obey prompt and reference more strongly, but can sound stiff or less natural.",
                "lower": "Lower values sound freer and sometimes more natural, but style and identity control weaken.",
            },
            "zh": {
                "title": "CFG 值",
                "purpose": "引导强度。官方 VoxCPM 文档说明，值越高越严格跟随条件，值越低变化空间越大。",
                "recommended": "官方常见范围是 `1.0` 到 `3.0`；`2.0` 是稳妥默认值。",
                "higher": "值越高，对提示词和参考的服从更强，但可能更僵硬、不够自然。",
                "lower": "值越低，结果更自由，有时更自然，但风格与身份控制会变弱。",
            },
        },
        "Inference Steps": {
            "en": {
                "title": "Inference Steps",
                "purpose": "Number of diffusion denoising steps. Official docs say more steps improve detail and naturalness at the cost of speed.",
                "recommended": "`8` to `12` for daily use. Official recommended span is `4` to `30`.",
                "higher": "More steps can improve detail and stability, but synthesis gets slower.",
                "lower": "Fewer steps return faster, but quality can drop and artifacts may rise.",
            },
            "zh": {
                "title": "推理步数",
                "purpose": "扩散去噪步数。官方文档说明，步数越多通常细节与自然度越好，但速度更慢。",
                "recommended": "日常先用 `8` 到 `12`。官方建议范围是 `4` 到 `30`。",
                "higher": "步数更高，细节和稳定性可能更好，但合成更慢。",
                "lower": "步数更低，返回更快，但质量可能下降，伪影也可能增加。",
            },
        },
        "Normalize Text": {
            "en": {
                "title": "Normalize Text",
                "purpose": "Expand numbers, dates, and similar raw text forms before synthesis, matching the official usage guide.",
                "recommended": "Turn it on when input contains numbers, dates, abbreviations, or messy mixed text.",
                "higher": "More normalization improves readability and pronunciation of raw text, but can alter literal surface form.",
                "lower": "Less normalization preserves original spelling, but awkward formatting may hurt pronunciation.",
            },
            "zh": {
                "title": "文本归一化",
                "purpose": "在合成前把数字、日期等原始文本形态展开，和官方使用指南一致。",
                "recommended": "文本里有数字、日期、缩写或混乱混排时建议开启。",
                "higher": "归一化越积极，原始文本越容易被正确朗读，但可能改动字面形式。",
                "lower": "归一化越少，原文保留越完整，但奇怪格式可能影响发音。",
            },
        },
        "Denoise Reference": {
            "en": {
                "title": "Denoise Reference",
                "purpose": "Denoise prompt or reference audio before generation. Official docs recommend it when reference audio is noisy.",
                "recommended": "Enable only for noisy clips.",
                "higher": "Cleaner reference often improves cloning quality, but aggressive cleanup can strip vocal texture.",
                "lower": "Keeping raw audio preserves texture, but background noise may leak into synthesis.",
            },
            "zh": {
                "title": "参考音频降噪",
                "purpose": "在生成前先清理提示音或参考音噪声。官方文档建议在参考片段有噪声时开启。",
                "recommended": "只在参考片段明显嘈杂时开启。",
                "higher": "参考越干净，克隆质量通常越好，但清理过重会损失人声纹理。",
                "lower": "保留原始音频更能保住质感，但背景噪声可能被带进结果里。",
            },
        },
        "Audio Format": {
            "en": {
                "title": "Audio Format",
                "purpose": "Choose exported audio container for the synthesized clip.",
                "recommended": "`mp3` for preview and delivery, `wav` for editing and remuxing.",
                "higher": "Less-compressed formats preserve detail better, but files get larger.",
                "lower": "More-compressed formats save space and transfer faster, but may lose detail.",
            },
            "zh": {
                "title": "音频格式",
                "purpose": "选择合成结果导出的音频封装格式。",
                "recommended": "预览或交付优先 `mp3`，后期编辑或混流优先 `wav`。",
                "higher": "压缩更少的格式更保细节，但文件更大。",
                "lower": "压缩更多的格式更省空间、传输更快，但会损失一些细节。",
            },
        },
    },
    "index_tts": {
        "Emotion Reference Audio": {
            "en": {
                "title": "Emotion Reference Audio",
                "purpose": "Provide separate emotion clip. Official IndexTTS docs support `emo_audio_prompt` to inject emotional color independently from speaker timbre.",
                "recommended": "Use a short, clean clip with obvious intended emotion.",
                "higher": "Stronger emotional reference usually increases expressiveness, but can drift away from base speaker identity.",
                "lower": "Without a clear emotion clip, output stays more neutral and predictable.",
            },
            "zh": {
                "title": "情绪参考音频",
                "purpose": "提供独立情绪片段。官方 IndexTTS 文档支持用 `emo_audio_prompt` 在不改变基础音色的前提下注入情绪色彩。",
                "recommended": "使用短、干净、情绪明显的片段。",
                "higher": "情绪参考越强，表现力通常越明显，但也更容易偏离基础说话人身份。",
                "lower": "没有清晰情绪样本时，结果会更中性、也更可预测。",
            },
        },
        "Enable Emotion Audio": {
            "en": {
                "title": "Enable Emotion Audio",
                "purpose": "Toggle whether the separate emotion reference participates in synthesis.",
                "recommended": "Turn it on only when you intentionally provide an emotion clip.",
                "higher": "When enabled, emotion control becomes stronger, but poor clips can destabilize tone consistency.",
                "lower": "When disabled, cloning stays more stable and mainly follows speaker timbre.",
            },
            "zh": {
                "title": "启用情绪音频",
                "purpose": "控制独立情绪参考是否参与合成。",
                "recommended": "只有明确提供了情绪片段时再开启。",
                "higher": "开启后情绪控制更强，但差样本也更容易破坏语气一致性。",
                "lower": "关闭后克隆通常更稳，主要跟随说话人本身音色。",
            },
        },
        "Emotion Strength": {
            "en": {
                "title": "Emotion Strength",
                "purpose": "Blend weight of the emotion reference. Official docs define valid range `0.0 - 1.0`, default `1.0`.",
                "recommended": "Try `0.5` to `0.8` first when emotion clip is obvious.",
                "higher": "Higher values inject more emotion and drama, but exaggeration and identity drift increase.",
                "lower": "Lower values keep speaker identity steadier, but emotion becomes subtler.",
            },
            "zh": {
                "title": "情绪强度",
                "purpose": "控制情绪参考混入结果的权重。官方文档定义有效范围 `0.0 - 1.0`，默认 `1.0`。",
                "recommended": "如果情绪样本很明显，先试 `0.5` 到 `0.8`。",
                "higher": "值越高，情绪注入越重、戏剧性越强，但夸张和跑偏风险也更高。",
                "lower": "值越低，说话人身份更稳，但情绪会更弱、更含蓄。",
            },
        },
        "Audio Format": {
            "en": {
                "title": "Audio Format",
                "purpose": "Choose exported audio container for the synthesized clip.",
                "recommended": "`mp3` for preview and delivery, `wav` for editing and remuxing.",
                "higher": "Less-compressed formats preserve detail better, but files get larger.",
                "lower": "More-compressed formats save space and transfer faster, but may lose detail.",
            },
            "zh": {
                "title": "音频格式",
                "purpose": "选择合成结果导出的音频封装格式。",
                "recommended": "预览或交付优先 `mp3`，后期编辑或混流优先 `wav`。",
                "higher": "压缩更少的格式更保细节，但文件更大。",
                "lower": "压缩更多的格式更省空间、传输更快，但会损失一些细节。",
            },
        },
    },
}


def _lang_key() -> str:
    return "zh" if get_active_language() == "中文" else "en"


def help_html(engine: str, field: str) -> str:
    lang = _lang_key()
    text = TTS_HELP[engine][field].get(lang, TTS_HELP[engine][field]["en"])
    source = ENGINE_SOURCES[engine]
    source_name = source["name"].get(lang, source["name"]["en"])
    labels = {
        "purpose": "作用" if lang == "zh" else "Purpose",
        "recommended": "推荐值" if lang == "zh" else "Recommended",
        "source": "来源" if lang == "zh" else "Source",
    }
    section_labels = {
        "range": ("调大影响", "调小影响") if lang == "zh" else ("Higher value", "Lower value"),
        "boolean": ("开启后", "关闭后") if lang == "zh" else ("When enabled", "When disabled"),
        "choice": ("这样选时", "换个选项时") if lang == "zh" else ("With this choice", "With another choice"),
        "text": ("描述更强时", "描述更弱时") if lang == "zh" else ("With stronger wording", "With lighter wording"),
        "reference": ("参考更强时", "参考较弱时") if lang == "zh" else ("With stronger reference", "With weaker reference"),
    }
    detail_up, detail_down = section_labels[FIELD_LABEL_MODES[field]]
    return (
        f'<div class="tts-help-inner">'
        f'<button type="button" class="tts-help-close" onclick="document.getElementById(\'{{close_id}}\')?.click()" aria-label="Close help">×</button>'
        f"<p><strong>{escape(text['title'])}</strong></p>"
        f"<p><strong>{labels['purpose']}</strong><br>{escape(text['purpose'])}</p>"
        f"<p><strong>{labels['recommended']}</strong><br>{escape(text['recommended'])}</p>"
        f"<p><strong>{detail_up}</strong><br>{escape(text['higher'])}</p>"
        f"<p><strong>{detail_down}</strong><br>{escape(text['lower'])}</p>"
        f'<p><strong>{labels["source"]}</strong><br><a href="{source["url"]}" target="_blank" rel="noopener noreferrer">{escape(source_name)}</a></p>'
        f"</div>"
    )


def render_helped_control(engine: str, field: str, component_factory):
    close_id = f"tts-help-close-{uuid4().hex}"

    with gr.Column(elem_classes=["tts-help-shell"]):
        with gr.Row(elem_classes=["tts-help-row"]):
            with gr.Column(scale=24, min_width=0):
                component = component_factory()
            with gr.Column(scale=1, min_width=44):
                help_button = gr.Button(
                    value="?",
                    variant="secondary",
                    elem_classes=["tts-help-button"],
                    min_width=36,
                )
        help_state = gr.State(False)
        help_overlay = gr.HTML(
            value=f'<button type="button" class="tts-help-overlay-hit" onclick="document.getElementById(\'{close_id}\')?.click()" aria-label="Close help"></button>',
            visible=False,
            elem_classes=["tts-help-overlay"],
        )
        help_card = gr.HTML(
            value=help_html(engine, field).replace("{close_id}", close_id),
            visible=False,
            elem_classes=["tts-help-card"],
        )
        help_close = gr.Button(value="close", visible=False, elem_id=close_id)

    def _toggle(visible):
        next_visible = not bool(visible)
        return (
            next_visible,
            gr.update(visible=next_visible),
            gr.update(visible=next_visible, value=help_html(engine, field).replace("{close_id}", close_id)),
        )

    def _close():
        return False, gr.update(visible=False), gr.update(visible=False)

    help_button.click(_toggle, inputs=[help_state], outputs=[help_state, help_overlay, help_card])
    help_close.click(_close, outputs=[help_state, help_overlay, help_card])
    return component
