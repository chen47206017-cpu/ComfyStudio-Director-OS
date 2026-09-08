# 最新交接

> 本文件由 iteration_recap.py 在显式 `--promote-handoff` 后更新。

## 最近任务

- 日期：2026-09-04 05:30
- 任务 ID：TASK-20260904-045550
- 用户目标：补齐 SUBTITLE_LOCK_V1 ASS 只读预检、明确 1080x1920/24fps/约5秒的 CLOUD_5090_QUALITY 终版目标，并让本机 ComfyUI 启动脚本按 COMFY_AUTO_OPEN 选择性打开 UI；未触碰用户独立 PowerShell 正在写入的 H3 Ref2VA 权重，未修改网络，未提交云任务。
- 实际改动：README_COMFYUI_PRODUCTION.md
- 未改动范围：请以本任务契约的 non_goals 为准。

## 验证与结果

- 结果：PARTIAL
- 声明等级：static-only
- 执行的验证：python scripts/run_project_tests.py: 40/40 passed; python scripts/check_workflow_json.py: 8 workflow JSON files validated; python scripts/run_api_smoke.py: 7/7 passed; python scripts/secret_scan.py: no potential secrets found in 116 text files; python scripts/check_h3_download_status.py: manifest-only, six artifacts PENDING, H3 remains DEFERRED; python scripts/validate_subtitles.py sample_assets/subtitles/SUBTITLE_LOCK_V1_preview.ass --video-width 1080 --video-height 1920: passed; verification receipts generated for subtitle-preflight, project-regression, api-preset-contract, workflow-spec, secret-scan, and protected-download-state
- 运行观察对象：无
- 未验证项：The independent PowerShell transfer has not been confirmed to have returned to a prompt; the protected Ref2VA file was not accessed, enumerated, hashed, loaded, moved, renamed, or refreshed.; The remaining H3 text encoder, video VAE, audio VAE, LoRA, custom nodes, compatibility, model-list recognition, and local H3 inference remain unverified.; The running 8092 process still serves an older preset payload until an explicitly authorized service reload; source and live runtime must not be conflated.; No real AutoDL request, cloud RTX 5090 render, or credential flow was exercised.; No 1080x1920, 24fps, authored-dialogue, subtitle-burned and visually accepted final video exists.

## 下一步与注意事项

- 下一步：等待用户确认独立 PowerShell 下载窗口已自然返回提示符；随后在单独授权下只读检查 Ref2VA 大小、修改时间、SHA-256、来源、节点兼容性和模型识别。另行获准后再重载 8092 验证 live 预设，并使用 AutoDL/RTX 5090 或已验证的云端链路生成 1080x1920、24fps、约5秒成片。
- 不要重复的失败尝试：A partial model transfer, dry-run response, successful ComfyUI prompt, or low-resolution smoke artifact cannot prove H3 installation or final delivery.; Do not retry or alter the protected transfer, its network path, either listener, or the completed Wan task without new authorization and new evidence.; Do not inspect or refresh the H3 model list until the user confirms the independent PowerShell window naturally returned to a prompt.; A source-code preset change is not live-service evidence; after an authorized API reload, re-run the capability and preset checks.; The subtitle validator is a preflight only; final delivery still requires an authored ASS, burn, media probe, frame QA, and output hash.
