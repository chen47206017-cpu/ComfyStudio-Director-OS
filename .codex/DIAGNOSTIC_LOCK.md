# 缺陷诊断锁

> 本文件锁定本轮唯一运行事实和唯一可证伪假设；验证失败后不得直接追加第二个补丁。

## 本次运行事实
- 版本：comfyui-production v0.1-local-autodl
- 观察时间：current task; filesystem timestamps after September 3, 2026 are untrusted
- 证据来源：read-only loopback capability audit
- 实际阻塞点：8091 lacks the H3 capability routes while project defaults select it.
- 目标路径已执行：是

## 唯一假设
- 假设：Moving the project default to 8092 and checking the catalog plus dry-run route prevents a management page from silently selecting the stale 8091 control plane.
- 支持证据：8091 health returned 200 but /engines and /h3/dry-run returned 404.；8092 returned 200 for health, the MINIMAX_H3 catalog, and a DRY_RUN_ONLY plan.
- 证伪条件：The default checker targets 8092 but cannot receive the expected MINIMAX_H3 catalog and DRY_RUN_ONLY plan.

## 稳定基线
- 状态：known
- 路径：127.0.0.1:8092/api/comfyui
- 已证实行为：Full H3 control-plane routes respond without model, cloud, or vendor network I/O.
- 对比范围：127.0.0.1:8091 only responds to health and is route-incomplete.

## 补丁预算与停止条件
- 最多文件：11
- 最多符号：2
- 最多改动行：260
- 最多改动块：24
- 每轮假设性补丁：1
- 验证失败后：If the capability probe cannot be implemented and verified within scope without a service mutation, stop and document the explicit 8092 workaround.
