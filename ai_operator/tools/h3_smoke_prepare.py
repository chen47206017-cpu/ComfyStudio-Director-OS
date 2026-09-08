import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

import httpx


PROJECT = Path(r"F:\一人公司\comfyui-production")

SOURCE = PROJECT / "workflows" / "smoke" / "H3-R2V-SMOKE-001_CN.json"

DEST = PROJECT / "workflows" / "smoke" / "H3-R2V-SMOKE-001_CN_FIXED.json"

REPORT = PROJECT / "workflows" / "smoke" / "H3-R2V-SMOKE-001_CN_FIXED.report.json"

INPUT_IMAGE = Path(
    r"G:\ComfyStudioData\workers\h3-f\input\H3_SMOKE_SW45.png"
)

COMFY_URL = "http://127.0.0.1:8189"


EXPECTED_TYPES = {
    92:  "SaveVideo",
    115: "ResolutionSelector",
    116: "MarkdownNote",
    117: "MarkdownNote",
    119: "VAELoader",
    120: "VAELoader",
    121: "VAEDecodeAudio",
    122: "VAEDecode",
    123: "KSamplerSelect",
    124: "BasicScheduler",
    125: "SamplerCustomAdvanced",
    126: "BasicGuider",
    127: "UNETLoader",
    128: "CLIPLoader",
    129: "RandomNoise",
    130: "CreateVideo",
    131: "ComfyMathExpression",
    132: "PrimitiveFloat",
    136: "MiniMaxH3ReferenceToVideo",
    137: "LoadImage",
    138: "PrimitiveStringMultiline",
    139: "LoadImage",
    140: "MarkdownNote",
    141: "ComfySwitchNode",
    142: "ComfySwitchNode",
    143: "PrimitiveInt",
    144: "PrimitiveInt",
    145: "LoraLoaderModelOnly",
    146: "PrimitiveBoolean",
}


EXPECTED_MODELS = {
    "unet": "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
    "clip": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    "video_vae": "minimax_h3_video_vae_fp16.safetensors",
    "audio_vae": "minimax_h3_audio_vae_fp32.safetensors",
    "lora": "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
}


PROMPT = """<Picture 1> 是唯一的人物身份参考图。

写实、电影级、自然的人物镜头。

画面中的人物必须保持为 <Picture 1> 中完全同一位中国女性。
保持相同的面部身份、年龄观感、五官结构、脸型、发型、发色和服装。
不得改变人物身份。

人物自然站在现代室内空间。
身体保持基本静止，只产生真实而轻微的自然呼吸。
开始时视线接近镜头方向，随后缓慢、自然地把目光转向侧方。
头部仅允许极小幅度自然运动。

表情克制、自然、真实。
真实皮肤纹理，保留毛孔、细微纹理和年龄特征。
电影级自然光影，浅景深，真实空间感。

动作必须符合现实物理。
镜头稳定，只允许极其轻微的电影感呼吸式运动。

无对白。
不要张嘴说话。
只允许自然环境底噪。

禁止新增人物。
禁止出现第二个人。
禁止复制人物。
禁止复制身体。
禁止多余肢体。
禁止脸部变形。
禁止身份漂移。
禁止年龄漂移。
禁止换脸。
禁止突然切镜。
禁止剧烈镜头运动。
禁止异常身体运动。
禁止卡通化。
禁止二次元化。
"""


GROUP_TITLES = {
    1: "模型加载",
    2: "采样执行",
    3: "模式切换与采样参数",
    4: "解码与视频合成",
    5: "用户输入",
    6: "H3 条件构建",
}


NODE_TITLES = {
    92:  "保存最终视频",
    115: "分辨率：9:16竖屏 / 0.4MP",
    116: "说明：MiniMax H3 Ref2VA",
    117: "说明：H3模型与存储",
    119: "加载视频 VAE",
    120: "加载音频 VAE",
    121: "解码 H3 音频",
    122: "解码 H3 视频画面",
    123: "采样器：res_multistep",
    124: "采样调度：simple / 20步",
    125: "执行 H3 高级采样",
    126: "H3 条件引导",
    127: "加载 H3 Ref2VA 主模型",
    128: "加载 H3 Qwen3-VL 编码器",
    129: "随机种子 / 噪声",
    130: "合成24fps视频与音频",
    131: "5秒时长转 H3 合法帧数",
    132: "视频时长：5秒",
    136: "H3核心：单人物参考生成视频",
    137: "参考图1：苏婉晴45岁人物身份",
    138: "H3生成提示词（中文）",
    140: "说明：竖屏分辨率与测试参数",
    141: "模型路径切换：完整 / Turbo",
    142: "采样步数切换：20步 / 4步",
    143: "完整模式采样步数：20",
    144: "Turbo模式采样步数：4",
    145: "加载 H3 Turbo LoRA（当前不启用）",
    146: "H3 Turbo LoRA：关闭",
}


def bj_now():
    return datetime.now(
        timezone(timedelta(hours=8))
    ).isoformat()


def get_node(data, node_id):
    for n in data.get("nodes", []):
        if n.get("id") == node_id:
            return n

    raise RuntimeError(
        f"找不到节点 id={node_id}"
    )


def set_title(node, title):
    node["title"] = title


def set_note(node, text):
    props = node.setdefault(
        "properties",
        {}
    )

    props["中文说明"] = text


def set_widgets(node, values, named=None):
    node["widgets_values"] = values

    if named is not None:
        node["widgets_values_named"] = named


def remove_node_and_links(
    data,
    node_id
):
    removed_link_ids = set()

    for link in data.get("links", []):
        if (
            len(link) >= 4
            and (
                link[1] == node_id
                or link[3] == node_id
            )
        ):
            removed_link_ids.add(
                link[0]
            )

    data["links"] = [
        link
        for link in data.get("links", [])
        if link[0] not in removed_link_ids
    ]

    data["nodes"] = [
        node
        for node in data.get("nodes", [])
        if node.get("id") != node_id
    ]

    for node in data["nodes"]:

        for inp in node.get(
            "inputs",
            []
        ) or []:

            if inp.get(
                "link"
            ) in removed_link_ids:

                inp["link"] = None

        for out in node.get(
            "outputs",
            []
        ) or []:

            links = out.get("links")

            if isinstance(
                links,
                list
            ):

                new_links = [
                    x
                    for x in links
                    if x not in removed_link_ids
                ]

                out["links"] = (
                    new_links
                    if new_links
                    else None
                )

    return sorted(
        removed_link_ids
    )


def validate_links(data):

    errors = []

    nodes = data.get(
        "nodes",
        []
    )

    links = data.get(
        "links",
        []
    )

    node_map = {
        n["id"]: n
        for n in nodes
    }

    link_map = {}

    for link in links:

        if (
            not isinstance(link, list)
            or len(link) < 6
        ):
            errors.append(
                f"非法link结构：{link!r}"
            )
            continue

        link_id = link[0]

        if link_id in link_map:
            errors.append(
                f"重复link id：{link_id}"
            )

        link_map[link_id] = link

        source_node = link[1]
        target_node = link[3]

        if source_node not in node_map:
            errors.append(
                f"link {link_id} 来源节点不存在：{source_node}"
            )

        if target_node not in node_map:
            errors.append(
                f"link {link_id} 目标节点不存在：{target_node}"
            )

    for n in nodes:

        node_id = n["id"]

        for inp in n.get(
            "inputs",
            []
        ) or []:

            link_id = inp.get(
                "link"
            )

            if link_id is None:
                continue

            if link_id not in link_map:
                errors.append(
                    f"节点 {node_id} 输入 {inp.get('name')} "
                    f"引用不存在link {link_id}"
                )
                continue

            if (
                link_map[link_id][3]
                != node_id
            ):
                errors.append(
                    f"节点 {node_id} 输入link {link_id} "
                    f"目标不一致"
                )

        for output_index, out in enumerate(
            n.get("outputs", []) or []
        ):

            output_links = out.get(
                "links"
            )

            if not isinstance(
                output_links,
                list
            ):
                continue

            for link_id in output_links:

                if link_id not in link_map:
                    errors.append(
                        f"节点 {node_id} 输出引用不存在link {link_id}"
                    )

                    continue

                if (
                    link_map[link_id][1]
                    != node_id
                ):
                    errors.append(
                        f"节点 {node_id} 输出link {link_id} "
                        f"来源不一致"
                    )

    return errors


def loader_options(
    object_info,
    node_type,
    field
):
    try:
        return object_info[
            node_type
        ]["input"]["required"][
            field
        ][0]
    except Exception:
        return []


def main():

    report = {
        "timestamp_beijing": bj_now(),
        "source": str(SOURCE),
        "output": str(DEST),
        "status": "BLOCKED",
        "changes": [],
        "local_checks": {},
        "runtime_checks": {},
        "errors": [],
        "warnings": [],
    }

    if not SOURCE.exists():
        raise RuntimeError(
            f"中文源工作流不存在：{SOURCE}"
        )

    if not INPUT_IMAGE.exists():
        raise RuntimeError(
            f"H3输入参考图不存在：{INPUT_IMAGE}"
        )

    data = json.loads(
        SOURCE.read_text(
            encoding="utf-8-sig"
        )
    )

    # =========================================================
    # 1. 验证我们面对的是已知官方 H3 R2V 模板
    # =========================================================

    for node_id, expected_type in EXPECTED_TYPES.items():

        n = get_node(
            data,
            node_id
        )

        actual = n.get("type")

        if actual != expected_type:

            raise RuntimeError(
                f"节点 {node_id} 类型漂移："
                f"expected={expected_type}, actual={actual}"
            )

    report[
        "local_checks"
    ][
        "known_workflow_structure"
    ] = True


    # =========================================================
    # 2. 中文化所有28个保留节点
    # =========================================================

    for node_id, title in NODE_TITLES.items():

        n = get_node(
            data,
            node_id
        )

        set_title(
            n,
            title
        )

        set_note(
            n,
            (
                f"内部节点类型：{n.get('type')}。"
                "中文标题和说明仅用于用户界面；"
                "ComfyUI内部type、输入输出字段、模型文件名和link协议保持原始值。"
            )
        )

    # 工作流分组标题也改成中文
    for group in data.get(
        "groups",
        []
    ):

        group_id = group.get(
            "id"
        )

        if group_id in GROUP_TITLES:

            group[
                "title"
            ] = GROUP_TITLES[
                group_id
            ]

    report["changes"].append(
        "所有用户可见节点标题和分组标题中文化"
    )


    # =========================================================
    # 3. 参考图1 -> 苏婉晴45
    # =========================================================

    image1 = get_node(
        data,
        137
    )

    set_widgets(
        image1,
        [
            "H3_SMOKE_SW45.png",
            "image"
        ],
        {
            "image":
                "H3_SMOKE_SW45.png",
            "upload":
                "image"
        }
    )

    report["changes"].append(
        "参考图1 -> H3_SMOKE_SW45.png"
    )


    # =========================================================
    # 4. 删除官方第二张示例图节点139及link282
    # =========================================================

    removed_links = remove_node_and_links(
        data,
        139
    )

    report["changes"].append(
        f"删除官方示例图节点139；删除links={removed_links}"
    )

    # H3核心节点再明确清空 Picture2 / Picture3
    h3 = get_node(
        data,
        136
    )

    for inp in h3.get(
        "inputs",
        []
    ) or []:

        name = inp.get(
            "name",
            ""
        )

        if name in {
            "ref_images.ref_image_1",
            "ref_images.ref_image_2",
        }:

            inp["link"] = None


    # =========================================================
    # 5. Prompt -> 中文单参考图版本
    # =========================================================

    prompt_node = get_node(
        data,
        138
    )

    set_widgets(
        prompt_node,
        [PROMPT],
        {
            "value": PROMPT
        }
    )

    report["changes"].append(
        "Prompt -> 中文；仅引用 <Picture 1>"
    )


    # =========================================================
    # 6. 9:16 / 0.4MP / multiple 32
    # =========================================================

    resolution = get_node(
        data,
        115
    )

    set_widgets(
        resolution,
        [
            "9:16 (Portrait Widescreen)",
            0.4,
            32
        ],
        {
            "aspect_ratio":
                "9:16 (Portrait Widescreen)",
            "megapixels":
                0.4,
            "multiple":
                32
        }
    )

    report["changes"].append(
        "分辨率 -> 9:16 / 0.4MP / 32"
    )


    # =========================================================
    # 7. 5秒
    # =========================================================

    duration = get_node(
        data,
        132
    )

    set_widgets(
        duration,
        [5],
        {
            "value": 5
        }
    )

    report["changes"].append(
        "视频时长 -> 5秒"
    )


    # =========================================================
    # 8. 采样参数锁定
    # =========================================================

    sampler = get_node(
        data,
        123
    )

    set_widgets(
        sampler,
        [
            "res_multistep"
        ],
        {
            "sampler_name":
                "res_multistep"
        }
    )

    scheduler = get_node(
        data,
        124
    )

    set_widgets(
        scheduler,
        [
            "simple",
            20,
            1
        ],
        {
            "scheduler":
                "simple",
            "steps":
                20,
            "denoise":
                1
        }
    )

    full_steps = get_node(
        data,
        143
    )

    set_widgets(
        full_steps,
        [
            20,
            "fixed"
        ],
        {
            "value": 20,
            "fixed": "fixed"
        }
    )

    turbo_steps = get_node(
        data,
        144
    )

    set_widgets(
        turbo_steps,
        [
            4,
            "fixed"
        ],
        {
            "value": 4,
            "fixed": "fixed"
        }
    )

    # 两个Switch全部固定False
    for switch_id in (
        141,
        142
    ):

        switch = get_node(
            data,
            switch_id
        )

        set_widgets(
            switch,
            [False],
            {
                "switch":
                    False
            }
        )

    turbo_enable = get_node(
        data,
        146
    )

    set_widgets(
        turbo_enable,
        [False],
        {
            "value":
                False
        }
    )

    report["changes"].append(
        "完整模式20步；Turbo 4步分支保留但关闭"
    )


    # =========================================================
    # 9. 视频输出参数锁定
    # =========================================================

    create_video = get_node(
        data,
        130
    )

    set_widgets(
        create_video,
        [
            24,
            8
        ],
        {
            "fps":
                24,
            "bit_depth":
                8
        }
    )

    save_video = get_node(
        data,
        92
    )

    set_widgets(
        save_video,
        [
            "video/H3_SMOKE_SW45",
            "auto",
            "auto"
        ],
        {
            "filename_prefix":
                "video/H3_SMOKE_SW45",
            "format":
                "auto",
            "codec":
                "auto"
        }
    )


    # =========================================================
    # 10. 三个 Markdown Note 全部换中文
    # =========================================================

    note116 = get_node(
        data,
        116
    )

    text116 = """## MiniMax H3 Ref2VA 中文工作流

当前工作流用于第一轮本地 H3 人物一致性 Smoke Test。

### 当前测试参数

- 模式：Ref2VA
- 人物参考：仅 `<Picture 1>`
- 比例：9:16
- 目标像素：0.4MP
- 时长：5秒
- 帧率：24fps
- 完整模式采样：20步
- Turbo / Lightning LoRA：关闭
- 不使用视频参考
- 不使用音频参考

### 测试目标

只验证：

1. H3模型能否在 RTX 5060 Ti 16GB 环境完成真实生成；
2. 单人物参考身份是否稳定；
3. 视频/音频联合解码是否正常；
4. 是否存在OOM、dtype、DynamicVRAM或节点执行错误。

本轮不追求正式短剧成片质量。
"""

    set_widgets(
        note116,
        [text116],
        {
            "text": text116
        }
    )


    note117 = get_node(
        data,
        117
    )

    text117 = f"""## H3 模型配置

### 主模型
`{EXPECTED_MODELS["unet"]}`

### 文本 / 视觉编码器
`{EXPECTED_MODELS["clip"]}`

### 视频 VAE
`{EXPECTED_MODELS["video_vae"]}`

### 音频 VAE
`{EXPECTED_MODELS["audio_vae"]}`

### 可选 Turbo LoRA
`{EXPECTED_MODELS["lora"]}`

当前 Smoke Test：

**Turbo LoRA = 关闭**

模型文件名属于 ComfyUI 运行协议，不翻译。
"""

    set_widgets(
        note117,
        [text117],
        {
            "text": text117
        }
    )


    note140 = get_node(
        data,
        140
    )

    text140 = """## 竖屏测试参数

| 参数 | 当前值 |
|---|---|
| 比例 | 9:16 竖屏 |
| 目标像素 | 0.4 MP |
| 对齐倍数 | 32 |
| 时长 | 5 秒 |
| 帧率 | 24 fps |
| 参考图片 | 1 张 |
| Turbo LoRA | 关闭 |

0.4MP 用于第一轮 16GB 显存兼容性测试。

首轮稳定通过以后，再提高到正式720P质量测试。
"""

    set_widgets(
        note140,
        [text140],
        {
            "text": text140
        }
    )


    # =========================================================
    # 11. 锁定/核对真实模型，不盲目改模型结构
    # =========================================================

    json_models = {
        "unet":
            get_node(data, 127)
            .get("widgets_values", [None])[0],

        "clip":
            get_node(data, 128)
            .get("widgets_values", [None])[0],

        "video_vae":
            get_node(data, 119)
            .get("widgets_values", [None])[0],

        "audio_vae":
            get_node(data, 120)
            .get("widgets_values", [None])[0],

        "lora":
            get_node(data, 145)
            .get("widgets_values", [None])[0],
    }

    report[
        "local_checks"
    ][
        "workflow_models"
    ] = json_models

    for key, expected in EXPECTED_MODELS.items():

        actual = json_models.get(
            key
        )

        if actual != expected:

            report["errors"].append(
                f"JSON模型不一致：{key}: "
                f"expected={expected}, actual={actual}"
            )


    # =========================================================
    # 12. 本地Workflow结构验证
    # =========================================================

    link_errors = validate_links(
        data
    )

    report["errors"].extend(
        link_errors
    )

    node_ids = {
        n["id"]
        for n in data["nodes"]
    }

    link_ids = {
        x[0]
        for x in data["links"]
    }

    if 139 in node_ids:
        report["errors"].append(
            "节点139仍然存在"
        )

    if 282 in link_ids:
        report["errors"].append(
            "link282仍然存在"
        )

    if "<Picture 1>" not in PROMPT:
        report["errors"].append(
            "Prompt缺少Picture 1"
        )

    if "<Picture 2>" in PROMPT:
        report["errors"].append(
            "Prompt错误包含Picture 2"
        )

    if "<Audio 1>" in PROMPT:
        report["errors"].append(
            "Prompt错误包含Audio 1"
        )

    report[
        "local_checks"
    ][
        "input_image_exists"
    ] = INPUT_IMAGE.exists()

    report[
        "local_checks"
    ][
        "node_count_after_fix"
    ] = len(
        data["nodes"]
    )

    report[
        "local_checks"
    ][
        "link_count_after_fix"
    ] = len(
        data["links"]
    )


    # =========================================================
    # 13. 中文覆盖检查
    # =========================================================

    chinese_title_missing = []

    for n in data[
        "nodes"
    ]:

        title = str(
            n.get(
                "title",
                ""
            )
        )

        if not title:
            chinese_title_missing.append(
                n["id"]
            )

        props = n.get(
            "properties",
            {}
        )

        if (
            "中文说明"
            not in props
        ):
            report["warnings"].append(
                f"节点 {n['id']} 缺少中文说明"
            )

    if chinese_title_missing:
        report["errors"].append(
            "缺少标题的节点："
            + str(
                chinese_title_missing
            )
        )

    english_group_titles = []

    for group in data.get(
        "groups",
        []
    ):

        if group.get("id") in GROUP_TITLES:

            if (
                group.get("title")
                != GROUP_TITLES[
                    group["id"]
                ]
            ):

                english_group_titles.append(
                    group["id"]
                )

    if english_group_titles:
        report["errors"].append(
            "存在未中文化分组："
            + str(
                english_group_titles
            )
        )


    # =========================================================
    # 14. 保存固定版
    # =========================================================

    DEST.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    DEST.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


    # =========================================================
    # 15. 8189 Runtime Schema + 模型发现验证
    # =========================================================

    runtime_ok = False

    try:

        with httpx.Client(
            timeout=30,
            trust_env=False
        ) as client:

            r = client.get(
                f"{COMFY_URL}/object_info"
            )

            r.raise_for_status()

            oi = r.json()

        required_runtime_nodes = [
            "MiniMaxH3ReferenceToVideo",
            "ResolutionSelector",
            "UNETLoader",
            "CLIPLoader",
            "VAELoader",
            "KSamplerSelect",
            "BasicScheduler",
            "SamplerCustomAdvanced",
            "CreateVideo",
            "SaveVideo",
            "LoraLoaderModelOnly",
        ]

        missing_runtime_nodes = [
            x
            for x in required_runtime_nodes
            if x not in oi
        ]

        report[
            "runtime_checks"
        ][
            "missing_nodes"
        ] = missing_runtime_nodes


        unets = loader_options(
            oi,
            "UNETLoader",
            "unet_name"
        )

        clips = loader_options(
            oi,
            "CLIPLoader",
            "clip_name"
        )

        vaes = loader_options(
            oi,
            "VAELoader",
            "vae_name"
        )

        loras = loader_options(
            oi,
            "LoraLoaderModelOnly",
            "lora_name"
        )

        model_checks = {
            "unet":
                EXPECTED_MODELS["unet"]
                in unets,

            "clip":
                EXPECTED_MODELS["clip"]
                in clips,

            "video_vae":
                EXPECTED_MODELS["video_vae"]
                in vaes,

            "audio_vae":
                EXPECTED_MODELS["audio_vae"]
                in vaes,

            "lora":
                EXPECTED_MODELS["lora"]
                in loras,
        }

        report[
            "runtime_checks"
        ][
            "models"
        ] = model_checks


        ratio_options = []

        try:
            ratio_options = (
                oi[
                    "ResolutionSelector"
                ][
                    "input"
                ][
                    "required"
                ][
                    "aspect_ratio"
                ][1][
                    "options"
                ]
            )
        except Exception:
            pass

        ratio_ok = (
            "9:16 (Portrait Widescreen)"
            in ratio_options
        )

        report[
            "runtime_checks"
        ][
            "ratio_9_16_supported"
        ] = ratio_ok


        if missing_runtime_nodes:

            report["errors"].append(
                "8189缺少运行节点："
                + ", ".join(
                    missing_runtime_nodes
                )
            )

        for key, ok in model_checks.items():

            if not ok:
                report["errors"].append(
                    f"8189没有识别模型：{key}"
                )

        if not ratio_ok:
            report["errors"].append(
                "8189 ResolutionSelector没有9:16选项"
            )

        runtime_ok = (
            not missing_runtime_nodes
            and
            all(
                model_checks.values()
            )
            and
            ratio_ok
        )

    except Exception as exc:

        report[
            "runtime_checks"
        ][
            "reachable"
        ] = False

        report["errors"].append(
            "8189 Runtime验证失败："
            + repr(exc)
        )

    else:

        report[
            "runtime_checks"
        ][
            "reachable"
        ] = True


    # =========================================================
    # 16. 最终结果
    # =========================================================

    local_ok = (
        len(
            report["errors"]
        )
        == 0
    )

    if local_ok and runtime_ok:

        report["status"] = (
            "PASS_READY_FOR_FIRST_GENERATION"
        )

    else:

        report["status"] = (
            "BLOCKED"
        )


    REPORT.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


    print()
    print(
        "=========================================="
    )

    print(
        "H3 SMOKE WORKFLOW STATUS =",
        report["status"]
    )

    print(
        "固定版：",
        DEST
    )

    print(
        "报告：",
        REPORT
    )

    print(
        "节点数：",
        report["local_checks"][
            "node_count_after_fix"
        ]
    )

    print(
        "8189可连接：",
        report["runtime_checks"].get(
            "reachable",
            False
        )
    )

    print(
        "9:16支持：",
        report["runtime_checks"].get(
            "ratio_9_16_supported",
            False
        )
    )

    print()
    print(
        "模型验证："
    )

    for key, value in (
        report[
            "runtime_checks"
        ].get(
            "models",
            {}
        ).items()
    ):

        print(
            f"  {key}: {value}"
        )

    if report["errors"]:

        print()
        print(
            "错误："
        )

        for err in report["errors"]:
            print(
                " -",
                err
            )

    print()
    print(
        "修改内容："
    )

    for change in report[
        "changes"
    ]:

        print(
            " -",
            change
        )

    print(
        "=========================================="
    )

    if report["status"] == (
        "PASS_READY_FOR_FIRST_GENERATION"
    ):
        return 0

    return 1


if __name__ == "__main__":

    try:
        sys.exit(
            main()
        )

    except Exception as exc:

        REPORT.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        fatal = {
            "timestamp_beijing":
                bj_now(),
            "status":
                "FATAL",
            "error":
                repr(exc),
        }

        REPORT.write_text(
            json.dumps(
                fatal,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        print()
        print(
            "FATAL：",
            repr(exc)
        )

        print(
            "报告：",
            REPORT
        )

        sys.exit(2)
