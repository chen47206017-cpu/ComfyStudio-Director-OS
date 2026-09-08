# 回归测试影响候选（实际）

> 由静态 import 关系与测试命名匹配生成；它提示应阅读/运行的测试，不能证明覆盖完整。

## 实际改动范围
- `docs/AUTODL_COMFYUI_API.md`
- `docs/CLOUD_5090.md`
- `docs/H3_WORKFLOW.md`
- `docs/WEB_INTEGRATION.md`
- `src/comfyui_production/h3.py`
- `src/comfyui_production/server.py`
- `tests/test_core_contracts.py`
- `tests/test_h3_contracts.py`
- `workflows/specs/07_minimax_h3_unified.json`

## 潜在受影响测试
- `tests/test_core_contracts.py` — 文件名与 `tests/test_core_contracts.py` 匹配
- `tests/test_h3_contracts.py` — 文件名与 `src/comfyui_production/h3.py` 匹配
- `tests/test_minimax_h3_download_guard.py` — 文件名与 `src/comfyui_production/h3.py` 匹配
- `tests/test_server.py` — 文件名与 `src/comfyui_production/server.py` 匹配

## 使用方式
将与本轮成功标准相关的候选纳入实际验证，并在 iteration-result.json 的 verification 中记录命令和结果。
