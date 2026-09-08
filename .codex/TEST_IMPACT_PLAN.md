# 回归测试影响候选（计划）

> 由静态 import 关系与测试命名匹配生成；它提示应阅读/运行的测试，不能证明覆盖完整。

## 计划改动范围
- `ComfyStudio_StudioOS_CURRENT/backend/app.py`
- `ComfyStudio_StudioOS_CURRENT/ui/canvas.js`
- `ComfyStudio_StudioOS_CURRENT/backend/modules/prompt/compiler.py`
- `ComfyStudio_StudioOS_CURRENT/backend/modules/qc/qc_engine.py`
- `ComfyStudio_StudioOS_CURRENT/backend/modules/router/router.py`
- `ComfyStudio_StudioOS_CURRENT/backend/modules/script/parser.py`
- `ComfyStudio_StudioOS_CURRENT/reports/V8_backup_20260908_004712/backend/app.py`
- `ComfyStudio_StudioOS_CURRENT/reports/V8_backup_20260908_004712/ui/canvas.js`
- `ComfyStudio_StudioOS_CURRENT/reports/V8_backup_20260908_004712/backend/modules/prompt/compiler.py`
- `ComfyStudio_StudioOS_CURRENT/reports/V8_backup_20260908_004712/backend/modules/qc/qc_engine.py`
- `ComfyStudio_StudioOS_CURRENT/reports/V8_backup_20260908_004712/backend/modules/router/router.py`
- `ComfyStudio_StudioOS_CURRENT/reports/V8_backup_20260908_004712/backend/modules/script/parser.py`

## 潜在受影响测试
- 未发现直接关联测试；请检查验证候选、README 或 CI 配置，不能据此认定无需回归。

## 使用方式
将与本轮成功标准相关的候选纳入实际验证，并在 iteration-result.json 的 verification 中记录命令和结果。
