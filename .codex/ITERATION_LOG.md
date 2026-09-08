# 迭代记录

> 每条记录对应一次可追溯的代码迭代。

## 2026-09-04 03:44 | TASK-20260904-030825 | PARTIAL

- 摘要：Completed the project-local ComfyUI control layer, MiniMax H3 unified selector, AutoDL dry-run contract, port documentation, and separate Wan smoke-test evidence. The protected H3 transfer was not inspected. The Wan artifact is a technical smoke result only, and finish is additionally gated by a runtime log changed by the natural ComfyUI run.
- 声明等级：static-only
- 下一步：Wait for explicit user confirmation that the independent PowerShell transfer has finished. Then perform a separately authorized read-only H3 integrity and component audit before refreshing model lists or running H3. After that, start a new explicitly authorized final-video task for a 1080x1920, 24fps, subtitle-burned five-second render.

### 实际改动
- README_COMFYUI_PRODUCTION.md
- docs/DISK_AND_RUNTIME_PLAN.md
- docs/INSTALL_WINDOWS.md
- docs/TROUBLESHOOTING.md
- docs/WEB_INTEGRATION.md
- docs/WORKFLOW_CATALOG.md
- handoff/bugs.md
- handoff/current_state.md
- handoff/next_tasks.md
- handoff/verification.md
- runtime/artifacts/d14f40680fe241b6a91a2258d5cccaab/qa.json
- runtime/artifacts/d14f40680fe241b6a91a2258d5cccaab/qa_frames/frame_01.jpg
- runtime/artifacts/d14f40680fe241b6a91a2258d5cccaab/qa_frames/frame_02.jpg
- runtime/artifacts/d14f40680fe241b6a91a2258d5cccaab/qa_frames/frame_03.jpg
- scripts/check_comfyui_api.ps1
- scripts/start_comfyui_api.ps1
- tests/test_core_contracts.py

### 验证
- python scripts/run_project_tests.py: 31/31 OK
- python scripts/check_workflow_json.py: 8 workflow JSON files validated
- python scripts/run_api_smoke.py: API smoke suite passed
- python scripts/secret_scan.py: no potential secrets found
- python scripts/check_h3_download_status.py: manifest_only; H3 remains PENDING/DEFERRED
- Read-only GET http://127.0.0.1:8092/api/comfyui/jobs/d14f40680fe241b6a91a2258d5cccaab: SUCCEEDED with prompt_id d6f31d60-bee3-47a7-8f51-357c0c2739a1
- runtime/artifacts/d14f40680fe241b6a91a2258d5cccaab/qa.json: 432x768, 121 frames, 24fps, 5.04s, SMOKE_ONLY / REJECTED_FOR_DELIVERY

### 成功标准证据
- 无

### 未验证项
- The user has not confirmed that the independent PowerShell download has returned to a prompt; Ref2VA presence, final size, modification time, SHA-256, and ComfyUI recognition remain uninspected.
- The remaining H3 text encoder, video VAE, audio VAE, LoRA, custom nodes, compatibility, and local H3 inference are not verified.
- No real AutoDL task, cloud RTX 5090 render, or AutoDL credential flow has been exercised.
- No 1080x1920, 24fps, subtitle-burned, visually accepted five-second final video exists.
- The standard finish gate detects runtime/comfyui-local.err.log changed by the natural ComfyUI run although that log is outside this iteration's declared file scope; the log was not altered to bypass the gate.

### 运行观察对象
- 无

### 失败教训 / 下轮约束
- Do not interpret a partial model transfer, a dry-run response, a successful ComfyUI prompt, or a low-resolution smoke artifact as a completed H3 installation or final delivery.
- Do not retry or alter the protected transfer, its network path, or the completed Wan task without new user authorization and new evidence.
- Treat runtime log drift as an explicit governance blocker; do not restore, truncate, rename, or otherwise edit the log merely to satisfy a scope checker.
- Use the task baseline date 2026-09-03 as the ordering reference; later filesystem timestamps are untrusted anomaly data.

## 2026-09-04 04:43 | TASK-20260904-035538 | PARTIAL

- 摘要：统一项目控制层默认 API 到 127.0.0.1:8092，并完成 H3 dry-run、旧 8091 反例和下载延期状态的受控验证；未触碰用户独立 PowerShell 正在写入的 H3 权重，未提交云任务，也未声称 H3 安装完成或最终视频交付。
- 声明等级：static-only
- 下一步：Wait for explicit user confirmation that the independent PowerShell download has finished. Then start a separately authorized read-only H3 integrity/component audit. In a distinct follow-up iteration, wire the desired local ComfyUI browser-open behavior to a real UI URL if needed, and only after H3/component evidence authorize a 1080x1920, 24fps, approximately five-second final render with authored SUBTITLE_LOCK_V1 subtitles.

### 实际改动
- .env.example
- README_COMFYUI_PRODUCTION.md
- docs/DISK_AND_RUNTIME_PLAN.md
- docs/INSTALL_WINDOWS.md
- docs/TROUBLESHOOTING.md
- docs/WEB_INTEGRATION.md
- handoff/current_state.md
- scripts/check_comfyui_api.ps1
- scripts/start_comfyui_api.ps1
- src/comfyui_production/config.py
- tests/test_core_contracts.py

### 验证
- python scripts/run_project_tests.py: 33/33 passed
- python scripts/check_workflow_json.py: 8 workflow JSON files validated
- python scripts/run_api_smoke.py: 7/7 passed
- python scripts/secret_scan.py: no potential secrets found in 115 text files
- python scripts/check_h3_download_status.py: manifest_only, six artifacts PENDING, H3 remains DEFERRED
- powershell scripts/check_comfyui_api.ps1 -Port 8092: exit 0, MINIMAX_H3, BLOCKED_LOCAL_H3, DRY_RUN_ONLY, vendor_task_id null
- powershell scripts/check_comfyui_api.ps1 -Port 8091: expected exit 2, health-only capability failure, no replacement started
- verification_plan.py generated receipts for static-and-unit, workflow-spec, api-smoke, secret-scan, and protected-download-state

### 成功标准证据
- A fresh Settings instance and .env.example default COMFY_API_PORT to 8092 while explicit environment/.env/-Port values still take precedence.: 33/33 project tests passed, including the Settings and dotenv precedence contract tests.
- The launcher and checker share that default and distinguish a full H3-enabled control-plane listener from a health-only legacy listener without a process mutation.: 8092 capability check passed; 8091 returned the expected nonzero health-only capability error without starting or replacing a process.
- The operating documentation directs the management page to 8092 by default and retains the no-stop boundary for both observed listeners.: Updated project-local settings and operating documents; static contract tests passed.
- Tests pass, secret scan finds no credentials, and the H3 manifest remains deferred without a model-file inspection.: Project tests, workflow validation, API smoke, secret scan, and manifest-only H3 status check all passed.

### 未验证项
- The independent PowerShell transfer has not been confirmed to have returned to a prompt; the protected Ref2VA file was not accessed, enumerated, hashed, loaded, moved, renamed, or refreshed.
- The remaining H3 text encoder, video VAE, audio VAE, LoRA, custom nodes, compatibility, model-list recognition, and local H3 inference remain unverified.
- No real AutoDL request, cloud RTX 5090 render, or credential flow was exercised.
- No 1080x1920, 24fps, approximately five-second, dialogue-authored, subtitle-burned and visually accepted final video exists.
- COMFY_AUTO_OPEN is documented as an example but is not wired into the API launcher; the local ComfyUI UI still requires -OpenBrowser unless a separate safe launcher iteration is authorized.

### 运行观察对象
- 无

### 失败教训 / 下轮约束
- A partial model transfer, dry-run response, successful ComfyUI prompt, or low-resolution smoke artifact cannot prove H3 installation or final delivery.
- Do not retry or alter the protected transfer, its network path, either listener, or the completed Wan task without new authorization and evidence.
- Do not inspect or refresh the H3 model list until the user confirms the independent PowerShell window naturally returned to a prompt.
- Treat runtime log drift and future filesystem timestamps as evidence limits; do not edit logs or fabricate a PASS to satisfy a scope gate.

## 2026-09-04 05:30 | TASK-20260904-045550 | PARTIAL

- 摘要：补齐 SUBTITLE_LOCK_V1 ASS 只读预检、明确 1080x1920/24fps/约5秒的 CLOUD_5090_QUALITY 终版目标，并让本机 ComfyUI 启动脚本按 COMFY_AUTO_OPEN 选择性打开 UI；未触碰用户独立 PowerShell 正在写入的 H3 Ref2VA 权重，未修改网络，未提交云任务。
- 声明等级：static-only
- 下一步：等待用户确认独立 PowerShell 下载窗口已自然返回提示符；随后在单独授权下只读检查 Ref2VA 大小、修改时间、SHA-256、来源、节点兼容性和模型识别。另行获准后再重载 8092 验证 live 预设，并使用 AutoDL/RTX 5090 或已验证的云端链路生成 1080x1920、24fps、约5秒成片。

### 实际改动
- README_COMFYUI_PRODUCTION.md

### 验证
- python scripts/run_project_tests.py: 40/40 passed
- python scripts/check_workflow_json.py: 8 workflow JSON files validated
- python scripts/run_api_smoke.py: 7/7 passed
- python scripts/secret_scan.py: no potential secrets found in 116 text files
- python scripts/check_h3_download_status.py: manifest-only, six artifacts PENDING, H3 remains DEFERRED
- python scripts/validate_subtitles.py sample_assets/subtitles/SUBTITLE_LOCK_V1_preview.ass --video-width 1080 --video-height 1920: passed
- verification receipts generated for subtitle-preflight, project-regression, api-preset-contract, workflow-spec, secret-scan, and protected-download-state

### 成功标准证据
- A standard-library subtitle validator accepts the locked 1080x1920 ASS template plus authored events and rejects wrong canvas, out-of-range style, unsafe animation overrides, more than two lines, and malformed event timing.: 40/40 project tests passed, including six SUBTITLE_LOCK_V1 validator regression tests; the preview preflight receipt passed.
- CLOUD_5090_QUALITY reports a 1080x1920 delivery target, 24 fps, 121 frames, approximately 5.04 seconds, 9:16, 1080p竖, and an explicit SUBTITLE_LOCK_V1 burn requirement while LOCAL_DRAFT remains low resolution.: ApiApplication._presets() and the API smoke contract expose the target; project regression and api-preset-contract receipts passed.
- start_comfyui_local.ps1 resolves COMFY_AUTO_OPEN from process environment then project .env, preserves -OpenBrowser, and supports an explicit -NoBrowser suppression without restarting an existing service during verification.: Project regression passed the launcher contract; the script opens only after a healthy existing/new loopback server and honors -NoBrowser.
- Existing project tests, workflow validation, API smoke, secret scan, and manifest-only H3 guard continue to pass.: All declared static/runtime receipts passed; the H3 manifest remains six PENDING artifacts with no model-file inspection.

### 未验证项
- The independent PowerShell transfer has not been confirmed to have returned to a prompt; the protected Ref2VA file was not accessed, enumerated, hashed, loaded, moved, renamed, or refreshed.
- The remaining H3 text encoder, video VAE, audio VAE, LoRA, custom nodes, compatibility, model-list recognition, and local H3 inference remain unverified.
- The running 8092 process still serves an older preset payload until an explicitly authorized service reload; source and live runtime must not be conflated.
- No real AutoDL request, cloud RTX 5090 render, or credential flow was exercised.
- No 1080x1920, 24fps, authored-dialogue, subtitle-burned and visually accepted final video exists.

### 运行观察对象
- 无

### 失败教训 / 下轮约束
- A partial model transfer, dry-run response, successful ComfyUI prompt, or low-resolution smoke artifact cannot prove H3 installation or final delivery.
- Do not retry or alter the protected transfer, its network path, either listener, or the completed Wan task without new authorization and new evidence.
- Do not inspect or refresh the H3 model list until the user confirms the independent PowerShell window naturally returned to a prompt.
- A source-code preset change is not live-service evidence; after an authorized API reload, re-run the capability and preset checks.
- The subtitle validator is a preflight only; final delivery still requires an authored ASS, burn, media probe, frame QA, and output hash.

## 2026-09-04 06:05 | TASK-20260904-054420 | PARTIAL

- 摘要：在不触碰用户独立 PowerShell 正在写入的 MiniMax H3 Ref2VA 权重、不修改 Clash Verge/网络、不重启运行服务或提交云任务的前提下，完成控制层静态审计；移除 .env.example 中未接线的 COMFY_LOCAL_HOST/COMFY_LOCAL_PORT 示例，并补充 -Port/8092 使用说明，登记用户报告的进行中下载进度但不把它当作完整性证据。
- 声明等级：static-only
- 下一步：等待用户确认独立 PowerShell 下载窗口自然返回提示符；随后在单独授权下只读检查 Ref2VA 的最终大小、修改时间、SHA-256、来源、节点兼容性和模型识别。完整 H3 组件验证后，再由用户填写 AutoDL Token 并明确授权云端 RTX 5090 5 秒渲染，最后完成真实对白字幕烧录、媒体探测、抽帧 QA 和 hash。

### 实际改动
- .env.example
- docs/INSTALL_WINDOWS.md
- docs/MINIMAX_H3_STATUS.md
- handoff/current_state.md
- handoff/next_tasks.md
- tests/test_core_contracts.py

### 验证
- python G:\codex话术\agents\verification_plan.py run --id project-regression: exit 0
- python G:\codex话术\agents\verification_plan.py run --id workflow-spec: exit 0; 8 workflow JSON files valid
- python G:\codex话术\agents\verification_plan.py run --id api-smoke: exit 0
- python G:\codex话术\agents\verification_plan.py run --id subtitle-preflight: exit 0
- python G:\codex话术\agents\verification_plan.py run --id secret-scan: exit 0; no potential secrets found
- python G:\codex话术\agents\verification_plan.py run --id protected-download-state: exit 0; six artifacts PENDING / manifest_only

### 成功标准证据
- The example configuration no longer advertises unsupported COMFY_LOCAL_HOST/COMFY_LOCAL_PORT variables, and Windows launch docs state that -Port controls the local ComfyUI server.: Project regression passed the updated .env.example assertions and the Windows launch documentation contract.
- The source control plane retains COMFY_API_PORT=8092, the MINIMAX_H3 selector, BLOCKED_LOCAL_H3, DRY_RUN_ONLY, and both AutoDL workflow IDs.: Project regression, workflow validation, and API smoke all passed; no source or live-service mutation was performed.
- The H3 download guard remains manifest-only with six PENDING artifacts, DEFERRED verification, no hashes, and no model-file access.: The project-local manifest-only checker returned six PENDING artifacts; the protected G:\ComfyUI path was not accessed.
- Project tests, workflow JSON validation, API smoke, subtitle preflight, secret scan, and the guarded download-state check pass.: All six declared verification checks returned exit 0 and wrote current receipts.

### 未验证项
- 用户尚未确认独立 PowerShell 下载窗口已自然返回命令提示符；约 4,278,120,438 字节只是 2026-09-03 截图中的进行中进度，不是最终文件大小或 SHA-256。
- Ref2VA 及其余文本编码器、视频 VAE、音频 VAE、LoRA、节点兼容性和 ComfyUI 模型识别尚未检查。
- 运行中的 8092 进程仍可能提供旧的 576x1024 preset；未获维护授权，未重载服务，不能把源码的 1080x1920 目标当作 live 证据。
- 没有真实 AutoDL 请求、RTX 5090 云渲染或 1080x1920/24fps/字幕烧录终版视频。

### 运行观察对象
- 无

### 失败教训 / 下轮约束
- 活动下载的进度数字、dry-run 回包、旧 Wan smoke 或源码 preset 都不能证明 H3 安装完成或终版交付。
- 不要在用户确认 PowerShell 返回提示符前读取、哈希、加载或刷新 H3 权重/模型列表。
- 不要修改 Clash Verge、代理、网络或运行监听器；live 8092 的旧 preset 只能在明确维护授权后重载并重新验证。
- AutoDL 仍只允许 dry-run；真实 Token、云任务和费用需要用户后续明确授权。
