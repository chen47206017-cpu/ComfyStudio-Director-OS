# 当前状态

状态：`PARTIAL`

- 本机 ComfyUI：`127.0.0.1:8188`，已打开并处于可用状态；Wan 5 秒受控重试已自然终态。
- 集成网关：默认配置值已统一为 `127.0.0.1:8092`，并要求 H3 catalog 与 no-I/O dry-run 能力。`8091` 仍是观测到的 health-only 旧监听器；检查脚本会明确失败且不停止、替换或修改任一监听器。
- Wan 任务：`d14f40680fe241b6a91a2258d5cccaab`，ComfyUI `prompt_id=d6f31d60-bee3-47a7-8f51-357c0c2739a1`，状态 `SUCCEEDED`。项目内镜像 MP4 为 `432x768`、`121` 帧、`24fps`、`5.04s`、SHA-256 `f148c6a6bf1bee170f70d04960622fbc456630b4a7a0622fba373cacd6a2b0ae`；QA 为 `SMOKE_ONLY` / `REJECTED_FOR_DELIVERY`，不得无界重试或称为最终成片。
- H3：`BLOCKED_LOCAL_H3` / `DRY_RUN_ONLY`；下载保护仍为 deferred，未做文件检查。用户于 **2026-09-03** 报告独立 PowerShell 尚未返回提示符，截图进度约 `4,278,120,438` 字节；这是用户报告的进行中进度，不是文件大小或 SHA-256 证据。下载结束前不得停止、重启、替换、重复启动、读取、哈希、移动、改名、加载或刷新模型列表。
