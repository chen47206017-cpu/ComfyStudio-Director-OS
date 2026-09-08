# 本轮任务代码上下文候选

> 自动按关键词匹配；它提示优先阅读的事实，不代表这些文件已获准修改。

- 任务查询：在北京时间记录的本次生产迭代中，先扫描并备份 F:/一人公司/comfyui-production/ComfyStudio_StudioOS_CURRENT，确认 G:/我的文档/deepseek 只作研发环境；将当前无法启动的 ComfyStudio Director Factory V4/V5 基线升级为可运行的 StudioOS Production Core V8.0 垂直切片，保留既有数据库和 Canon 规则，真实接入 ReactFlow 画布持久化、脚本解析、Canon 阻断、Prompt 编译、ComfyUI 127.0.0.1:8189 路由、基础 QC 报告，并验证 127.0.0.1:8190 与 8189 调用；不修改历史版本目录，不生成空壳，不做 EXE/安装器。 本轮不实现 EXE/安装器，不迁移或重写历史版本，不重构既有资产数据库 schema，不生成不存在的 H3 workflow。
- 关键词：在北京时间记录的本次生产迭代中、先扫描并备份、一人公司、comfyui-production、comfystudio_studioos_current、确认、我的文档、deepseek、只作研发环境、将当前无法启动的、comfystudio、director、factory、v4、v5、基线升级为可运行的、studioos、production、core、v8.0、垂直切片、保留既有数据库和、canon、规则、真实接入、reactflow、画布持久化、脚本解析、阻断、prompt、编译、comfyui、127.0.0.1、8189、路由、基础、qc、报告、并验证、8190、调用、不修改历史版本目录、不生成空壳、不做、exe、安装器、本轮不实现、不迁移或重写历史版本、不重构既有资产数据库、schema、不生成不存在的、h3、workflow

## 优先阅读的源码
### [460] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyUI_MiniMax_H3_Extender/extender.py`
```text
1: """
2: MiniMax H3 Extender
3: ===================
```
### [460] `staging/h3-extender-88cc10d4/ComfyUI_MiniMax_H3_Extender-88cc10d4db3d51f88e6a3fe097f5a750edf05ab3/extender.py`
```text
1: """
2: MiniMax H3 Extender
3: ===================
```
### [377] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/comfy_api_nodes/nodes_kling.py`
```text
39:     MotionControlRequest,
40:     MultiPromptEntry,
41:     OmniImageParamImage,
```
### [314] `runtime/temp/install_comfystudio_manager_v1.py`
```text
20: # ============================================================
21: # 0. Canonical paths
22: # ============================================================
```
### [304] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/execution.py`
```text
25: import nodes
26: from comfy_execution.caching import (
27:     BasicCache,
```
### [288] `runtime/temp/install_comfystudio_v3_0.py`
```text
4: 
5: ROOT=Path(r"F:\一人公司\comfyui-production")
6: H3_ROOT=ROOT/"staging"/"comfyui-v0.34.0"/"ComfyUI-0.34.0"
```
### [280] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/comfy_api_nodes/apis/__init__.py`
```text
101:     input_image: str = Field(..., description='Base64 encoded image to be edited')
102:     prompt: str = Field(
103:         ..., description='The text prompt describing what to edit on the image'
```
### [276] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyUI_MiniMax_H3_Extender/motion_context_disk.py`
```text
1: """
2: MiniMax H3 Motion Context - disk-backed sequential chain (v13 clean).
3: 
```

## 优先阅读的测试
### [140] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/tests/execution/test_execution.py`
```text
15: import urllib.error
16: from comfy_execution.graph_utils import GraphBuilder, Node
17: 
```
### [133] `tests/api_smoke.py`
```text
1: """Runnable standard-library smoke tests for the local ComfyUI API.
2: 
```
### [112] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/tests/execution/test_jobs.py`
```text
1: """Unit tests for comfy_execution/jobs.py"""
2: 
```
### [96] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/tests/execution/test_preview_method.py`
```text
3: 
4: Tests actual execution with different preview_method values.
5: Requires a running ComfyUI server with models.
```
### [89] `tests/test_core_contracts.py`
```text
11: 
12: from comfyui_production.config import Settings, _read_dotenv
13: from comfyui_production.media import MediaError, MediaResolver, clean_path_text
```
### [87] `tests/test_server.py`
```text
9: 
10: from comfyui_production.config import Settings
11: from comfyui_production.server import ApiApplication, ApiError, ApiHTTPServer, create_server
```
### [84] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/tests-unit/assets_test/test_list_filter.py`
```text
9: from app.assets.api import routes as assets_routes
10: from app.assets.api import schemas_in
11: 
```
### [75] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/tests-unit/folder_paths_test/system_user_test.py`
```text
3: Tests cover:
4: - get_system_user_directory(): Internal API for custom nodes to access System User directories
5: - get_public_user_directory(): HTTP endpoint access with System User blocking
```

## 相关代码符号
- [10] `src/comfyui_production/h3.py:39` — function `is_minimax_h3_workflow_id`
- [9] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyStudio_Asset_Library/nodes.py:982` — class `ComfyStudioCanonFile`
- [9] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyUI_MiniMax_H3_Extender/prompt_bridge.py:57` — class `MiniMaxH3PromptPackBridge`
- [9] `staging/comfyui-v0.34.0/ComfyUI-0.34.0/execution.py:664` — class `PromptExecutor`
- [9] `staging/h3-extender-88cc10d4/ComfyUI_MiniMax_H3_Extender-88cc10d4db3d51f88e6a3fe097f5a750edf05ab3/prompt_bridge.py:57` — class `MiniMaxH3PromptPackBridge`
- [7] `ComfyStudio_StudioOS_CURRENT/backend/app.py:104` — function `canon`
- [7] `ComfyStudio_StudioOS_CURRENT/backend/app.py:116` — function `prompt`
- [7] `ComfyStudio_StudioOS_CURRENT/backend/modules/prompt/compiler.py:1` — class `PromptCompiler`
- [7] `ComfyStudio_StudioOS_CURRENT/backend/modules/qc/qc_engine.py:1` — class `QC`
- [7] `ComfyStudio_StudioOS_CURRENT/reports/V8_backup_20260908_004712/backend/app.py:104` — function `canon`
- [7] `ComfyStudio_StudioOS_CURRENT/reports/V8_backup_20260908_004712/backend/app.py:116` — function `prompt`
- [7] `ComfyStudio_StudioOS_CURRENT/reports/V8_backup_20260908_004712/backend/modules/prompt/compiler.py:1` — class `PromptCompiler`

## 直接本地依赖方
- `src/comfyui_production/server.py` imports `src/comfyui_production/h3.py`
- `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyStudio_Asset_Library/__init__.py` imports `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyStudio_Asset_Library/nodes.py`
- `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyUI_MiniMax_H3_Extender/__init__.py` imports `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyUI_MiniMax_H3_Extender/prompt_bridge.py`
- `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyUI_MiniMax_H3_Extender/extender.py` imports `staging/comfyui-v0.34.0/ComfyUI-0.34.0/custom_nodes/ComfyUI_MiniMax_H3_Extender/prompt_bridge.py`
- `staging/h3-extender-88cc10d4/ComfyUI_MiniMax_H3_Extender-88cc10d4db3d51f88e6a3fe097f5a750edf05ab3/__init__.py` imports `staging/h3-extender-88cc10d4/ComfyUI_MiniMax_H3_Extender-88cc10d4db3d51f88e6a3fe097f5a750edf05ab3/prompt_bridge.py`
- `staging/h3-extender-88cc10d4/ComfyUI_MiniMax_H3_Extender-88cc10d4db3d51f88e6a3fe097f5a750edf05ab3/extender.py` imports `staging/h3-extender-88cc10d4/ComfyUI_MiniMax_H3_Extender-88cc10d4db3d51f88e6a3fe097f5a750edf05ab3/prompt_bridge.py`

## 项目事实入口
- `CURRENT_STATUS.md`
- `HANDOFF_LATEST.md`
- `.codex/CODEBASE_MAP.md`
- `.codex/MODULE_RELATIONSHIPS.md`
- `.codex/CODE_SYMBOLS.md`
- `.codex/decisions.md` 与 `.codex/bugs.md`

## 使用边界
先阅读候选文件和符号确认职责；再结合模块关系图检查入边/出边，最后在任务契约中限定允许修改的文件和函数。关键词命中和依赖关系都不是修改授权。
