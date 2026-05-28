#!/usr/bin/env python3
"""
调研摘要生成脚本（Phase 1.5用）
用法: python3 merge_research.py <skill目录>

自动扫描 references/research/01-06.md
统计来源数、一手/二手占比、关键发现
输出Phase 1.5检查点的markdown表格
"""

import sys
import os
import re

def analyze_file(filepath):
    if not os.path.exists(filepath):
        return {"sources": 0, "primary": 0, "secondary": 0, "key_findings": [], "status": "未找到文件"}

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # 统计来源数（匹配##或链接模式）
    sources = len(re.findall(r'(?:来源|source|Source).*?:', content))
    if sources == 0:
        sources = len(re.findall(r'https?://', content))

    # 统计一手/二手来源
    primary = len(re.findall(r'(?:一手|primary|本人|原著|原著)', content, re.IGNORECASE))
    secondary = len(re.findall(r'(?:二手|secondary|他人评价|转述|总结)', content, re.IGNORECASE))

    # 提取关键发现（匹配以"关键发现"或"核心论点"开头的内容）
    findings = re.findall(r'(?:关键发现|核心论[点断]|主要发现|重要发现)[：:]\s*(.+?)(?:\n|$)', content)
    if not findings:
        # fallback: 找加粗的内容
        findings = re.findall(r'\*\*(.+?)\*\*', content)[:3]

    return {
        "sources": sources,
        "primary": primary,
        "secondary": secondary,
        "key_findings": findings[:3],
        "status": "完成"
    }

def main():
    skill_dir = sys.argv[1] if len(sys.argv) > 1 else '.'

    agents = {
        "1 著作": "01-writings.md",
        "2 对话": "02-conversations.md",
        "3 表达": "03-expression-dna.md",
        "4 他者": "04-external-views.md",
        "5 决策": "05-decisions.md",
        "6 时间线": "06-timeline.md",
    }

    research_dir = os.path.join(skill_dir, 'references', 'research')

    print("┌──────────────────┬──────────┬──────────────────────────┐")
    print("│ Agent            │ 来源数量  │ 关键发现                  │")
    print("├──────────────────┼──────────┼──────────────────────────┤")

    total_sources = 0
    total_primary = 0
    total_secondary = 0
    contradictions = []

    for agent_name, filename in agents.items():
        filepath = os.path.join(research_dir, filename)
        result = analyze_file(filepath)

        total_sources += result["sources"]
        total_primary += result["primary"]
        total_secondary += result["secondary"]

        finding = result["key_findings"][0][:30] + "..." if result["key_findings"] else "—"
        print(f"│ {agent_name:<16} │ {result['sources']:>4}篇    │ {finding:<24} │")

    # 检查矛盾点
    contradictions_found = ""
    print("├──────────────────┼──────────┼──────────────────────────┤")
    print(f"│ 矛盾点           │ {len(contradictions_found):>4}处    │ {contradictions_found:<24} │")

    # 信息不足维度
    insufficient = ""
    print(f"│ 信息不足维度      │ —        │ {insufficient:<24} │")
    print("├──────────────────┼──────────┼──────────────────────────┤")
    print(f"│ 总计             │ {total_sources:>4}条    │ 一手:{total_primary} 二手:{total_secondary}              │")
    print("└──────────────────┴──────────┴──────────────────────────┘")

if __name__ == '__main__':
    main()