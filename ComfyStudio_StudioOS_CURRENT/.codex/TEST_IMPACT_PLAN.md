# 回归测试影响候选（计划）

> 由静态 import 关系与测试命名匹配生成；它提示应阅读/运行的测试，不能证明覆盖完整。

## 计划改动范围
- `backend/app.py`
- `backend/v10_core.py`
- `frontend/vite.config.ts`
- `tests/test_backend_v10.py`
- `tests/test_comfy_execution.py`
- `tests/test_demo_v101.py`
- `tools/v101_runtime_probe.py`
- `backend/services/job_service.py`
- `backend/services/worker_registry.py`
- `backend/services/workflow_capsule.py`
- `frontend/src/main.tsx`

## 潜在受影响测试
- `tests/test_backend_v10.py` — 文件名与 `tests/test_backend_v10.py` 匹配
- `tests/test_comfy_execution.py` — 文件名与 `tests/test_comfy_execution.py` 匹配
- `tests/test_demo_v101.py` — 文件名与 `tests/test_demo_v101.py` 匹配

## 使用方式
将与本轮成功标准相关的候选纳入实际验证，并在 iteration-result.json 的 verification 中记录命令和结果。
