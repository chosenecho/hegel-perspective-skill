#!/usr/bin/env python3
"""
SRT/VTT字幕清洗为纯文本Transcript
用法: python3 srt_to_transcript.py <input.srt> [output.txt]
去时间戳、序号、HTML标签、连续重复行
"""

import re
import sys
import os

def clean_srt(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # 去HTML标签
    content = re.sub(r'<[^>]+>', '', content)
    # 去时间戳行
    content = re.sub(r'\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}', '', content)
    # 去序号行
    content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)
    # 去VTT头部
    content = re.sub(r'^WEBVTT.*\n', '', content)
    # 去多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    # 去连续重复行
    lines = content.split('\n')
    cleaned = []
    prev = None
    for line in lines:
        stripped = line.strip()
        if stripped and stripped != prev:
            cleaned.append(stripped)
            prev = stripped
        elif not stripped:
            cleaned.append('')
            prev = None

    return '\n'.join(cleaned)

def main():
    if len(sys.argv) < 2:
        print("用法: python3 srt_to_transcript.py <input.srt> [output.txt]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(input_path)[0] + '_transcript.txt'

    cleaned = clean_srt(input_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned)

    print(f"清洗完成: {input_path} → {output_path}")
    print(f"输出行数: {len(cleaned.splitlines())}")

if __name__ == '__main__':
    main()