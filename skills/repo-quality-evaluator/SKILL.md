---
name: "repo-quality-evaluator"
description: "评估 E:\\claudeCoding\\repos 和 E:\\claudeCoding\\dist 中的仓库运行结果，并草拟 quality.toml。当用户要求对产物进行评分、审查 prompt/patch/trajectory 证据，或生成 quality.toml 时调用。"
---

# 仓库质量评估器

使用此技能评估 `E:\claudeCoding` 工作区中的单个仓库运行结果，并根据执行证据草拟 `quality.toml` 文件。

## 何时调用

当用户要求执行以下操作时调用此技能：

- 对 `repo-1`、`repo-2` 或 `E:\claudeCoding\repos` 下的其他仓库进行评分或审查
- 分析 `E:\claudeCoding\dist\<仓库名>` 或 `E:\claudeCoding\dist\<仓库名>\<变体>` 下的产物
- 生成或更新 `quality.toml`
- 将 prompt、patch、trajectory、proxy events 和 session 证据与源仓库进行对比

不要将此技能用于 `E:\claudeCoding\repos` + `E:\claudeCoding\dist` 工作流之外的通用代码审查。

## 工作区约定

默认布局如下：

```text
E:\claudeCoding\
  repos\
    repo-1\
    repo-2\
  dist\
    repo-1\
      prompt.txt
      qwen\
        patch.diff
        patch.branch.diff
        trajectory.jsonl
        proxy_events.jsonl
        session.json
        commit.txt
        quality.toml
      opus\
        patch.diff
        patch.branch.diff
        trajectory.jsonl
        proxy_events.jsonl
        session.json
        commit.txt
        quality.toml
    repo-2\
      ...
```

仓库名是 `repos` 和 `dist` 下共用的文件夹名称。

`E:\claudeCoding\dist\<仓库名>\prompt.txt` 是标准的 prompt 文件。为向后兼容，仅当 `prompt.txt` 不存在时，`prompt.md` 可作为可接受的回退方案。

## 运行解析规则

除非用户明确要求汇总摘要，否则评估应视为**变体级别**而非仓库根级别。

首选目标形式：

- 仓库 + 变体，例如 `repo-1 qwen`
- 一个 dist 运行目录，例如 `E:\claudeCoding\dist\repo-1\qwen`
- 仅仓库名，但仅在 `E:\claudeCoding\dist\<仓库名>` 下恰好存在一个可运行的变体目录时

如果用户只提供 `repo-1`，且 `qwen` 和 `opus` 都存在，不要将它们静默合并为一次评估。尽可能从上下文推断预期的变体；否则清楚地报告歧义。

## 所需输入

对于目标运行 `<仓库名>/<变体>`，读取：

- 源仓库：`E:\claudeCoding\repos\<仓库名>`
- prompt：`E:\claudeCoding\dist\<仓库名>\prompt.txt`
- patch：`E:\claudeCoding\dist\<仓库名>\<变体>\patch.diff`
- trajectory：`E:\claudeCoding\dist\<仓库名>\<变体>\trajectory.jsonl`
- proxy events：`E:\claudeCoding\dist\<仓库名>\<变体>\proxy_events.jsonl`
- session 摘要：`E:\claudeCoding\dist\<仓库名>\<变体>\session.json`

存在时的可选辅助输入：

- 分支 patch：`E:\claudeCoding\dist\<仓库名>\<变体>\patch.branch.diff`
- commit 元数据：`E:\claudeCoding\dist\<仓库名>\<变体>\commit.txt`

如果 `prompt.txt` 缺失但 `prompt.md` 存在于 `E:\claudeCoding\dist\<仓库名>\prompt.md`，则使用 `prompt.md` 作为回退 prompt 来源。

如果任何其他必需文件缺失，停止并清楚地报告缺失的路径。

## 证据优先级

按以下优先级使用文件：

1. `prompt.txt` 或回退的 `prompt.md` 定义任务目标。
2. `patch.diff` 定义运行预期提交的暂存或已提交变更集。
3. `trajectory.jsonl` 是主要的对话追踪。
4. `proxy_events.jsonl` 是实际模型调用证据的最强来源。
5. `session.json` 仅作为辅助 hook 证据。
6. `patch.branch.diff` 和 `commit.txt` 是辅助上下文，不是主要证据。

如果模型身份在文件间存在冲突：

- 优先采用 `proxy_events.jsonl`
- 然后采用 `trajectory.jsonl`
- 将 `session.json` 和 `commit.txt` 视为较低可信度的元数据

## 基于文档的评分规则

以「数据需求文档 Level 1」为事实来源，严格遵循以下章节的约束：

- 4.2.3 rubrics 人工评分
- 4.2.3.1 文件格式
- 4.2.3.2 quality 文件内容
- 4.2.4 passrate
- 4.2.4 任务类型、应用领域、编程语言
- 4.2.5 命中 Qwen BadPattern
- 5.3 Explicit（显式）vs Implicit（隐式）定义

仅使用可追溯到上述章节或其示例的、有文档依据的规则。不要引入自行编造的评分理论。

### 命名关联链

根据文档要求，`criterion.name` 要和 prompt/query 相关 → `criterion.description` 要和 `criterion.name` 相关 → `criterion.rationale` 要和 `criterion.description` 相关。四个层级必须形成可追溯的语义链条。

### description 格式规范

每个 `criterion.description` 必须遵循以下格式：

1. **首句**为 rubric 问题（必填），描述该 criterion 评判什么
2. 紧跟 **`1:锚点;2:锚点;3:锚点;4:锚点;5:锚点`**，五级评分差距明显，读者无需额外假设即可分辨 1 分 vs 3 分 vs 4 分的区别
3. 可使用 `[Explicit]` 或 `[Implicit]` 标签前缀区分 prompt 中显式/隐式要求的维度

### rationale 规范

- 必须**紧扣所选的 score**，与 description 中对应锚点高度相关
- 必须**具体到文件或类名、方法名**，指出哪里没有实现好或哪里实现到位
- **禁止**将原始错误信息、堆栈跟踪直接粘贴到 rationale 中
- rationale 是对当前运行的独立评估，不要出现 `qwen` 或 `opus` 模型名

### badpattern 字段

qwen 变体的 quality.toml 必须分析是否命中 Qwen BadPattern：

- 字段名：`badpattern`（顶层字段，字符串类型）
- 如命中，填写对应的 bad pattern 名称（如 `task_abandonment`）
- 如未命中，可省略该字段
- opus 变体不需要此字段

硬性要求：

- 输出文件为 `quality.toml`
- rubric 数量保持在 **5 到 15** 之间
- 同一任务的 qwen 和 claude 使用**一套共享的 rubric**：`[[criterion]]` 数量相同、`description` 逐字相同、`type`/`points`/`weight` 完全一致
- 每个 `criterion.type` 保持 `"likert"`
- 每个 `criterion.points` 保持 `5`
- 每个 `criterion.weight` 保持 `1.0`
- passrate 计算方式为：加权得分之和除以加权满分之和
- passrate 交付目标为 `qwen < 0.7`，`opus > qwen`，且 `(opus - qwen) / qwen > 20%`
- 在设置 score 时，必须确保最终 qwen passrate < 0.7，opus passrate > qwen passrate，且相对 gap > 20%
- `task_type` / `application_domain` / `programming_language` 是单选元数据字段

## Rubric 编写规则

根据 prompt 中的实际任务压力和 patch 中观察到的工程表面来编写 rubric，而不是套用可复用的通用模板。

这意味着你必须：

- 仔细阅读 prompt，识别任务真正测试的是什么
- 确保 `criterion.name` 和 prompt 任务相关，`criterion.description` 和 `criterion.name` 相关，`criterion.rationale` 和 `criterion.description` 相关——形成不可断裂的命名关联链
- 将这些任务压力转化为 criterion name 和 criterion description
- 让 rubric 语言反映该仓库任务的具体链路、边界、回归风险或交付风险
- 保持 rubric 足够具体，使其明确属于此任务而非通用评分卡
- 仅在同一任务的 qwen vs claude 配对中复用完全相同的 rubric 集

根据文档示例，`criterion.description` 必须是一个有锚点的 1–5 级评分标准，遵循固定格式：

- **首句**：以被评判的具体问题开头（必填的 rubric 问题），可带 `[Explicit]` 或 `[Implicit]` 标签前缀
- **正文**：紧跟 `1:锚点描述;2:锚点描述;3:锚点描述;4:锚点描述;5:锚点描述;`，五个级别评分差距明显
- 分数越高，锚点越完整、正确、稳健；读者无需额外假设即可分辨 1 分 vs 3 分 vs 4 分的区别
- 分数随后在 `criterion.rationale` 中用代码和执行证据进行论证

`[Explicit]` 和 `[Implicit]` 标签用于区分 prompt 中显式/隐式要求的维度。在它们有助于清晰描述 criterion 时使用。

此工作流的内部 rubric 质量检查：

- 每个 criterion 聚焦于一个主要判断；不要将多个可分的问题捆绑到一个分数中
- 使底层判断尽可能接近一个明确的"是或否"的工程问题，然后在 1–5 级上按完整性和稳健性进行评分
- 使 criterion 标签准确对应正在评判的描述和证据
- 避免近重复的 criterion，即用不同名称对同一事物评两次分
- 如果一个 criterion 可以拆分为更清晰的独立检查而不丢失任务含义，则拆分它
- 当一个 criterion 可能混淆两个在质量审查中可能冲突的判断时，优先将其拆分为多个 `[[criterion]]` 项，使每个分数只回答一个狭窄的问题
- 如果反复的质量审查反馈不断指向同一 criterion 上的分数/理由冲突，应通过拆分 criterion 来重建该区域，而不是在原地反复修补措辞
- 使每个分数锚点足够可分，让读者能够分辨为什么某个运行是 1 分 vs 3 分 vs 4 分，而不需要借助未陈述的假设
- 确保每个 rationale 匹配所选的分数锚点，而不仅仅是匹配 criterion 的通用主题
- 当 rationale 说各层矛盾、互相不一致、或可能直接导致错误计费/错误授权/错误数据丢失时，将其校准到最低锚点，除非描述明确另有规定
- 当 rationale 说链路内部一致但语义错误时，将其校准到矛盾级别以上的锚点，并直接解释该区别
- 留意措辞漂移，即某个 criterion 的 rationale 无意中描述的更多是另一个 criterion 的问题而非其自身的

这些检查是工作流保障措施，并非声称的文档措辞。

## repo-7 和 repo-4 的经验教训

当配对评估反复无法通过质量审查时，将这些作为来之不易的工作流启发规则。

### repo-7 经验

- 当任务围绕标识符统一时，不要保留一个宽泛的 criterion 同时评判键选择、筛选/查询一致性、表单写入一致性、旧数据兼容性和验证深度
- 如果一次运行引入了新键，而另一次运行坚持使用现有键，在评分前至少拆分以下问题：
  - 筛选和查询是否停止依赖显示名称
  - 表单写入路径和查询路径是否真正收敛到同一个键
  - 所选方案是否在不回填的情况下保留了旧数据
  - 验证是否真正覆盖了变更链路
- 对于配对的同一 criterion，保持描述字面相同，并保持 rationale 处于同一观察层面；不要让一方谈论键选择理论，而另一方谈论 UX 打磨或验证
- 当配对的双方在不同的具体键上不同时，仅在该 criterion 明确关于键选择时才提及字面的键名；否则描述被评判的属性，如"新查询键"、"现有关系键"、"筛选/查询路径"或"表单写入路径"
- 如果一方分数较低是因为两个层仍使用不同的键，直接说明并将其映射到低锚点；如果另一方分数较高是因为主链路使用了一致的键，直接说明并将其映射到较高锚点
- 不要让一个 criterion 的 rationale 借用本当属于另一个 criterion 的证据，尤其是兼容性证据泄漏到统一评分中，或验证证据泄漏到正确性评分中

### repo-4 经验

- 当反复的审查意见持续集中在相同的少数 criterion 上时，重建 rubric 而不是在原地反复修补措辞
- 成功的修复模式是将冲突的标识符任务拆分为更窄的 criterion，例如：
  - 重复名称预防
  - 筛选/查询的稳定键策略
  - 筛选/查询契约一致性
  - 事件表单写入路径统一
  - 无回填的旧数据兼容
  - 对话框输入验证与反馈
  - 对话框去重合并与列表刷新
  - 验证尝试深度
  - 交付说明与交接质量
- 将"他们是否为筛选/查询选择了稳定键"与"表单写入是否也使用了相同的键"分开；这些不是同一个判断
- 将"旧数据可以在没有新字段的情况下继续工作"与"运行添加了新查询键"分开；否则即使两个 rationale 各自在局部上合理，配对的双方听起来也像是在断言矛盾的事实
- 将"对话框有输入/错误处理"与"对话框结果稳定地合并到列表中并在下游可见"分开；否则前端交互评分会漂移到列表刷新评分
- 将"存在验证尝试"与"最终交付清晰说明了契约、风险与交接"分开；这些不应合并为一个弱的验证 criterion
- 当一个 criterion 在配对中仍必须有数值差异时，用相同的锚点导向句式书写两个 rationale：
  - 什么证据使其高于较低的锚点
  - 什么缺失的证据阻止了其达到下一个更高的锚点
- 避免 rationale 措辞可能被解读为断言相反的具体事实，除非 patch 证据确实相反且该 criterion 正是关于该事实的
- 在评分编辑后，立即根据实际的十个或更少分数重新计算 passrate；不要信任过时的顶层 passrate 文本

### 最终确定配对前的反冲突检查清单

- qwen 和 claude 的 criterion 顺序相同
- qwen 和 claude 的 criterion 名称相同
- qwen 和 claude 的 criterion 描述相同
- 每个 rationale 在双方谈论相同的工程表面
- 没有 rationale 引入属于另一个 criterion 的证据
- 没有 criterion 将键选择、写入路径统一、旧数据兼容性、交互打磨和验证全部捆绑在一起
- passrate 文本与文件中字面的分数总和匹配
- 最终配对仍满足 `qwen < 0.7`、`claude > qwen` 且相对差距 `> 20%`

## 配对评分规则

当同一任务同时存在 qwen 和 claude 运行时，执行配对评估而非孤立的评分漂移。

这意味着你必须：

1. 首先构建一套共享的 rubric
2. 以完全相同的 rubric 含义对两个运行评分
3. 使用文档公式计算两个 passrate
4. 比较配对中同一 criterion 的 rationale 到分数的映射，而不仅仅是最终的数字排序
5. 如果一次运行因各层冲突而评低分，另一次运行因各层一致但错误而评高分，在双方 rationale 中明确说明该区别，并确保锚点支持它
6. 不要将配对中不同的 rationale 内容或不同的锚点本身视为缺陷；当观察到的行为不同时，配对运行可以合理地落在不同的锚点上，只要应用的是相同的 rubric 和相同的评分逻辑
7. 检查最终配对是否满足交付目标
8. 如果不满足，仅在证据范围内重新审视 rubric 的锐度和分数校准

### 双模型对齐强制检查

在写入两个 quality.toml 之前，必须逐项确认：

- qwen 和 claude 的 `[[criterion]]` **数量相同**
- 每个 criterion 的 `name` 在两份文件中**完全一致**
- 每个 criterion 的 `description` 在两份文件中**逐字相同**
- 每个 criterion 的 `type`、`points`、`weight` 在两份文件中**完全一致**
- 仅 `score` 和 `rationale` 可以（且通常应该）不同
- qwen 变体必须包含 `badpattern` 字段（如果适用），opus 变体不需要



## 评估工作流

### 1. 解析目标运行

接受以下任一形式：

- 仓库名加变体，如 `repo-1 qwen`
- 解析为 `E:\claudeCoding\dist\<仓库名>\<变体>` 的 dist 运行文件夹名
- 仅仓库名如 `repo-1`，仅在恰好存在一个可运行的变体目录时

然后映射到：

- `E:\claudeCoding\repos\<仓库名>`
- `E:\claudeCoding\dist\<仓库名>`
- `E:\claudeCoding\dist\<仓库名>\<变体>`

### 2. 验证输入

确认源仓库和所有必需的运行产物文件均存在。

自动优先使用 `prompt.txt`。仅将 `prompt.md` 作为回退方案。

### 3. 阅读任务和执行证据

至少提取：

- 来自 `prompt.txt` 或回退 `prompt.md` 的用户任务
- 实际使用的模型
- session id（如存在）
- 主要的 assistant 响应轨迹
- 工具使用和验证证据（如存在）
- 来自 `patch.diff` 的修改文件列表
- 来自 `commit.txt` 的任何 commit 元数据（如存在）

### 4. 阅读源代码上下文

从 `patch.diff` 中识别变更文件，并检查 `E:\claudeCoding\repos\<仓库名>` 下对应的文件。

阅读足够的附近代码以判断：

- patch 是否解决了任务
- 变更是否符合仓库的约定
- 解决方案是否引入了回归或可疑的缺陷
- 验证或测试是否与变更代码匹配

在业务代码评分中忽略 `.claude` 和其他本地 assistant 配置文件夹。它们不参与质量判断。

仅当 `patch.branch.diff` 有助于理解更大的分支上下文时使用它；不要让它覆盖暂存 patch 证据。

### 5. 构建 rubric 集

使用 **5 到 15** 个 criterion。

一个强健的 rubric 集通常涵盖：

- 任务理解
- 核心实现正确性
- 当任务要求时的隐藏边界或降级数据处理
- 当 prompt 或 patch 暗示验证工作时的验证深度
- 当最终答案质量重要时的交付完整性

不要强制套用固定模板。criterion 应随任务本身而变化。

### 6. 根据证据保守评分

不要编造事实。如果证据薄弱或缺失，保守评分并说明原因。

使用实现和观察到的执行中的具体证据。不要奖励没有代码或验证支撑的说法。

### 7. 填写文档元数据

生成 `quality.toml` 时填充以下顶级字段：

- `version`
- `repo`
- `variant`
- `model`
- `session_id`
- `task_type`
- `application_domain`
- `programming_language`
- `passrate`
- `summary`

如果存在 bad pattern 证据，使用工作区已建立的命名风格添加一个专用的 bad-pattern 字段，并在各运行中保持一致。

优先按以下顺序获取元数据来源：

1. `commit.txt` 中现有的明确运行元数据
2. prompt 措辞和仓库上下文
3. 代码库语言和应用形态

不要凭空虚断。如果元数据无法从证据中获得支撑，如实说明而不是编造一个精确的标签。

### 8. 生成 quality.toml

写入或更新：

`E:\claudeCoding\dist\<仓库名>\<变体>\quality.toml`

作为标准工作流的一部分，直接读取 `E:\claudeCoding\dist\<仓库名>\prompt.txt`；当该文件存在时，不需要用户重新提供 prompt。

除非用户明确要求更多文件，否则仅为目标变体运行生成 `quality.toml`。

## quality.toml 格式

使用以下结构（注意 qwen 变体需包含 `badpattern` 字段）：

```toml
version = 1
repo = "repo-1"
variant = "qwen"
model = "qwen3.7-max"
session_id = "example-session-id"
task_type = "缺陷修复"
application_domain = "企业协作后端"
programming_language = "Java"
passrate = 0.64
badpattern = "task_abandonment"
summary = "一段简洁的、基于证据的摘要段落。"

[[criterion]]
name = "semantic_understanding_and_root_cause"
description = "[Explicit] 是否准确理解任务并定位关键根因。1: 基本未理解问题；2: 只看到表面现象；3: 抓到部分主链路但解释不完整；4: 能用代码证据解释主要问题机制；5: 能完整串联关键链路、触发条件和边界。"
type = "likert"
points = 5
weight = 1.0
score = 3
rationale = "用实现和观察到的验证中的直接证据解释分数。必须具体到文件或类名、方法名。"

[[criterion]]
name = "implementation_correctness"
description = "[Explicit] 是否正确实现任务要求。1: 基本未修复；2: 只改到表层症状；3: 主路径部分可用但仍有重要缺口；4: 主路径修复较完整且主要风险可控；5: 端到端正确并兼顾关键边界与回归风险。"
type = "likert"
points = 5
weight = 1.0
score = 4
rationale = "说明已确认的优势和任何未解决的正确性风险。必须具体到文件或类名、方法名。"
```

## quality.toml 规则

基于文档的规则：

- 除非用户明确要求，否则将 criterion 数量保持在 5 到 15 之间
- 将 `score` 值保持在 **1–5** likert 量表上
- 每个 criterion 保持 `weight = 1.0`
- 每个 criterion 保持 `points = 5`
- 使用文档公式计算 `passrate`：`(∑weight × score) / (∑weight × points)`
- 为同一任务的配对 qwen 和 claude 运行保持一套共享的 rubric：
  - `[[criterion]]` 数量相同
  - 每个 `description` 逐字相同
  - `type`、`points`、`weight` 完全一致
- 确保 `criterion.name` → `criterion.description` → `criterion.rationale` 形成可追溯的语义关联链
- 确保 `criterion.description` 首句为 rubric 问题，紧跟 `1:锚点;2:锚点;3:锚点;4:锚点;5:锚点`
- 确保 `criterion.rationale` 引用真实证据，具体到文件、类名或方法名，禁止粘贴原始错误信息
- qwen 变体必须分析并填写 `badpattern` 字段（如适用），opus 变体不需要
- 填写 `task_type`、`application_domain` 和 `programming_language`

工作区和交付规则：

- 在此 `dist/<仓库>/<变体>` 工作流中评估变体级运行时包含 `variant`
- 不要在 rationale 文本中提及原始产物文件名，如 `patch.diff`、`trajectory.jsonl`、`session.json` 或 `proxy_events.jsonl`
- 不要在 rationale 文本中放置 `file:///...` 链接或原始绝对路径
- 不要在 rationale 文本中提及 qwen 或 opus 名称；将 rationale 写为对当前运行的独立评估
- 不要使用基于轮次的措辞，如 `本轮`、`这轮` 或 `轮次`
- 避免交接式的开头；直接书写关于代码、行为、风险或结果的内容

## 输出标准

最终的 `quality.toml` 应该是：

- 简洁的
- 基于证据的
- 符合文档可见字段规则的
- 足够严格，薄弱的证据会降低分数
- 经过校准，使配对结果在证据合理允许时满足交付约束

## 执行说明

- 在判断质量之前，优先阅读 `patch.diff` 和变更的源文件。
- 使用 trajectory 来理解模型尝试了什么，而不是作为 patch 正确的证明。
- 当用户已经对 rationale 措辞要求了内部风格时，在后续输出中保持该风格一致。