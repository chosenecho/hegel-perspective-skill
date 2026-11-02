# 本地研究语料

主索引`manifest.json`逐响应记录URL（含重定向）、字节数、SHA-256、原始文件、提取文本及HTML锚点。TXT是便于查找的派生文本；原始HTML/PDF/TXT保留在raw中。动态链接、广告和导航不等于作者正文。`read_status`默认“已归档、未逐项审计”，实际选读范围见研究报告和证据台账。

辅助档案：

- `letters-agent/source-index.json`：书信、教育、机构/版本档案；失败/空白搜索页已保留并排除有效来源计数。
- `critics-agent/source-index.json`：批评原始文本、研究论文、相应PDF和许可；同书章节、两种格式不重复计为独立著作。
- `articles/writings/`：原典组的补充下载，存在与主采集相同的响应，统计须去重。
- `research/voice-samples.json`位于本目录的同级research下，保存实际风格样本，不代表全集统计。

## 权利与用途

黑格尔德文原著本身已进入公共域，但特定电子转录的使用条件、现代翻译、校勘、注释、编排与学术文章的权利各异。Project Gutenberg文件保留其电子书头尾及使用说明；不能把仓库MIT许可覆盖到第三方材料。

现代论文中有CC BY、CC BY-NC及Harvard IOAL等不同许可，SEP也有其版权条款；具体见critics-agent的source-notes.md。不因可免费访问就断言允许再分发。此处为用户授权的**本地研究存档**，仓库`.gitignore`默认排除原文大档；除非另行核清许可，不把这些档案自动推到公共仓库。不下载绕过付费墙的现代专著。

Skill核心、原创研究摘要、来源地图与脚本不依赖任何本机绝对路径。复制整个本地skill目录可离线使用这些存档；只从Git取得入口与索引时，可能缺少被忽略的语料，必须如实报告，而不是假装读到。恢复下载需网络及requests/beautifulsoup4，离线检索脚本只用标准库。

公开发行保留`letters-agent`与`critics-agent`的来源索引/许可说明，排除原文载荷和机器本地安装回执。发行包可运行`python scripts/quality_check.py --structure-only`核结构；该模式将原文指纹与哈希明确标为未验证/跳过。本地完整语料仍用默认模式审计。

## 检索与重取

```text
python scripts/corpus.py find "Aufheben" --id logic1-de
python scripts/corpus.py audit
python scripts/collect_sources.py --proxy http://127.0.0.1:10808 --depth 2
```

最后一条中的代理地址只是本次机器上的示例，换机器应传自己的代理或不用代理。不可把当前本地代理端口当Skill运行前提。重新抓取只证明取到响应，不自动升级为“已阅读”。
