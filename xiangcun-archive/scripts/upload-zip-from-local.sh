#!/usr/bin/env bash
set -euo pipefail

# 用法：
# 1. 先把 ChatGPT 下载的 xiangcun-github-upload-ready.zip 放到本机 Downloads 或当前目录
# 2. 在仓库根目录运行：bash xiangcun-archive/scripts/upload-zip-from-local.sh /path/to/xiangcun-github-upload-ready.zip

ZIP_PATH="${1:-}"
if [ -z "$ZIP_PATH" ]; then
  echo "请传入 zip 文件路径，例如：bash xiangcun-archive/scripts/upload-zip-from-local.sh ~/Downloads/xiangcun-github-upload-ready.zip"
  exit 1
fi

if [ ! -f "$ZIP_PATH" ]; then
  echo "找不到文件：$ZIP_PATH"
  exit 1
fi

mkdir -p xiangcun-archive
cp "$ZIP_PATH" xiangcun-archive/xiangcun-github-upload-ready.zip

sha256sum xiangcun-archive/xiangcun-github-upload-ready.zip || shasum -a 256 xiangcun-archive/xiangcun-github-upload-ready.zip

git add xiangcun-archive/xiangcun-github-upload-ready.zip
git commit -m "add xiangcun full archive zip" || echo "没有新变化可提交"
git push
