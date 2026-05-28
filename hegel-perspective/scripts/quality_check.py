#!/usr/bin/env python3
"""
质量自检脚本（Phase 4用）
用法: python3 quality_check.py <SKILL.md路径>

自动检查6项通过标准，输出逐项PASS/FAIL和总结
"""

import sys
import re

def check_quality(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    results = []

    # 1. 心智模型数量 (3-7)
    model_count = len(re.findall(r'###\s+心智模型\d+', content))
    results.append({
        "check": "心智模型数量",
        "standard": "3-7个",
        "result": f"{model_count}个",
        "pass": 3 <= model_count <= 7
    })

    # 2. 每个模型的局限性
    limitation_count = len(re.findall(r'局限性', content))
    has_limits = limitation_count >= model_count if model_count > 0 else False
    results.append({
        "check": "模型局限性",
        "standard": "每个模型有局限说明",
        "result": f"找到{limitation_count}处",
        "pass": has_limits
    })

    # 3. 表达DNA辨识度
    has_dna = bool(re.search(r'表达DNA|句式偏好|词汇特征', content))
    dna_detail = len(re.findall(r'\|.*\|.*\|', content[content.find('表达DNA'):content.find('表达DNA')+500] if '表达DNA' in content else ''))
    results.append({
        "check": "表达DNA辨识度",
        "standard": "读100字能认出是谁",
        "result": f"{'有' if has_dna else '无'}详细表达DNA表格",
        "pass": has_dna and dna_detail >= 3
    })

    # 4. 诚实边界
    boundary_section = content[content.find('诚实边界'):] if '诚实边界' in content else ''
    boundary_count = len(re.findall(r'^\d+\.', boundary_section, re.MULTILINE))
    results.append({
        "check": "诚实边界",
        "standard": "至少3条具体局限",
        "result": f"{boundary_count}条",
        "pass": boundary_count >= 3
    })

    # 5. 内在张力
    tension_count = len(re.findall(r'核心张力|矛盾|张力', content))
    results.append({
        "check": "内在张力",
        "standard": "至少2对矛盾/张力",
        "result": f"找到{tension_count}处相关描述",
        "pass": tension_count >= 2
    })

    # 6. 一手来源占比
    has_sources = bool(re.search(r'调研来源|一手来源|二手来源', content))
    results.append({
        "check": "一手来源占比",
        "standard": "来源section存在",
        "result": f"{'有' if has_sources else '无'}来源section",
        "pass": has_sources
    })

    # 输出
    print("\n┌──────────────────────┬──────────┬──────────┬────────┐")
    print("│ 检查项               │ 标准      │ 结果      │ 状态   │")
    print("├──────────────────────┼──────────┼──────────┼────────┤")
    for r in results:
        status = "✅PASS" if r["pass"] else "❌FAIL"
        print(f"│ {r['check']:<20} │ {r['standard']:<8} │ {r['result']:<8} │ {status:<6} │")
    print("├──────────────────────┼──────────┼──────────┼────────┤")

    pass_count = sum(1 for r in results if r["pass"])
    print(f"│ 通过: {pass_count}/{len(results)}                                                    │")
    print("└──────────────────────┴──────────┴──────────┴────────┘")

    if pass_count < len(results):
        failed = [r["check"] for r in results if not r["pass"]]
        print(f"\n⚠️ 未通过的检查项: {', '.join(failed)}")
        print("建议: 回到Phase 2修复上述维度后重新验证。")
    else:
        print("\n⭐ 全部通过！Skill可以交付。")

    return pass_count == len(results)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 quality_check.py <SKILL.md路径>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"错误: 文件不存在 - {filepath}")
        sys.exit(1)

    success = check_quality(filepath)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    import os
    main()