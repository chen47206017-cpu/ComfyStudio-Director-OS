# 自然语言任务简报

- 用户目标：进入 IMPLEMENTATION_FASTLANE_V44：在既有 V10.1 Demo 上实现并验证 local_comfy 真实 Render Pipeline。导演台支持选择 local_comfy（默认）、AutoDL5090、API；SHOT002 点击生成后执行 Canon/Prompt/Workflow preflight、提交当前 8189 ComfyUI、轮询 history、下载且验证真实 MP4、回写 durable job 状态并在导演台显示视频播放器。必须生成真实 MP4 才能完成。同步按 V44 规则补齐可验证的中文导演台、全能参考、ReactFlow 持久化和单一运行证据；绝不删除资产/Canon/数据库或触碰 G 盘运行时。
- 建议任务类型：`high_risk`（必须在审阅后确认）
- 关键词：进入、implementation_fastlane_v44、在既有、v10.1、demo、上实现并验证、local_comfy、真实、render、pipeline、导演台支持选择、默认、autodl5090、api、shot002、点击生成后执行、canon、prompt、workflow、preflight、提交当前、8189、comfyui、轮询、history、下载且验证真实、mp4、回写、durable、job、状态并在导演台显示视频播放器、必须生成真实、才能完成、同步按、v44、规则补齐可验证的中文导演台、全能参考、reactflow、持久化和单一运行证据、绝不删除资产、数据库或触碰、盘运行时

## 风险信号
- 包含删除操作
- 涉及数据库

## 建议优先阅读的源码
- `backend/app.py`（相关度 416）
- `frontend/src/main.tsx`（相关度 265）
- `backend/v10_core.py`（相关度 99）
- `reports/V921_UI_router_20260908_031517/v8_routes.py`（相关度 78）
- `reports/V924_ROUTE_CLEAN_20260908_032432/v8_routes.py`（相关度 78）

## 建议优先阅读的测试
- `tests/test_backend_v10.py`（相关度 77）
- `tests/test_comfy_execution.py`（相关度 23）
- `tests/test_demo_v101.py`（相关度 18）

## 历史经验命中
- `05_EXPERIENCE_DATABASE/Technical_Changes/TCM-TASK-20260904-035538-e1945231f2f4e3ea.md`：在不访问、停止、重启、移动、哈希或加载正在由用户独立 PowerShell 写入的 G:\ComfyUI\models\diffusion_models\minimax_h3_ref2va_pruned_nvfp4.safetensors，且不更改 Clash Verge、代理或网络的前提下，修复 Web 管理页面默认 API 端口指向旧服务的问题；将控制层默认/文档/启动验证统一到当前带 H3 dry-run 与 job evidence 的受管 8092 服务，并为 10
- `05_EXPERIENCE_DATABASE/Technical_Changes/TCM-TASK-20260904-045550-172bf5d64fddaa75.md`：- 当前错误/失败基础：A partial model transfer, dry-run response, successful ComfyUI prompt, or low-resolution smoke artifact cannot prove H3 installation or final delivery. | Do not retry or alter the protected transfer, its network path, either lis
- `05_EXPERIENCE_DATABASE/Technical_Changes/TCM-TASK-20260826-125911-7252586ebe53dca9.md`：Implement a bounded local Phase 12 processing-trace read model: link durable ProviderRun attempts to their originating ProcessingJob using an internal trace ID, expose a redacted read-only trace through LocalOperationsCore and the local HTT
- `05_EXPERIENCE_DATABASE/Technical_Changes/TCM-TASK-20260904-072408-f2506f760823607a.md`：- `docs/AUTODL_COMFYUI_API.md`
- `05_EXPERIENCE_DATABASE/Debug/API_Verification_Checklist.md`：代码中有**10处**备注更新API调用，全部使用**错误的API格式**：

## 验证命令候选
- `python -m pytest` — pytest.ini、tox.ini 或 tests 目录

## 下一步
1. 阅读命中源码、测试、状态与交接，确认模块职责。
2. 补全同目录的 `TASK_CONTRACT_DRAFT.json`：先完成 acceptance 并清空未决问题；再填写精确 allowed_files/allowed_symbols、成功标准以及同时覆盖 static/runtime 的 verification_plan。
3. 若草稿含 `conflict_resolutions`，说明安全边界与用户原话冲突；必须先取得用户对安全替代方案的逐字确认，禁止 AI 自行改写。
4. 网站账号、Cookie、发布、监控、检测或点赞等复合自动化必须审阅 capability_plan：每轮只选择一个 current_slice；默认 simulation，不得把“开发”解释为真实账号执行授权。
5. 首个候选执行 `artifact_lineage.py init`；后续候选执行 `artifact_lineage.py advance`，然后运行 `iteration_workflow.py prepare`。
6. 修改后用 `verification_plan.py run --id <检查ID>` 运行契约内命令；不得手写伪造验证日志。

## 安全边界
本简报只提供阅读建议；草稿的 allowed_files 保持为空，绝不会自动授权修改文件。凭据只允许来自 mock、环境变量、Secret Store 或交互输入，禁止写入契约和验证输出。
