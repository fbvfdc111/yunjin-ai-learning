# 文化知识库数据字典

## `knowledge_base.json`

- `id`：稳定知识条目 ID。
- `category` / `title`：主题与展示标题。
- `claims`：一条知识可含多条事实；每条事实分别保存 `text`、`source_ids` 和 `evidence_scope`。
- `evidence_scope`：仅允许 `direct_yunjin`、`official_object_name`、`general_cultural_background`、`governance_methodology`。
- `keywords`：本地检索关键词，不是监督学习标签。
- `evidence_level`：A/B/C 证据类型等级。
- `visual_retrieval`：`direct`、`object_name_only` 或 `disabled`。一般文化背景必须为 `disabled`。

## `official_object_knowledge_map.json`

覆盖47件南京云锦官方对象。关系只在官方名称逐字出现核验词时建立，固定为
`official_name_mentions` + `official_object_name`。未关联对象必须写明原因。该表不读取
`craft_name` 或 `pattern_name` 候选字段来扩充关系，也不表示图像鉴定、模型分类或训练标签。

## `sources.json` / `sources.csv`

两者表达同一来源表，JSON 供程序读取，CSV 供人工审阅。外部来源记录访问日期；本地来源使用项目相对路径。

## 内容边界

知识条目不保存上传图像的视觉观察或模型推测。运行时结果只存在于当前 Streamlit 会话状态，不写回知识库。
`general_cultural_background` 只能作为明确标注的一般传统文化背景回答，不能由视觉结果自动召回，
也不能据此确定具体南京云锦对象的寓意。Candidate Knowledge Labels 只用于组织和探索，不用于监督训练。
