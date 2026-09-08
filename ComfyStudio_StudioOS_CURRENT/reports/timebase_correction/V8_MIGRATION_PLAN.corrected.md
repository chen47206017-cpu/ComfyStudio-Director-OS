# ComfyStudio StudioOS V8.0 Migration Plan

- Generated at (Asia/Shanghai): 2026-09-08T09:27:23+08:00
- Production source: F:\一人公司\comfyui-production\ComfyStudio_StudioOS_CURRENT
- Research-only environment: G:\我的文档\deepseek
- ComfyStudio endpoint: http://127.0.0.1:8190
- ComfyUI executor: http://127.0.0.1:8189

## Audit Findings

1. The real CURRENT directory is ComfyStudio_StudioOS_CURRENT; the nested path in the request does not exist.
2. ackend/app.py has a duplicate /api/shots endpoint and cannot import.
3. The current UI is a ReactFlow prototype with no API-backed canvas persistence.
4. Asset and Canon JSON files are valid and protected. ssets.json has the real asset list; studio.json has an empty legacy asset list.
5. ComfyUI 8189 is the execution engine and must be probed through its real HTTP API. Studio canvas JSON is not a ComfyUI workflow JSON.

## V8 Vertical Slice

1. Preserve protected JSON and create upgrade logs before writes.
2. Restore a bootable 8190 Flask application and retain legacy read routes.
3. Add atomic JSON storage, version status, canvas revision persistence, script parsing, Canon validation, prompt compilation, MemoryOS and QC report services.
4. Add a ComfyUI client for real system stats, object info, queue, history and prompt submission. Submission rejects missing workflow payloads and Canon failures; it never fabricates a result.
5. Upgrade the ReactFlow panel to load/save its canvas and run prompt/Canon/ComfyUI health actions through the backend.

## Deferred

- No EXE/installer.
- No historical-directory migration.
- No claim of successful H3 video generation until a real queued workflow completes and yields media evidence.

