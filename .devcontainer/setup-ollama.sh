#!/usr/bin/env bash
set -euo pipefail
echo "==> Installing Ollama..."
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
echo "==> Starting Ollama server..."
if ! pgrep -x ollama >/dev/null; then
  nohup ollama serve >/tmp/ollama.log 2>&1 &
  sleep 3
fi
echo "==> Pulling model qwen2.5:1.5b (first time only, ~1 GB)..."
ollama pull qwen2.5:1.5b
echo "==> Installing Python dependencies..."
pip install -r requirements.txt
echo "==> Setup done. Ollama API: http://localhost:11434"
