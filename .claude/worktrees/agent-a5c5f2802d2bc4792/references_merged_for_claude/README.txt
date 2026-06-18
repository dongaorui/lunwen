# ReplenishVerifier Extra Reference TXT Pack

这个包不是论文全文，而是为 ReplenishVerifier 论文写作和 Claude Code 实验实现准备的“参考文献笔记 + 对比矩阵 + 提示词”。

## 内容
- `paper_notes/`: 每篇论文一份 txt，包含：为什么有用、怎么用、风险、给 Claude Code 的指令。
- `matrices/related_work_comparison_extra.txt`: 相关工作对比矩阵。
- `reading_order.txt`: 推荐阅读顺序。
- `claude_prompts/prompt_update_with_extra_references.txt`: 给 Claude Code 的下一步提示词。

## 使用方法
把整个文件夹放到项目中，例如：

```bash
ReplenishVerifier/
  references_extra_txt/
```

然后对 Claude Code 说：
“请阅读 references_extra_txt，并按照 claude_prompts/prompt_update_with_extra_references.txt 修改论文和实验计划。”

## 注意
- 不要把这些笔记当成正式引用格式。
- 正式论文需要在 bib 文件中补全作者、会议、年份、链接。
- 对 2026 年 arXiv 工作（OptArgus/OptiRepair）要注明是近期预印本，避免过度依赖。
