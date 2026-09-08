# 验证候选

> 自动从项目文件提取；未执行，不代表命令在当前环境已经成功。

## 任务成功标准
- 升级前在 CURRENT/reports 下生成带北京时间戳的备份清单和迁移报告，且既有 database/assets/canon/shots/reference/projects/studio、assets、workflows 文件内容未被覆盖。
- backend/app.py 可导入并启动，不再因重复 /api/shots endpoint 崩溃；/api/status 保持兼容且新增 V8 版本状态。
- ReactFlow 画布从后端加载并可保存到 database/canvas.json，节点/连线包含稳定类型和数据。
- Script Parser 对 txt/md 文本输出 episode、scenes、shots；Canon Engine 对年份、年龄、服装、场景、道具、声音执行可观察校验，违规时阻断。
- Prompt Compiler 将 Shot、Asset、Canon、Memory 编译为 positive、negative、reference_list，用户反向禁止词不会被放入 positive。
- ComfyUI Router 真实调用 127.0.0.1:8189 的 system_stats/object_info/queue，并对提交接口保留真实响应或明确错误，不伪造结果。
- 基础 QC API 生成可读取 HTML 报告，Memory API 可保存成功/失败案例和模型评分。
- 在不修改历史版本和既有 Canon/资产 JSON 的前提下，8190 端到端健康验证通过；任何未完成的真实视频生成明确标记为 PARTIAL。

## 可审阅命令候选
- `python -m pytest` — 来源：pytest.ini、tox.ini 或 tests 目录

## 使用边界
先选择与本轮成功标准直接相关的最小命令，再实际执行并将结果写入 iteration-result.json。语法检查不能单独证明功能已修复。
