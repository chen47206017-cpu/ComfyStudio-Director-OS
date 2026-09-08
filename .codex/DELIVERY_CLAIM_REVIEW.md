# 交付声明复核

- 结果：`PARTIAL`
- 声明等级：`static-only`

## 用户成功标准
- The H3 catalog and dry-run response distinguish a project planning contract from a vendor-submittable AutoDL request body, and no longer fabricate ref_image_*/ref_audio_* fields for legacy v5/v2 wrappers. — H3 contract tests passed for catalog status, blocked vendor submission, image-only and image-plus-audio selection, planning_input-only output, and rejection of unsupported planner fields.
- Image-only planning still selects minimax_h3_lightx2v_v5 and image-plus-audio planning still selects minimax_h3_image_audio_to_video_v2, with hosted URL safety checks and no provider/job side effect. — The in-process API smoke suite passed H3 dry-run planning and paid-submit gate cases with no provider or job side effect from dry-run.
- The source recognizes 1080x1920 as the final delivery target but says the legacy H3 source resolution must be verified per current workflow drawer and cannot be claimed as direct 1080p. — Core contract tests and workflow JSON validation passed the target-only, unverified-vendor-schema contract across the source and documentation.
- The H3 workflow spec and public docs match the code's unverified-vendor-schema boundary. — 缺失
- Project regression, API smoke, workflow JSON validation, subtitle preflight, secret scan, and manifest-only download-state checks pass without accessing the protected model file. — All six declared checks returned exit 0; the download guard remained manifest-only and reported six deferred artifacts.

## 既有行为保持
- POST /api/comfyui/h3/dry-run remains no-I/O and keeps MINIMAX_H3 as BLOCKED_LOCAL_H3 / DRY_RUN_ONLY. — 缺失
- The two user-supplied workflow IDs remain registered in the selector: minimax_h3_lightx2v_v5 and minimax_h3_image_audio_to_video_v2. — 缺失
- AUTODL_ALLOW_PAID_SUBMIT remains disabled by default, and direct H3 job submission remains blocked with HTTP 409. — 缺失
- The user-managed H3 Ref2VA transfer, G:\ComfyUI, Clash Verge, network routing, live listeners, credentials, and cloud jobs are not accessed or changed. — 缺失

## 主动反证
- A source file or a stale document claims that v5/v2 accepts particular ref_image/ref_audio fields, duration limits, or direct 1080p output without an active workflow drawer verification. — 缺失：缺失
- The user-managed PowerShell transfer has not been confirmed to have naturally returned to a prompt. — 缺失：缺失
