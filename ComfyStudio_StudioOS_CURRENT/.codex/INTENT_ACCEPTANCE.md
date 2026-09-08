# 意图验收锁

> 编码前确认自然语言任务的真实含义；本文件不是对用户话语的自由补全。

- 请求摘要：在用户指定的 F 盘 CURRENT 生产工程中，从既有 V10.1 Director Demo 增量升级 V44 核心渲染路径、中文导演 UI、全能参考、可保存 ReactFlow 和严格视频验收；真实执行仅允许 local_comfy/127.0.0.1:8189，外部/付费 lanes 只显示明确阻塞。
- 原始请求：读取我附上的《ComfyStudio_StudioOS_V10.1-V44_30分钟实施快车道总控_v1.0.md》，立即进入 IMPLEMENTATION_FASTLANE_V44。不要重新写方案，不要停在只读审计，从第0节开始连续修改、测试、修复并生成证据。除文档规定的授权阻塞外不要暂停询问。
- 请求 SHA256：71fffeaff155424b795ef9c851ae632be69cde4cbea90013b7f83ef9b7e4b260
- 用户场景：导演在 http://127.0.0.1:8190/director/ 选择 SHOT002 和“本机 ComfyUI 8189”，点击生成。系统展示 Canon、Prompt、Capsule/Worker 预检、创建 Durable Job、提交 prompt 并轮询。只有下载到 StudioOS 受控输出目录且经 ftyp、ffprobe、视频流、时长、SHA-256 验证的 MP4 才显示“已完成”和视频播放器；无 MP4 时清楚显示失败或未验证。
- 可观察终态：导演台默认简体中文，显示本机/AutoDL/API lane 选择与全能参考；可见 ReactFlow 连线能保存、刷新恢复；后端 job 仅在 verified MP4 非空时转 SUCCEEDED；浏览器能播放经白名单 media route 暴露的已验证 MP4；测试、构建、运行时 preflight 和 run manifest 均采用 Asia/Shanghai +08:00 证据。

## 必须保持
- 保留既有 V8、V10、/api/prompt API、Demo JSON、Canvas CAS、Canon 规则和现有 SQLite job store 的历史记录
- 不删除、覆盖、移动或重写 database、assets、workflows、Canon、历史 reports、upgrade_logs 或用户输出
- 不停止、重启、升级、安装、删除、移动、哈希或修改 8189 Worker / ComfyUI runtime；仅通过 HTTP 调用其公开接口
- AutoDL5090 与 API 未配置时不得回退到本机、不得发起外部网络或付费调用
- 没有真实 decodable MP4、hash、ffprobe、Job/prompt history 和受控路径证据时不得声称 H3 或 Production READY 成功

## 正例
- Given lane=local_comfy 且 8189 可探测、Capsule 预检通过、参考图可上传 / When 导演对 SHOT002 点击生成 / Then 服务使用 local-8189 创建一个幂等 Job、保存 prompt_id 并且仅提交一次；随后的刷新仅查询 queue/history/outputs，不会自动二次提交
- Given history 返回图片、WAV、空文件、HTML 错误页或不可解析 .mp4 / When Job refresh 收集输出 / Then Job 转 FAILED，reason_code 为 OUTPUT_MP4_VERIFICATION_FAILED，运行时与 UI 不显示成功或视频播放器
- Given history 返回受控路径内的有效 MP4，且 ftyp、ffprobe、video stream、duration 和 SHA-256 均成功 / When Job refresh 完成 / Then Job 转 SUCCEEDED，Demo runtime 保存 output metadata，媒体仅可经 job output id route 播放
- Given 用户选择 AutoDL5090 或 API，尚无 URL/凭据/付费授权 / When 点击生成 / Then 返回中文 BLOCKED 和明确 reason_code，不发送任何外部请求

## 反例
- 场景：HTTP 200、H3 节点存在、workflow preflight READY、prompt 队列已接收、单元测试通过；不得：不得单独作为 MP4 或 READY_LOCAL_PRODUCTION 成功证据
- 场景：输出文件不在受控 StudioOS reports/job_outputs 根目录，或 output id 与 JobStore 无关；不得：不得通过 media route 暴露任意本机路径

## 已验证假设
- 无

## 未决问题
- 无
