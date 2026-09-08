# 自然语言任务简报

- 用户目标：继续执行 ComfyStudio StudioOS V10.1 Director Demo Production Upgrade：修复 Demo 生成界面的真实反馈与选中态问题，优先当前镜头场景解析，补齐运行态验收证据；不修改旧数据库结构、不删除资产、不声称 H3 已产出 MP4，所有新时间使用 Asia/Shanghai。
- 建议任务类型：`high_risk`（必须在审阅后确认）
- 关键词：继续执行、comfystudio、studioos、v10.1、director、demo、production、upgrade、修复、生成界面的真实反馈与选中态问题、优先当前镜头场景解析、补齐运行态验收证据、不修改旧数据库结构、不删除资产、不声称、h3、已产出、mp4、所有新时间使用、asia、shanghai

## 风险信号
- 包含删除操作
- 涉及生产环境
- 涉及数据库

## 建议优先阅读的源码
- `backend/app.py`（相关度 108）
- `frontend/src/main.tsx`（相关度 85）
- `reports/V921_UI_router_20260908_031517/v8_routes.py`（相关度 33）
- `reports/V924_ROUTE_CLEAN_20260908_032432/v8_routes.py`（相关度 33）
- `backend/routes/v8_routes.py`（相关度 30）

## 建议优先阅读的测试
- `tests/test_backend_v10.py`（相关度 21）
- `tests/test_demo_v101.py`（相关度 11）
- `tests/test_comfy_execution.py`（相关度 6）

## 历史经验命中
- `05_EXPERIENCE_DATABASE/Technical_Changes/TCM-TASK-20260904-035538-e1945231f2f4e3ea.md`：在不访问、停止、重启、移动、哈希或加载正在由用户独立 PowerShell 写入的 G:\ComfyUI\models\diffusion_models\minimax_h3_ref2va_pruned_nvfp4.safetensors，且不更改 Clash Verge、代理或网络的前提下，修复 Web 管理页面默认 API 端口指向旧服务的问题；将控制层默认/文档/启动验证统一到当前带 H3 dry-run 与 job evidence 的受管 8092 服务，并为 10
- `05_EXPERIENCE_DATABASE/20260725_全会话事故分析报告.md`：# 全会话事故分析报告: 上下文压缩与修复循环崩塌
- `05_EXPERIENCE_DATABASE/Technical_Changes/TCM-TASK-20260904-072408-f2506f760823607a.md`：- `src/comfyui_production/h3.py`
- `05_EXPERIENCE_DATABASE/Technical_Changes/RECURRING_FAILURES_AND_COUNTERMEASURES.md`：# 重复故障与对抗修复矩阵
- `05_EXPERIENCE_DATABASE/General/Recurring_Bugs_Root_Cause.md`：# 重复错误的根因分析 — 备份不等于修复

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
