#!/usr/bin/env bash
set -e
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc 2>/dev/null || true

echo ">>> Ollama"
if ! command -v ollama >/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y zstd
  curl -fsSL https://ollama.com/install.sh | sh
fi
ollama --version

echo ">>> Hermes"
if ! command -v hermes >/dev/null; then
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-browser
  source ~/.bashrc
fi
hermes --version

echo ">>> Config Ollama endpoint"
hermes config set model.provider custom
hermes config set model.base_url "http://127.0.0.1:11434/v1"
hermes config set model.default "kimi-k2.6:cloud"

echo "Done. Run: ollama signin (if needed), then: ollama launch hermes"
