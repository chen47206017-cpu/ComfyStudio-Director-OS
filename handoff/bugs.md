# 已知阻塞与风险

- 先前 Wan 使用 `dpmpp_3m_sde/karras` 在 KSampler 节点因 CPU 内存不足失败；后续 `euler/simple/16` 重试已技术成功，但只能作为 smoke 记录。
- 该 `432x768` smoke 不是用户锁定的 `1080x1920` 成片；抽帧显示重颗粒/过处理人脸与极弱动作，且字幕模板未烧录到候选，故已标记 `REJECTED_FOR_DELIVERY`。
- H3 Ref2VA 单文件不等于完整 H3 安装；节点、文本编码器、视频/音频 VAE、LoRA 和兼容性均未核验。
