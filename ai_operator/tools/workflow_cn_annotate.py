import json
import sys
from copy import deepcopy
from pathlib import Path
from datetime import datetime, timezone, timedelta


TYPE_CN = {
    "SaveVideo": (
        "保存视频",
        "保存最终生成的视频文件。"
    ),
    "ResolutionSelector": (
        "分辨率选择",
        "设置画面比例、目标像素量和尺寸对齐倍数。"
    ),
    "VAELoader": (
        "加载 VAE",
        "加载视频或音频 VAE。模型文件名保持英文以确保兼容。"
    ),
    "VAEDecode": (
        "视频 VAE 解码",
        "把视频潜变量解码为图像帧。"
    ),
    "VAEDecodeAudio": (
        "音频 VAE 解码",
        "从联合潜变量中解码音频。"
    ),
    "KSamplerSelect": (
        "采样器选择",
        "选择采样算法。H3 官方 Ref2VA 模板默认使用 res_multistep。"
    ),
    "BasicScheduler": (
        "采样调度器",
        "控制采样步数、调度方式和去噪强度。"
    ),
    "SamplerCustomAdvanced": (
        "高级采样执行",
        "执行模型采样，输出视频与音频联合潜变量。"
    ),
    "BasicGuider": (
        "基础引导器",
        "把模型和条件提示组合成采样引导。"
    ),
    "UNETLoader": (
        "加载 H3 主模型",
        "加载 MiniMax H3 Ref2VA diffusion 模型。"
    ),
    "CLIPLoader": (
        "加载 H3 文本编码器",
        "加载 Qwen3-VL MiniMax H3 文本/视觉编码器。"
    ),
    "RandomNoise": (
        "随机种子 / 噪声",
        "控制生成随机种子。固定种子可用于重复对比测试。"
    ),
    "CreateVideo": (
        "合成视频",
        "把解码后的图像帧和音频组合为视频。"
    ),
    "ComfyMathExpression": (
        "时长转帧数",
        "根据秒数自动计算 H3 合法帧数。"
    ),
    "MiniMaxH3ReferenceToVideo": (
        "MiniMax H3 多参考生视频",
        "核心 Ref2VA 节点。支持图片、视频和音频参考；Prompt 中使用 <Picture 1>、<Video 1>、<Audio 1> 引用。"
    ),
    "LoadImage": (
        "加载参考图片",
        "加载人物、场景或道具参考图。"
    ),
    "PrimitiveStringMultiline": (
        "生成提示词",
        "填写 H3 Prompt。引用图片时必须使用正确的 <Picture N> 标签。"
    ),
    "PrimitiveFloat": (
        "数值参数",
        "工作流数值输入。"
    ),
    "PrimitiveInt": (
        "整数参数",
        "工作流整数输入。"
    ),
    "PrimitiveBoolean": (
        "开关参数",
        "工作流布尔开关。"
    ),
    "LoraLoaderModelOnly": (
        "加载 H3 加速 LoRA",
        "可选的 H3 Turbo / Lightning LoRA。首轮基线测试保持关闭。"
    ),
    "ComfySwitchNode": (
        "模型 / 参数切换",
        "用于在完整模式和加速模式之间切换。"
    ),
    "MarkdownNote": (
        "中文说明",
        "工作流说明文本。"
    ),
}


H3_PROMPT = """<Picture 1> 是唯一的人物身份参考图。

写实电影感人物镜头。
保持 <Picture 1> 中同一位中国女性的人物身份、年龄观感、面部结构、发型和服装完全一致。

人物自然站在现代室内空间中，轻微呼吸，先自然看向镜头附近，然后缓慢将视线转向侧方。
表情和动作克制、真实、自然，符合现实物理运动。

真实皮肤纹理，电影级自然光影，浅景深。
保持人物五官和身份稳定。

禁止新增人物。
禁止复制身体。
禁止脸部变形。
禁止年龄漂移。
禁止突然切镜。
禁止异常肢体。
禁止剧烈镜头运动。"""


def beijing_now():
    return datetime.now(
        timezone(timedelta(hours=8))
    ).isoformat()


def set_title_and_note(node, title, note):
    node["title"] = title

    props = node.setdefault(
        "properties",
        {}
    )

    props["中文说明"] = note
    props["内部节点类型"] = node.get("type", "")


def clean_removed_links(data, removed_node_ids):
    links = data.get("links", [])

    removed_link_ids = set()

    for link in links:
        if (
            len(link) >= 4
            and (
                link[1] in removed_node_ids
                or link[3] in removed_node_ids
            )
        ):
            removed_link_ids.add(link[0])

    data["links"] = [
        link
        for link in links
        if link[0] not in removed_link_ids
    ]

    for node in data.get("nodes", []):

        for inp in node.get("inputs", []) or []:
            if inp.get("link") in removed_link_ids:
                inp["link"] = None

        for out in node.get("outputs", []) or []:
            old = out.get("links")

            if isinstance(old, list):
                new = [
                    link_id
                    for link_id in old
                    if link_id not in removed_link_ids
                ]

                out["links"] = new if new else None

    return sorted(removed_link_ids)


def validate_workflow(data):
    errors = []
    warnings = []

    nodes = data.get("nodes", [])
    links = data.get("links", [])

    node_ids = [
        n.get("id")
        for n in nodes
    ]

    if len(node_ids) != len(set(node_ids)):
        errors.append(
            "存在重复 node id"
        )

    node_id_set = set(node_ids)

    link_ids = set()

    for link in links:
        if not isinstance(link, list) or len(link) < 6:
            errors.append(
                f"异常 link 格式: {link!r}"
            )
            continue

        link_id = link[0]
        origin_id = link[1]
        target_id = link[3]

        if link_id in link_ids:
            errors.append(
                f"重复 link id: {link_id}"
            )

        link_ids.add(link_id)

        if origin_id not in node_id_set:
            errors.append(
                f"link {link_id} 的来源节点不存在: {origin_id}"
            )

        if target_id not in node_id_set:
            errors.append(
                f"link {link_id} 的目标节点不存在: {target_id}"
            )

    for node in nodes:
        for inp in node.get("inputs", []) or []:
            link_id = inp.get("link")

            if (
                link_id is not None
                and link_id not in link_ids
            ):
                errors.append(
                    f"节点 {node.get('id')} 输入 {inp.get('name')} "
                    f"引用了不存在的 link {link_id}"
                )

    if not any(
        n.get("type") == "MiniMaxH3ReferenceToVideo"
        for n in nodes
    ):
        warnings.append(
            "没有找到 MiniMaxH3ReferenceToVideo"
        )

    return errors, warnings


def main():

    if len(sys.argv) != 3:
        print(
            "用法: workflow_cn_annotate.py SOURCE DEST"
        )
        return 2

    source = Path(sys.argv[1])
    dest = Path(sys.argv[2])

    if not source.exists():
        print(
            "FAIL：源工作流不存在：",
            source
        )
        return 2

    data = json.loads(
        source.read_text(
            encoding="utf-8-sig"
        )
    )

    data = deepcopy(data)

    changes = []
    warnings = []

    nodes = data.get(
        "nodes",
        []
    )

    # --------------------------------------------------
    # 1. 通用中文标题 + 中文说明
    # --------------------------------------------------

    load_images = []

    for node in nodes:

        node_type = node.get(
            "type",
            ""
        )

        if node_type in TYPE_CN:

            title, note = TYPE_CN[node_type]

            # LoadImage 后面单独编号
            if node_type != "LoadImage":
                set_title_and_note(
                    node,
                    title,
                    note
                )

        if node_type == "LoadImage":
            load_images.append(node)

    # --------------------------------------------------
    # 2. 两个参考图节点
    # --------------------------------------------------

    load_images.sort(
        key=lambda x: x.get("id", 0)
    )

    if len(load_images) >= 1:

        first = load_images[0]

        set_title_and_note(
            first,
            "参考图1：苏婉晴45岁人物身份",
            "本次 Smoke Test 唯一人物身份参考图。H3 Prompt 中使用 <Picture 1> 引用。"
        )

        first["widgets_values"] = [
            "H3_SMOKE_SW45.png",
            "image"
        ]

        first.setdefault(
            "widgets_values_named",
            {}
        )["image"] = "H3_SMOKE_SW45.png"

        first[
            "widgets_values_named"
        ]["upload"] = "image"

        changes.append(
            "参考图1 -> H3_SMOKE_SW45.png"
        )

    # 第二张官方示例图：首轮测试删除
    removed_node_ids = set()

    if len(load_images) >= 2:

        second = load_images[1]

        removed_node_ids.add(
            second["id"]
        )

        changes.append(
            f"删除官方第二张示例参考图节点 id={second['id']}"
        )

    if removed_node_ids:

        removed_links = clean_removed_links(
            data,
            removed_node_ids
        )

        data["nodes"] = [
            n
            for n in data["nodes"]
            if n.get("id") not in removed_node_ids
        ]

        changes.append(
            "删除关联连接线: "
            + ", ".join(
                map(str, removed_links)
            )
        )

    # --------------------------------------------------
    # 3. 分辨率固定到 9:16 / 0.4MP / 32
    # --------------------------------------------------

    for node in data["nodes"]:

        if node.get("type") == "ResolutionSelector":

            node["widgets_values"] = [
                "9:16 (Portrait Widescreen)",
                0.4,
                32
            ]

            node["widgets_values_named"] = {
                "aspect_ratio":
                    "9:16 (Portrait Widescreen)",
                "megapixels":
                    0.4,
                "multiple":
                    32
            }

            set_title_and_note(
                node,
                "分辨率：9:16 竖屏 / 0.4MP",
                "当前 Smoke Test 使用 9:16 竖屏、0.4MP、32像素网格对齐。"
            )

            changes.append(
                "分辨率 -> 9:16 / 0.4MP / multiple=32"
            )

    # --------------------------------------------------
    # 4. 视频时长固定 5 秒
    # --------------------------------------------------

    for node in data["nodes"]:

        if (
            node.get("type") == "PrimitiveFloat"
            and (
                "Duration" in node.get("title", "")
                or node.get("id") == 135
            )
        ):

            node["widgets_values"] = [
                5
            ]

            node["widgets_values_named"] = {
                "value": 5
            }

            set_title_and_note(
                node,
                "视频时长：5秒",
                "5秒在24fps下由公式转换为H3合法帧数，当前约124帧。"
            )

            changes.append(
                "Duration -> 5秒"
            )

    # --------------------------------------------------
    # 5. Prompt 中文化
    # --------------------------------------------------

    for node in data["nodes"]:

        if (
            node.get("type")
            == "PrimitiveStringMultiline"
        ):

            node["widgets_values"] = [
                H3_PROMPT
            ]

            node["widgets_values_named"] = {
                "value": H3_PROMPT
            }

            set_title_and_note(
                node,
                "H3生成提示词（中文）",
                "首轮仅引用 <Picture 1>。不得引用不存在的 <Picture 2>。"
            )

            changes.append(
                "Prompt -> 中文单参考图版本"
            )

    # --------------------------------------------------
    # 6. H3核心节点中文说明
    # --------------------------------------------------

    for node in data["nodes"]:

        if (
            node.get("type")
            == "MiniMaxH3ReferenceToVideo"
        ):

            set_title_and_note(
                node,
                "H3核心：多参考生成视频",
                "Ref2VA核心节点。当前只连接 Picture 1。图片/视频/音频内部字段名不能翻译，否则会破坏ComfyUI执行。"
            )

            # 把没有真实连接的第二/第三参考明确设空
            for inp in node.get("inputs", []) or []:

                name = inp.get(
                    "name",
                    ""
                )

                if (
                    "ref_image_1" in name
                    or "ref_image_2" in name
                ):
                    inp["link"] = None

    # --------------------------------------------------
    # 7. Lightning LoRA 保持关闭
    # --------------------------------------------------

    for node in data["nodes"]:

        if (
            node.get("type")
            == "PrimitiveBoolean"
            and (
                "Lightning" in node.get("title", "")
                or node.get("id") == 146
            )
        ):

            node["widgets_values"] = [
                False
            ]

            node["widgets_values_named"] = {
                "value": False
            }

            set_title_and_note(
                node,
                "H3 Turbo LoRA：关闭",
                "首轮基线测试关闭4步Turbo LoRA，使用完整采样路径。"
            )

            changes.append(
                "Lightning/Turbo LoRA -> OFF"
            )

    # --------------------------------------------------
    # 8. 中文 Markdown 说明
    # --------------------------------------------------

    for node in data["nodes"]:

        if node.get("type") != "MarkdownNote":
            continue

        original_title = node.get(
            "title",
            ""
        )

        if "MiniMax H3" in original_title:

            text = """## MiniMax H3 Ref2VA 中文说明

这是 MiniMax H3 多参考生成视频工作流。

### 当前测试目标

- 模式：Ref2VA
- 比例：9:16 竖屏
- 目标像素：0.4MP
- 时长：5秒
- 帧率：24fps
- 人物参考：仅 Picture 1
- Turbo / Lightning LoRA：关闭

### 引用规则

Prompt 中：

`<Picture 1>` = 苏婉晴45岁人物参考图

首轮测试不存在 Picture 2，因此不得在 Prompt 中出现 `<Picture 2>`。

### 注意

ComfyUI 内部节点类型、输入名、模型文件名保持英文，这是执行协议的一部分，不能直接翻译。
所有可读说明、标题和 Studio 界面统一使用中文。
"""

            node["widgets_values"] = [
                text
            ]

            node["widgets_values_named"] = {
                "text": text
            }

            node["title"] = (
                "说明：MiniMax H3 Ref2VA"
            )

        elif "Model Links" in original_title:

            text = """## H3 模型说明

当前工作流需要：

### 主模型
`minimax_h3_ref2va_pruned_int8_convrot.safetensors`

### 文本/视觉编码器
`qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`

### 视频 VAE
`minimax_h3_video_vae_fp16.safetensors`

### 音频 VAE
`minimax_h3_audio_vae_fp32.safetensors`

### 可选 Turbo LoRA
`minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors`

模型文件名属于运行时标识，不翻译。
"""

            node["widgets_values"] = [
                text
            ]

            node["widgets_values_named"] = {
                "text": text
            }

            node["title"] = (
                "说明：H3模型文件"
            )

        elif "Size Settings" in original_title:

            text = """## 分辨率说明

首轮 Smoke Test：

| 参数 | 当前值 |
|---|---|
| 画面比例 | 9:16 竖屏 |
| 目标像素 | 0.4 MP |
| 对齐倍数 | 32 |
| 时长 | 5 秒 |
| 帧率 | 24 fps |

正式720P测试将在首轮稳定通过后再开启。
"""

            node["widgets_values"] = [
                text
            ]

            node["widgets_values_named"] = {
                "text": text
            }

            node["title"] = (
                "说明：分辨率与测试参数"
            )

    # --------------------------------------------------
    # 9. JSON完整性验证
    # --------------------------------------------------

    errors, validation_warnings = validate_workflow(
        data
    )

    warnings.extend(
        validation_warnings
    )

    dest.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if errors:

        print(
            "FAIL：工作流结构验证失败"
        )

        for err in errors:
            print(
                " -",
                err
            )

        return 1

    dest.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    report = {
        "timestamp_beijing": beijing_now(),
        "source": str(source),
        "output": str(dest),
        "status": "PASS",
        "node_count": len(
            data.get("nodes", [])
        ),
        "link_count": len(
            data.get("links", [])
        ),
        "changes": changes,
        "warnings": warnings,
        "policy": {
            "translate_node_title": True,
            "translate_notes": True,
            "translate_internal_node_type": False,
            "translate_input_output_protocol_names": False,
            "translate_model_filename": False
        }
    }

    report_file = dest.with_suffix(
        ".report.json"
    )

    report_file.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print(
        "========================================"
    )
    print(
        "PASS：中文工作流生成完成"
    )
    print(
        "输出：",
        dest
    )
    print(
        "报告：",
        report_file
    )
    print(
        "节点数：",
        report["node_count"]
    )
    print(
        "连接数：",
        report["link_count"]
    )

    for change in changes:
        print(
            " -",
            change
        )

    print(
        "========================================"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
