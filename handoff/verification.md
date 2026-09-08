# 验证记录

- 已通过：单元契约测试 `31/31`、API smoke、下载保护测试、JSON 解析、PowerShell 启动/检查脚本解析和 secret scan。
- 已观察：Wan 任务 `d14f40680fe241b6a91a2258d5cccaab` 已 `SUCCEEDED`；项目内镜像 MP4 的哈希、大小、H.264/24fps/121 帧/5.04s 媒体规格、输入素材哈希和抽帧 QA 已写入 `runtime/artifacts/d14f40680fe241b6a91a2258d5cccaab/qa.json`。
- QA 结论：`SMOKE_ONLY` / `REJECTED_FOR_DELIVERY`。原因是 `432x768` 非 `1080x1920`，画面存在明显颗粒/过处理细节、动作很弱，且无烧录字幕证据。
- 未验证：本机 H3 完整安装/推理、AutoDL 真实提交、5090 云端渲染、1080x1920 最终成片质量。
