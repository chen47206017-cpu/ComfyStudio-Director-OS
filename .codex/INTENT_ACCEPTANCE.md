# 意图验收锁

> 编码前确认自然语言任务的真实含义；本文件不是对用户话语的自由补全。

- 请求摘要：在现有 F 盘 CURRENT 工程上完成可回滚的 V8.0 垂直切片，恢复 8190 启动并接通画布、Canon、Prompt、脚本、ComfyUI 和基础 QC。
- 原始请求：在北京时间记录的本次生产迭代中，先扫描并备份 F:/一人公司/comfyui-production/ComfyStudio_StudioOS_CURRENT，确认 G:/我的文档/deepseek 只作研发环境；将当前无法启动的 ComfyStudio Director Factory V4/V5 基线升级为可运行的 StudioOS Production Core V8.0 垂直切片，保留既有数据库和 Canon 规则，真实接入 ReactFlow 画布持久化、脚本解析、Canon 阻断、Prompt 编译、ComfyUI 127.0.0.1:8189 路由、基础 QC 报告，并验证 127.0.0.1:8190 与 8189 调用；不修改历史版本目录，不生成空壳，不做 EXE/安装器。
- 请求 SHA256：14e9a727df100a4d73b0fb11ccb5e99a04afffb47bfe7225284296b51d8e6dbe
- 用户场景：用户需要一个真正运行的本地短剧导演台：F 盘负责生产，G 盘只负责研发；导演台通过 8190 编排并调用 8189 执行。
- 可观察终态：CURRENT 下存在本次北京时间备份和迁移报告；8190 可启动并返回 V8 状态，画布可保存，Canon 违规会阻断，Prompt 可编译，脚本可拆镜头，ComfyUI 8189 健康/路由接口可被真实调用。

## 必须保持
- F 盘 CURRENT 是唯一修改目标，历史版本目录保持不变。
- 既有 database/assets/workflows 内容保留，Canon 规则逐条保留。
- G:\我的文档\deepseek 仅作研发环境，本次不写入。
- ComfyStudio 监听 127.0.0.1:8190，ComfyUI 监听 127.0.0.1:8189。

## 正例
- Given CURRENT 已完成只读审计且 8189 返回健康状态。 / When 创建带北京时间戳的备份后升级后端和前端，并启动 8190。 / Then /api/v8/status、/api/v8/canvas、/api/v8/canon/validate、/api/v8/prompt/compile、/api/v8/comfyui/health 可用，违规 Canon 返回阻断。

## 反例
- 场景：修改历史版本目录、覆盖既有 database/canon.json、把 G 盘研发目录当生产目录。；不得：不得执行，必须停止并保留备份。
- 场景：只显示 ReactFlow 演示节点、只返回固定 READY、或伪造 8189 生成结果。；不得：不得宣称 V8 闭环完成。

## 已验证假设
- F:\一人公司\comfyui-production\ComfyStudio_StudioOS_CURRENT 是当前实际生产主工程。 — verified：2026-09-08 北京时间目录审计：该路径存在且包含 backend/ui/database/assets/workflows。
- G:\我的文档\deepseek 是研发环境，不是本次生产代码目录。 — verified：2026-09-08 北京时间用户明确边界；本次只读访问并未把它作为生产源码目标。
- ComfyUI 127.0.0.1:8189 当前可达。 — verified：2026-09-08 北京时间审计代理读取 /system_stats 与 /object_info 成功。

## 未决问题
- 无
