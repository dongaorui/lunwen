# ReplenishVerifier References for Claude Code

这个包已经把前两次生成的参考资料合并整理好，适合直接放进你的 `ReplenishVerifier/` 项目目录下作为只读参考资料。

## 推荐放置位置

```text
ReplenishVerifier/
  references/
    uploaded_full_texts/
    extra_paper_notes/
    matrices/
    claude_prompts/
    repo_tools/
    project_drafts/
```

## 目录说明

- `uploaded_full_texts/`：你已经上传过的论文 PDF 转出的长文本，适合查细节。
- `extra_paper_notes/`：我整理的论文笔记，适合 Claude Code 快速理解 Related Work、baseline 和风险点。
- `matrices/`：相关工作对比矩阵，适合直接用于论文 Related Work 和 rebuttal 准备。
- `claude_prompts/`：给 Claude Code 的下一步提示词。
- `repo_tools/`：把源码仓库提取成 txt 的脚本。
- `project_drafts/`：你当前 ReplenishVerifier 论文草稿、图版 PDF 的文本和方向笔记。

## Claude Code 使用建议

优先让 Claude Code 读：

```text
references/extra_paper_notes/
references/matrices/
references/claude_prompts/
```

只有需要核对原文细节时，再读：

```text
references/uploaded_full_texts/
```

不要让 Claude Code 直接把外部论文的代码或文字复制到你的项目里。它们只能作为方法设计、baseline 设计、Related Work 和实验定位参考。

## 去重说明

两包中有重叠文献，例如 SIRL、OR-R1、StepORLM、LLMOPT、OptMATH。这里没有删除重复信息，而是做了分层：

- `uploaded_full_texts/` 保存较长的原文转换文本；
- `extra_paper_notes/` 保存短笔记和定位总结。

Claude Code 应优先参考 `extra_paper_notes/`，避免重复引用同一篇论文。

## 下一步建议

1. 让 Claude Code 阅读 `claude_prompts/prompt_update_with_extra_references.txt`。
2. 让它更新 Related Work 对比矩阵。
3. 然后继续实现强 baseline：SIRL-like LP-Stats、OptArgus-like Audit、OptiRepair-like Repair。
4. 最后再跑真实 LLM candidate 实验。
