# V20 Exhibition 修改摘要

本版本从 V19 Rebuild 复制而来，没有覆盖稳定版。

## 目标变化

用户明确指出当前版本仍像教学页面，而不是展示作品。V20 的核心目标改为：

- 默认进入展示模式，而不是教学模式。
- 3D 画面优先，文字、曲线、运行状态退到折叠辅助层。
- 视觉气质从浅色教学卡片改为深色展陈舞台。
- 保留教学模式，但不再让教学模式成为默认入口。

## 页面层变化

- `数字织机` 默认打开 `Exhibition Mode / 展示模式`。
- `Teaching Mode / 教学模式` 仍保留原六阶段 SVG 教学流程。
- `Live Simulation Mode / 实时仿真模式` 仍保留更多过程数据。
- 展示模式中主画面使用更高 iframe，高度从常规 720 提升为 860。
- 数据、曲线、运行状态、边界说明改为折叠面板，减少首屏干扰。
- 展示模式自动刷新从 1 秒放慢到 2.8 秒，降低 iframe 重新加载造成的跳脱感。

## 3D 层变化

- `render_process_twin_3d()` 新增 `exhibition` 参数。
- 展示模式使用深色背景、暖色聚光、冷色轮廓光和更低更近的默认镜头。
- 展示模式隐藏 3D 空间中的层级文字标签。
- 展示模式下布面去掉可见教学文字，只保留红金锦缎视觉效果。
- 展示模式动作幅度提高，拽花、开口、穿纬、打纬和卷取更明显。
- 保留 `Simulation-driven / Simulated Data` 和非一比一机械复原边界。

## 测试

相关测试：

```text
34 passed
```

全量测试：

```text
132 passed, 4 failed
```

剩余 4 个失败为原有保护文件哈希/治理门禁问题，涉及：

- `src/yunjin_ai/vision.py`
- `tests/test_phase4_dots.py`
- Round3 baseline audit
- governance/runtime health gate

这些不是 V20 展示模式改造新增的失败。
