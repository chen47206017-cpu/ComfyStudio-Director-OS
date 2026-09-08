# 验证候选

> 自动从项目文件提取；未执行，不代表命令在当前环境已经成功。

## 任务成功标准
- 导演台有真实 <select> lane 控件，默认 local_comfy；AutoDL5090/API 在未配置时以中文 BLOCKED 返回且不外发
- SHOT002 generate 真正走 Canon -> Prompt -> Capsule preflight -> upload -> /prompt -> Durable Job，不因 refresh 重复 submit
- Workflow 在内存深拷贝后才注入 prompt/duration/seed/reference；Capsule 预检记录 workflow/capsule hash、worker snapshot 和阻塞原因
- 任何非 MP4、空/错误文件、没有 ftyp、ffprobe 失败、无 video stream 或时长非正的输出都不能使 Job SUCCEEDED
- 可验证 MP4 保存 SHA-256、mime、时长和 ffprobe 证据；Demo runtime 只为 verified MP4 保存 SUCCEEDED
- 已验证 Job output 只能通过 job_id/output_id 白名单 route 播放；路径穿越、其他文件和未验证 output 被拒绝
- 前端在 verified MP4 存在时显示视频播放器、时长、哈希短码和 Job ID；不存在时清楚显示未取得可验证 MP4
- 默认 Director UI 使用中文，已有 ReactFlow edges 和 bindings 能保存、刷新恢复，且有真实全能参考预设/绑定数据行为
- 根解析不硬编码用户中文绝对路径，使用环境变量、root marker 和有限候选；原路径仍可兼容
- Python 单元/集成、TypeScript、Vite build、真实 HTTP preflight、Director 界面关键验收和 V44 manifest 都有当前北京时间证据
- 仅在真实 mp4、ffprobe、hash、history、Job chain、Director 界面播放都齐全时允许最终 READY_LOCAL_PRODUCTION；否则 manifest 必须降级为 PARTIAL、READY_CORE/H3_BLOCKED 或 BLOCKED_EXTERNAL

## 可审阅命令候选
- `python -m pytest` — 来源：pytest.ini、tox.ini 或 tests 目录

## 使用边界
先选择与本轮成功标准直接相关的最小命令，再实际执行并将结果写入 iteration-result.json。语法检查不能单独证明功能已修复。
