# 验证证据来源

> 缺陷任务 PASS 的每条成功标准必须有可追溯的来源、时间与证据类型。

## The H3 catalog and dry-run response distinguish a project planning contract from a vendor-submittable AutoDL request body, and no longer fabricate ref_image_*/ref_audio_* fields for legacy v5/v2 wrappers.
- 结论：H3 contract tests passed for catalog status, blocked vendor submission, image-only and image-plus-audio selection, planning_input-only output, and rejection of unsupported planner fields.
- 类型：automated_test
- 来源：.codex/verification-receipts/project-regression.stderr.log
- 观察时间：2026-09-04 current session; verifier receipt clock reported 2026-09-05 and is not used as chronology evidence

## Image-only planning still selects minimax_h3_lightx2v_v5 and image-plus-audio planning still selects minimax_h3_image_audio_to_video_v2, with hosted URL safety checks and no provider/job side effect.
- 结论：The in-process API smoke suite passed H3 dry-run planning and paid-submit gate cases with no provider or job side effect from dry-run.
- 类型：automated_test
- 来源：.codex/verification-receipts/api-smoke.stderr.log
- 观察时间：2026-09-04 current session; verifier receipt clock reported 2026-09-05 and is not used as chronology evidence

## The source recognizes 1080x1920 as the final delivery target but says the legacy H3 source resolution must be verified per current workflow drawer and cannot be claimed as direct 1080p.
- 结论：Core contract tests and workflow JSON validation passed the target-only, unverified-vendor-schema contract across the source and documentation.
- 类型：automated_test
- 来源：.codex/verification-receipts/workflow-spec.stdout.log
- 观察时间：2026-09-04 current session; verifier receipt clock reported 2026-09-05 and is not used as chronology evidence

## The H3 workflow spec and public docs match the code's unverified-vendor-schema boundary.
- 结论：缺失
- 类型：缺失
- 来源：缺失
- 观察时间：缺失

## Project regression, API smoke, workflow JSON validation, subtitle preflight, secret scan, and manifest-only download-state checks pass without accessing the protected model file.
- 结论：All six declared checks returned exit 0; the download guard remained manifest-only and reported six deferred artifacts.
- 类型：automated_test
- 来源：.codex/verification-receipts/protected-download-state.stdout.log
- 观察时间：2026-09-04 current session; verifier receipt clock reported 2026-09-05 and is not used as chronology evidence
