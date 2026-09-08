# MiniMax H3 状态

本轮交付时，MiniMax H3 仍不能标记为“已安装”或“已跑通”。

- 本机选择器：`BLOCKED_LOCAL_H3`。当前 RTX 5060 Ti 16GB 的 H3 节点/完整权重链尚未完成可验证安装。
- AutoDL 选择器：`DRY_RUN_ONLY`。`minimax_h3_lightx2v_v5` 用于多图参考，`minimax_h3_image_audio_to_video_v2` 用于多图多音频；本轮没有真实 Token、没有提交任务、没有产生费用。
- 下载清单：`minimax_h3.download-state.json` 中六项保持 `PENDING` / `verification: DEFERRED`。用户在 **2026-09-03** 报告独立 PowerShell 窗口仍未返回提示符，截图显示写入进度约 **4,278,120,438 字节**；该数字是用户报告的传输进度，不是本机读取、文件大小或完整性证据。传输结束前不得读取、哈希、移动、加载或据此判断完整安装，也不得刷新模型列表。
- 历史命令里其余来源不完整或 URL 为空的项目没有执行；没有根据文件名猜测补下载。

## 官方工作流核对（只读）

2026-09-03 对官方 MiniMax H3 模型页和 AutoDL ComfyUI API 说明做了只读
核对。官方 H3-Base-Ref2VA 是 Omni-reference 模式，输入上限为：图片最多
9 张，视频最多 3 段（每段 2-15 秒、总时长不超过 15 秒），音频最多 3 段
（每段 2-15 秒、总时长不超过 15 秒），混合输入总文件数不超过 12 个。
官方输出约束为 4-15 秒、24 fps；基础输出短边默认为 768，2K 需要单独的
H3-Regenerate-2K 流程。

官方本地检查点按任务族提供完整组件目录：`processor`、`tokenizer`、
`text_encoder`、`transformer`、`visual_vae` 和 `audio_vae`。其中
H3-Context-IR 与 H3-Regenerate-2K 不是当前开源本地组件；因此本项目当前
登记的六个量化文件只能作为用户提供的候选坐标，不能替代完整组件、节点和
兼容性验证。AutoDL 的两个工作流 ID 仍只通过本项目的 `DRY_RUN_ONLY`
选择器适配，字段限制以各工作流抽屉返回的实际 schema 为准。

只有用户确认活动 PowerShell 已自然返回提示符后，才能单独执行文件大小、修改时间、SHA-256、来源和 ComfyUI 识别检查。即使 Ref2VA 通过，也仍需分别验证文本编码器、视频 VAE、音频 VAE、LoRA、节点版本和实际短片推理。
