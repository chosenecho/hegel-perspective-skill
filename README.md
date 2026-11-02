# 黑格尔视角 · 原典驱动的思维顾问

版本 **2.0.0**，重建于2026-11-02—03。依据 `huashu-nuwa` 的六维研究与独立验证流程，从原典重新提炼；旧版已在本地备份。这是用于分析和文本阅读的角色化重构，不是历史人物本人的现代发言。

## 调用

在支持本地Skill的环境中调用：

```text
$hegel-perspective
用黑格尔的视角，分析这个规则为什么正在破坏它自己的目标。
```

也支持明确的“黑格尔模式”“Hegel perspective”、黑格尔原典细读。普通技术任务、一般权衡和普通人生建议不会仅因出现“矛盾”而自动触发。可以随时要求白话、短答或退出角色。

## 内容

- **7个核心模型**：内在检验与规定否定、中介与具体普遍、承认、客观自由、现实性与条件、教养与劳动、目的中介及后果。每个模型均有来源、应用和失效边界。
- **10条决策启发式**，明确属于现代转译；既能解释原文，也能形成有条件的行动判断。
- **六维研究**：著作、书信/演说、表达、外部批评、行动判断、文本与生平时间线。
- **版本分层**：区分作者正文、作者附注、书信/遗稿、学生记录、编辑补充和后世解释；保留种族、殖民、性别、国家与个体自由等实质张力。
- **可回查证据**：40条精选原典证据台账、20段德文表达采样及本地原始档案；下载不冒充通读，哈希一致不冒充哲学正确。
- **真实试用记录**：两位独立测试者的14题实际回答、另3次精炼试答、2题回归、双评审和修正记录。部分题与操作示例相近，不能称为完全未见题盲测或跨模型统计验证。

## 文件入口

| 文件 | 用途 |
|---|---|
| [SKILL.md](hegel-perspective/SKILL.md) | 激活后执行的主规则 |
| [出处地图](hegel-perspective/references/source-map.md) | 著作、版本、原典位置及解释文献 |
| [概念与误读](hegel-perspective/references/concepts.md) | 术语、形而上学与常见误解 |
| [版本方法](hegel-perspective/references/textual-method.md) | 正文/增补、引语和电子本风险 |
| [操作案例](hegel-perspective/references/operating-guide.md) | 文本、决策、短答及现代应用 |
| [六维研究与本轮记录](hegel-perspective/references/research/00-run-state.md) | 范围、方法、缺口和成果 |
| [验证](hegel-perspective/references/research/07-validation.md) | 实际测试及限制 |
| [双评审与修正](hegel-perspective/references/research/08-refinement.md) | 建议、采纳与未采纳理由 |
| [档案说明](hegel-perspective/references/sources/README.md) | 来源、权利与完整性边界 |

## 本地工具

GitHub发行包包含主规则、原创研究、来源元数据与脚本。解压后把`hegel-perspective/`放入Skill目录即可使用；原典细读时可按出处地图在线查原文。第三方全文存档单独保留在研究机器上，在`hegel-perspective/`目录运行以下命令检查发行包结构：

```text
python scripts/quality_check.py --structure-only
```

该模式明确跳过原文指纹和档案哈希，不把缺失语料记作已验证。以下检索、完整审计和表达复算命令需要先恢复相应本地语料。

先直接读出处地图与相关文本；Python只是便捷入口。以下命令在 `hegel-perspective/` 目录运行，Python 3.10+，前三个脚本只需标准库：

```text
python scripts/corpus.py find "Aufheben" --id logic1-de
python scripts/corpus.py show phg-de --find "Das Wahre ist das Ganze"
python scripts/corpus.py quote zeno-enc__b1560cf2d1 --find "Positiv-Vernünftige"
python scripts/corpus.py audit
python scripts/quality_check.py
python scripts/analyze_voice.py
```

`find/show`适合定位；逐字引文回到原始文件核对。`quote`读取HTML段落，保留内联标签两侧的标点关系，仍不等于影印本校勘。

联网采集器 `collect_sources.py` 另需 `requests`、`beautifulsoup4`。可选代理须显式传入，没有绑定本机端口；`--from-manifest`按现有清单重取主语料。它不自动恢复辅助研究者的全部档案，也不保证站点永远可用：

```text
python scripts/collect_sources.py --from-manifest --proxy http://127.0.0.1:10808
```

## 安装与档案

可将整个 `hegel-perspective/` 文件夹放入本机Skill目录。默认Codex位置是 `~/.codex/skills/hegel-perspective/`；不要只复制主文件而漏掉参考资料。安装前若目标已存在，先备份。

本轮机器上的原始下载、提取文本与失败响应仅供本地研究，受各来源自己的权利条件约束；仓库 `.gitignore` 默认排除这些大文件，保留来源索引、请求状态和选读范围等元数据。**Git检出或Release解压不等于获得完整离线语料**：迁移离线能力时应复制本地完整Skill目录，并遵守来源许可。仓库代码许可不覆盖第三方译文、论文或网页。

这不是GW全集校勘版，也不宣称读完全部黑格尔或所有近年研究。未取得的资料、传本缺陷、残留解释争论均在版本方法和研究报告中明示。
