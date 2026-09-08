# 本轮任务代码上下文候选

> 自动按关键词匹配；它提示优先阅读的事实，不代表这些文件已获准修改。

- 任务查询：读取我附上的《ComfyStudio_StudioOS_V10.1-V44_30分钟实施快车道总控_v1.0.md》，立即进入 IMPLEMENTATION_FASTLANE_V44。不要重新写方案，不要停在只读审计，从第0节开始连续修改、测试、修复并生成证据。除文档规定的授权阻塞外不要暂停询问。 不升级或重新搭建 ComfyUI，不改变 8189 的进程生命周期 不实现付费 AutoDL/API 真执行；只实现明确的可选入口与阻塞语义 不创建假 MP4、假 prompt_id、假截图、假 preflight 或假测试结果 不为版本账本生成没有真实工程入口的 Demo/空壳页面 不迁移或重写 protected JSON/SQLite schema；优先利用已有 JobStore 和附属证据 JSON
- 关键词：读取我附上的、comfystudio_studioos_v10.1-v44_30、分钟实施快车道总控、_v1.0.md、立即进入、implementation_fastlane_v44、不要重新写方案、不要停在只读审计、从第、节开始连续修改、测试、修复并生成证据、除文档规定的授权阻塞外不要暂停询问、不升级或重新搭建、comfyui、不改变、8189、的进程生命周期、不实现付费、autodl、api、真执行、只实现明确的可选入口与阻塞语义、不创建假、mp4、prompt_id、假截图、preflight、或假测试结果、不为版本账本生成没有真实工程入口的、demo、空壳页面、不迁移或重写、protected、json、sqlite、schema、优先利用已有、jobstore、和附属证据

## 优先阅读的源码
### [304] `backend/app.py`
```text
2: 
3: The application owns the stable absolute paths and the V10 API contract.  Older
4: V8 modules remain on disk for compatibility, while this entry point avoids their
```
### [190] `frontend/src/main.tsx`
```text
81: 
82: type DemoShot = {
83:   id: string
```
### [82] `reports/V921_UI_router_20260908_031517/v8_routes.py`
```text
1: 
2: from flask import Blueprint,jsonify,request,send_from_directory
3: import os
```
### [82] `reports/V924_ROUTE_CLEAN_20260908_032432/v8_routes.py`
```text
1: 
2: from flask import Blueprint,jsonify,request,send_from_directory
3: import os
```
### [81] `reports/V921_HOME_FIX_20260908_030335/v8_routes.py`
```text
1: 
2: from flask import Blueprint,jsonify,request
3: 
```
### [78] `backend/routes/v8_routes.py`
```text
1: 
2: from flask import Blueprint,jsonify,request,send_from_directory
3: import os
```
### [78] `reports/V921_UI_router_20260908_030204/v8_routes.py`
```text
1: 
2: from flask import Blueprint,jsonify,request
3: 
```
### [78] `reports/fastlane_backup_20260908_052127/backend/routes/v8_routes.py`
```text
1: 
2: from flask import Blueprint,jsonify,request,send_from_directory
3: import os
```

## 优先阅读的测试
### [72] `tests/test_backend_v10.py`
```text
12: from app import create_app  # noqa: E402
13: from services.job_service import JobStore  # noqa: E402
14: 
```
### [18] `tests/test_demo_v101.py`
```text
11: 
12: class DemoV101Tests(unittest.TestCase):
13:     def setUp(self):
```
### [11] `tests/test_comfy_execution.py`
```text
9: from v10_core import ComfyClient  # noqa: E402
10: from services.job_service import JobStore  # noqa: E402
11: 
```

## 相关代码符号
- [8] `backend/app.py:85` — function `_demo_json`
- [5] `backend/services/job_service.py:36` — method `JobStore._init_schema`
- [4] `backend/app.py:48` — function `_json_body`
- [4] `backend/app.py:89` — function `_demo_state`
- [4] `backend/app.py:94` — function `_save_demo_state`
- [4] `backend/services/job_service.py:23` — class `JobStore`
- [4] `backend/services/workflow_capsule.py:54` — method `WorkflowCapsuleStore.preflight`
- [4] `backend/v10_core.py:53` — function `read_json`
- [4] `backend/v10_core.py:67` — function `atomic_write_json`
- [4] `backend/v8/storage/atomic_json.py:27` — function `read_json`
- [4] `frontend/src/main.tsx:228` — class `ApiError`
- [4] `frontend/src/main.tsx:241` — function `summarizeApiPayload`

## 直接本地依赖方
- 未解析到命中符号所在文件的直接本地依赖方。

## 项目事实入口
- `CURRENT_STATUS.md`
- `HANDOFF_LATEST.md`
- `.codex/CODEBASE_MAP.md`
- `.codex/MODULE_RELATIONSHIPS.md`
- `.codex/CODE_SYMBOLS.md`
- `.codex/decisions.md` 与 `.codex/bugs.md`

## 使用边界
先阅读候选文件和符号确认职责；再结合模块关系图检查入边/出边，最后在任务契约中限定允许修改的文件和函数。关键词命中和依赖关系都不是修改授权。
