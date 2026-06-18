# references_txt 说明
这个压缩包包含我能在当前会话中访问到的论文 PDF / 草稿文档的文本版。

## 已生成文件
- OR-R1_2026_AAAI.txt  ← 来源：2026-AAAI-OR-R1 Automating Modeling and Solving of Operations Research Optimization Problem via Test-Time Reinforcement Learning.pdf，页数/类型：9，大小：63501 bytes
- StepORLM_2026_ICLR.txt  ← 来源：2026-ICLR-StepORLM A Self-Evolving Framework With Generative Process Supervision For Operations Research Language Models.pdf，页数/类型：27，大小：86567 bytes
- SIRL_2505_11792v3.txt  ← 来源：2505.11792v3.pdf，页数/类型：37，大小：118754 bytes
- LLMOPT_9457_Learning_to_Define.txt  ← 来源：9457_LLMOPT_Learning_to_Define.pdf，页数/类型：27，大小：127674 bytes
- OptMATH_9731_Scalable_Bidirectional.txt  ← 来源：9731_OptMATH_A_Scalable_Bidire.pdf，页数/类型：34，大小：168597 bytes
- ReplenishVerifier_zh_figures_pdf.txt  ← 来源：ReplenishVerifier_中文版_方法图版.pdf，页数/类型：8，大小：14125 bytes
- ReplenishVerifier_method_figures_pdf.txt  ← 来源：ReplenishVerifier_结构验证增强方法图版.pdf，页数/类型：19，大小：44426 bytes
- ReplenishVerifier_draft_zh.txt  ← 来源：replenishverifier_draft_zh.md，页数/类型：md，大小：37313 bytes
- 论文.txt  ← 来源：论文.docx，页数/类型：docx，大小：9372 bytes
- ReplenishVerifier_中文版_方法图版.txt  ← 来源：ReplenishVerifier_中文版_方法图版.docx，页数/类型：docx，大小：12835 bytes
- ReplenishVerifier_结构验证增强库存补货优化建模论文初稿.txt  ← 来源：ReplenishVerifier_结构验证增强库存补货优化建模论文初稿.docx，页数/类型：docx，大小：23759 bytes

## 关于源码
我现在只能读取你上传到当前会话的文件。你本地 Claude Code 项目里的源码或 references/repos 目录，我这里无法直接读取，除非你上传 zip 或把代码文件发到对话中。
如果你已经在本地有 references/repos/OR-R1 等源码，可以把 extract_repo_texts.py 复制到项目里运行：
```bash
python references_txt/extract_repo_texts.py references/repos references/repo_texts
```
它会把常见代码/配置/README 合并成每个 repo 一个 txt，方便 Claude Code 阅读。
