# 本机 Wan2.1 I2V 5 秒验收记录

验收状态：ComfyUI 历史记录为 `success`；机器记录的完成时间保存在 `run_metadata.json`。

## 结论

本机 ComfyUI 的 Wan2.1 I2V API 工作流已经通过真实运行验证。它能够将
`F:\AI短剧\苏晚晴45.png` 作为首帧/CLIP Vision 参考图，生成竖屏约 5 秒 MP4。

这是“本机可执行、可调用、可产出媒体”的基线验收，不是最终真人短剧画质验收。抽取的
0:00、0:02.50 和结尾帧可见明显颗粒、面部扭曲及身份漂移；在现有 RTX 5060 Ti 16 GB
配置上，它适合调通 API 和低分辨率预览，不应作为最终成片工作流。

## 已验证的工作流

- 已验证文件：`F:\一人公司\comfyui-production\workflows\wan2.1_i2v_ref_5s_local.json`
- 提交接口：`POST http://127.0.0.1:8188/prompt`
- `prompt_id`：`f6eaeeb7-8127-43ce-aa93-b3829c1ad404`
- ComfyUI 历史状态：`success`
- 未返回节点校验错误或执行错误。

工作流参数：

- 模型：`Wan2.1/wan2.1_i2v_720p_14B_fp8_scaled.safetensors`
- 文本编码器：`umt5_xxl_fp8_e4m3fn_scaled.safetensors`
- VAE：`wan_2.1_vae.safetensors`
- CLIP Vision：`clip_vision_h.safetensors`
- 首帧参考：`G:\ComfyUI\input\suwanqing45_ref.png`（从用户图片复制）
- 控制视频：`G:\ComfyUI\input\10000.mp4`
- 分辨率：432 x 768（9:16）
- 帧数与帧率：121 帧、24 fps
- 采样：24 steps，`dpmpp_3m_sde`，`karras`，seed `20260903`

## 输出证据

- 原始输出：`G:\ComfyUI\output\wanvideo_suwanqing_ref_5s_local_00001.mp4`
- 交付镜像：`F:\一人公司\comfyui-production\artifacts\wan2.1_i2v_suwanqing_5s\wanvideo_suwanqing_ref_5s_local_00001.mp4`
- 时长：5.04 秒
- 媒体：H.264 NVENC、yuv420p、432 x 768、24 fps、121 帧
- 文件大小：7,953,520 bytes
- SHA-256：`0E7C41318A7EBC27BDCF88F4A057073B66213D429AEFFD2BCED8797218F04AB6`
- 运行元数据：`F:\一人公司\comfyui-production\artifacts\wan2.1_i2v_suwanqing_5s\run_metadata.json`

首帧、中间帧和末帧分别保存为 `frame_000.png`、`frame_2_50.png` 和
`frame_last.png`，便于后续做自动或人工质量门控。

## 原有 API JSON 评估

`G:\ComfyUI\wan_api_fixed_9x16.json` 的节点和本机模型引用均可用，但其设定为
432 x 768、81 帧、24 fps，实际时长约为 3.38 秒，不能直接满足 5 秒验收。
将 `VHS_LoadVideo.frame_load_cap` 与 `WanFunControlToVideo.length` 同步改为 121，
并将 `LoadImage.image` 改为 `suwanqing45_ref.png` 后，即可形成此次已验证的 5 秒竖屏基线。

`G:\ComfyUI\wan_api_wan22_9x16.json` 不可作为当前正式工作流：它引用
`Wan22FunControlToVideo`，但本机只有 Wan2.1 I2V 权重和 Wan2.1 VAE，属于节点/权重
版本不匹配的未验证模板。

## 运行备注

本次真实渲染耗时约 46 分钟。采样期间 GPU 利用率达到 100%，显存使用约 12 GB；没有下载
任何模型或调用任何付费云 API。
