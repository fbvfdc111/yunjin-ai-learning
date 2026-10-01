# 标签与证据政策

1. `collection_scope` 记录用户确认的采集范围；它回答“为什么收集”，不直接等于监督标签。
2. `evidence_text` 原样记录截图可见标题、编号或说明；`classification_evidence_source` 记录最终类别使用的证据组合。
3. `pattern_labels_supported_by_name` 和 `craft_labels_supported_by_name` 只允许从文字证据中抽取；无法确认写 `unknown`。
4. 年代、机构、文物名和工艺不得由外观猜测。
5. `level1_label=nanjing_yunjin` 可以由用户确认的采集背景与截图中的云锦工艺语义共同支持；只靠项目相关性或只靠视觉外观均不够。
6. `level1_label=other_brocade` 需要标题或来源明确指出其他地域/类别织锦，且该直接证据不会被项目采集背景覆盖。
7. `level1_confidence` 表示证据强度；`label_evidence_available` 与 `usable_for_training` 分开管理。
8. 截图含类别文字、来源未授权、同源关系未解决或只有研究卡时，`usable_for_training=false`。
9. metadata 的更改应保留审核人、日期和证据来源；正式版建议增加 `annotator`、`reviewer`、`review_date`、`source_url`、`rights_status` 字段。
