---
name: "dist-doc-collector"
description: "汇总 E:\\claudeCoding\\dist\\<project>-N 的 prompt、commit_id、session_id 和 trajectory 到 doc 目录。当用户要执行 doc.bat、整理运行产物或导出项目文档时调用。"
---

# Dist 文档产物汇总器

使用此技能把 `doc.bat` 的工作流转成可直接执行的技能步骤：从 `E:\claudeCoding\dist\<project>-N` 中汇总 prompt、commit_id、session_id 与 trajectory 文件，并输出到 `E:\claudeCoding\doc\<project>\`。

## 何时调用

当用户提出以下需求时调用：

- 运行或替代 `scripts\doc.bat`
- 汇总某个项目全部变体的 prompt、commit、session、trajectory
- 把 `dist` 下多次运行的产物整理到 `doc\<project>`
- 导出某个项目的运行证据，便于审查、归档或后续分析

不要在以下场景调用：

- 只需要评估 `quality.toml`
- 只需要查看单个文件内容而不做汇总
- 与 `E:\claudeCoding\dist` / `E:\claudeCoding\doc` 工作流无关的通用文件整理

## 工作区约定

默认目录结构：

```text
E:\claudeCoding\
  dist\
    <project>-1\
      prompt.txt
      qwen\
        commit.txt
        session.json
        trajectory.jsonl
      opus\
        commit.txt
        session.json
        trajectory.jsonl
    <project>-2\
    ...
  doc\
    <project>\
```

其中：

- 输入项目名为 `<project>`
- 变体目录采用连续编号：`<project>-1`、`<project>-2`、`<project>-3` ...
- 遍历时必须从 `1` 开始，并在遇到第一个不存在的 `<project>-N` 目录时停止，保持与 `doc.bat` 一致

## 必须产出的文件

输出目录：`E:\claudeCoding\doc\<project>\`

必须生成或覆盖以下文件：

- `allPrompt.txt`
- `allQwenCommitId.txt`
- `allOpusCommitId.txt`
- `allQwenSessionId.txt`
- `allOpusSessionId.txt`
- `qwen_trajectory_N.jsonl`
- `opus_trajectory_N.jsonl`

## 汇总规则

### 1. 目录准备

- 若 `E:\claudeCoding\doc` 不存在，则创建
- 若 `E:\claudeCoding\doc\<project>` 不存在，则创建
- 若已存在，则允许覆盖其中同名输出文件

### 2. 收集 prompt

从每个存在的 `E:\claudeCoding\dist\<project>-N\prompt.txt` 读取内容，按编号顺序写入：

- `E:\claudeCoding\doc\<project>\allPrompt.txt`

要求：

- 默认把每个变体的 prompt 作为 `allPrompt.txt` 中的一行
- 变体之间只允许使用一个换行分隔，不要插入空白行
- 若源 `prompt.txt` 自带结尾换行，写入前应去掉尾部多余换行，避免在 `allPrompt.txt` 中形成空白行
- 若某个变体没有 `prompt.txt`，则跳过该文件，但继续处理后续步骤

### 3. 收集 qwen commit_id

对每个存在的：

- `E:\claudeCoding\dist\<project>-N\qwen\commit.txt`

读取其中以 `commit_id=` 开头的行，提取等号右侧内容，按编号顺序逐行写入：

- `E:\claudeCoding\doc\<project>\allQwenCommitId.txt`

注意：

- 输出文件中只写 commit_id 值本身，不要附加 `project-N:` 前缀
- 若文件不存在或没有匹配行，则跳过

### 4. 收集 opus commit_id

对每个存在的：

- `E:\claudeCoding\dist\<project>-N\opus\commit.txt`

按与 qwen 相同的规则提取 `commit_id=` 并写入：

- `E:\claudeCoding\doc\<project>\allOpusCommitId.txt`

### 5. 收集 qwen session_id

对每个存在的：

- `E:\claudeCoding\dist\<project>-N\qwen\session.json`

从原始文本中用正则提取：

```regex
"session_id":"([^"]+)"
```

把捕获值按编号顺序逐行写入：

- `E:\claudeCoding\doc\<project>\allQwenSessionId.txt`

注意：

- 保持与 `doc_extract_session.ps1` 一致，只做简单文本正则提取
- 若没有匹配到 `session_id`，则跳过

### 6. 收集 opus session_id

对每个存在的：

- `E:\claudeCoding\dist\<project>-N\opus\session.json`

按与 qwen 相同的规则提取并写入：

- `E:\claudeCoding\doc\<project>\allOpusSessionId.txt`

### 7. 复制 qwen trajectory

对每个存在的：

- `E:\claudeCoding\dist\<project>-N\qwen\trajectory.jsonl`

复制到：

- `E:\claudeCoding\doc\<project>\qwen_trajectory_N.jsonl`

其中 `N` 必须与变体编号一致。

### 8. 复制 opus trajectory

对每个存在的：

- `E:\claudeCoding\dist\<project>-N\opus\trajectory.jsonl`

复制到：

- `E:\claudeCoding\doc\<project>\opus_trajectory_N.jsonl`

其中 `N` 必须与变体编号一致。

## 执行流程

当用户给出项目名后，按以下顺序执行：

1. 解析项目名 `<project>`
2. 确认根目录为 `E:\claudeCoding`
3. 准备 `doc` 和 `doc\<project>` 目录
4. 从 `N = 1` 开始按连续编号扫描 `dist\<project>-N`
5. 依次生成 5 个汇总文本文件
6. 复制 qwen / opus 的 trajectory 文件
7. 向用户汇报输出目录和实际生成的文件

## 输出汇报要求

完成后，汇报时至少说明：

- 使用的项目名
- 扫描到的最大连续变体范围
- 输出目录路径
- 实际生成或更新了哪些文件
- 哪些变体缺少某些源文件并被跳过
- `allPrompt.txt` 是否按“每条一行、无空白行”输出

## 示例

### 用户请求

```text
把 bjsxz 的文档产物整理出来
```

### 期望行为

- 扫描 `E:\claudeCoding\dist\bjsxz-1`、`bjsxz-2`、`bjsxz-3` ...，直到遇到第一个不存在的目录
- 生成：
  - `E:\claudeCoding\doc\bjsxz\allPrompt.txt`
  - `E:\claudeCoding\doc\bjsxz\allQwenCommitId.txt`
  - `E:\claudeCoding\doc\bjsxz\allOpusCommitId.txt`
  - `E:\claudeCoding\doc\bjsxz\allQwenSessionId.txt`
  - `E:\claudeCoding\doc\bjsxz\allOpusSessionId.txt`
- `allPrompt.txt` 中每条 prompt 占一行，行与行之间没有空白行
- 复制：
  - `qwen_trajectory_1.jsonl`、`qwen_trajectory_2.jsonl` ...
  - `opus_trajectory_1.jsonl`、`opus_trajectory_2.jsonl` ...

## 实施注意事项

- 优先直接使用工作区文件操作完成汇总，而不是要求用户手动运行批处理
- 保持输出文件名、编号规则和停止条件与 `scripts\doc.bat` 一致
- 不要擅自改变文件格式，例如不要把 commit_id 或 session_id 改成带标签的 JSON 或表格
- 生成 `allPrompt.txt` 时，不要在相邻 prompt 之间额外写入空白行
- 如果用户明确要求“完全等同 doc.bat”，则严格遵守连续编号扫描与首个缺口即停止的行为；若用户明确要求去掉空白行，则在保持顺序不变的前提下只保留单个换行分隔
