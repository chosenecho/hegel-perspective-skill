#!/bin/bash
# YouTube字幕下载脚本
# 用法: bash download_subtitles.sh <YouTube_URL> [输出目录]
# 自动优先人工字幕 → 中文 → 英文 → 自动生成字幕

set -e

URL="$1"
OUTPUT_DIR="${2:-.}"

mkdir -p "$OUTPUT_DIR"

echo "正在下载字幕: $URL"

# 优先: 人工字幕(en) → 中文(zh-Hans) → 英文自动生成(en-orig) → 自动生成字幕
yt-dlp --write-subs --sub-langs "en,zh-Hans,en-orig" --skip-download --output "$OUTPUT_DIR/%(title)s.%(ext)s" "$URL" 2>/dev/null || \
yt-dlp --write-auto-subs --sub-langs "en,zh-Hans" --skip-download --output "$OUTPUT_DIR/%(title)s.%(ext)s" "$URL"

echo "字幕下载完成，保存至: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"/*.vtt "$OUTPUT_DIR"/*.srt 2>/dev/null || echo "未找到字幕文件"