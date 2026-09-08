# 已确认决策

- 保留现有 `G:\ComfyUI` 和 Web 项目，控制层只通过真实 ComfyUI `/prompt`、进度和 history 工作。
- 本机 16GB 只承担低分辨率 smoke；最终 720p/1080p 与云端 RTX 5090 仍需另行授权和验证。
- MiniMax H3 作为统一选择器中的一个逻辑引擎；AutoDL 两个工作流只做 dry-run 适配。
- 不使用或恢复此前暴露的 Hugging Face Token；用户应在 Hugging Face 侧撤销并重建。
